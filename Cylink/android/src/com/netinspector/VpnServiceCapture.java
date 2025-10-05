package com.netinspector;

import android.app.Service;
import android.content.Intent;
import android.net.VpnService;
import android.os.ParcelFileDescriptor;
import android.util.Log;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.Socket;

import org.json.JSONObject;

public class VpnServiceCapture extends VpnService {
    private static final String TAG = "VpnServiceCapture";
    private Thread vpnThread;
    private ParcelFileDescriptor vpnInterface;

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        startVpn();
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        stopVpn();
        super.onDestroy();
    }

    private void startVpn() {
        if (vpnThread != null && vpnThread.isAlive()) return;

        Builder builder = new Builder();
        builder.addAddress("10.0.0.2", 24);
        builder.addRoute("0.0.0.0", 0);
        builder.setSession("NetInspectorVPN");
        try {
            vpnInterface = builder.establish();
        } catch (Exception e) {
            Log.e(TAG, "Error establishing VPN", e);
            return;
        }

        vpnThread = new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    FileInputStream in = new FileInputStream(vpnInterface.getFileDescriptor());
                    byte[] packet = new byte[32767];
                    int length;
                    while ((length = in.read(packet)) > 0) {
                        // هنا لا نفك الشفرات — فقط نحصل على رأس الحزمة (IP/TCP/UDP)
                        // بسط: نرسل ملخّص إلى البايثون عبر socket محلي
                        try {
                            JSONObject j = new JSONObject();
                            j.put("pkt_len", length);
                            // يمكنك استخراج عناوين IP وPort من البايتات لو أردت (تحليل IP header)
                            // إرسال الملخص إلى الخادم المحلي
                            sendToLocal(jsonToBytes(j.toString()));
                        } catch (Exception e) {
                            // تجاهل أو تسجيل
                        }
                    }
                } catch (IOException e) {
                    Log.e(TAG, "VPN read error", e);
                }
            }
        });
        vpnThread.start();
    }

    private void stopVpn() {
        try {
            if (vpnInterface != null) vpnInterface.close();
        } catch (IOException e) { }
        if (vpnThread != null) vpnThread.interrupt();
    }

    private void sendToLocal(byte[] data) {
        Socket socket = null;
        try {
            socket = new Socket();
            socket.connect(new InetSocketAddress("127.0.0.1", 54321), 300);
            OutputStream out = socket.getOutputStream();
            out.write(intToBytes(data.length));
            out.write(data);
            out.flush();
            socket.close();
        } catch (IOException e) {
            Log.e(TAG, "sendToLocal failed: " + e.getMessage());
            if (socket != null) {
                try { socket.close(); } catch (IOException ignored) {}
            }
        }
    }

    private byte[] intToBytes(int val) {
        return new byte[] {
            (byte)(val >> 24),
            (byte)(val >> 16),
            (byte)(val >> 8),
            (byte)(val)
        };
    }
    
    private byte[] jsonToBytes(String s) {
        try { return s.getBytes("UTF-8"); } catch (Exception e) { return s.getBytes(); }
    }
}
