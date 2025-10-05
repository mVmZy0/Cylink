# monitor.py
import socket
import threading
import struct
import json
import time
from db import DBManager

class LocalCaptureServer:
    def __init__(self, host='127.0.0.1', port=54321):
        self.host = host
        self.port = port
        self.running = False
        self.db = DBManager('netinspector.db')
        self.callbacks = []  # واجهة للإخطار (UI)

    def start(self):
        self.running = True
        t = threading.Thread(target=self._run_server, daemon=True)
        t.start()

    def stop(self):
        self.running = False

    def _run_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen(5)
        s.settimeout(1.0)
        while self.running:
            try:
                conn, addr = s.accept()
                threading.Thread(target=self._handle_conn, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
        s.close()

    def _handle_conn(self, conn):
        try:
            # أول 4 بايت طول الرسالة
            raw_len = self._recv_all(conn, 4)
            if not raw_len:
                conn.close()
                return
            length = struct.unpack('!I', raw_len)[0]
            data = self._recv_all(conn, length)
            if not data:
                conn.close()
                return
            #解析 JSON
            try:
                j = json.loads(data.decode('utf-8'))
            except Exception:
                j = {"raw_len": length}
            # حفظ في DB
            ts = int(time.time())
            rec_id = self.db.insert_record(ts, j)
            # إخطار الواجهة
            for cb in self.callbacks:
                try:
                    cb({'id': rec_id, 'ts': ts, 'payload': j})
                except Exception:
                    pass
        finally:
            conn.close()

    def _recv_all(self, conn, n):
        data = b''
        while len(data) < n:
            packet = conn.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def register_callback(self, fn):
        if fn not in self.callbacks:
            self.callbacks.append(fn)

    def unregister_callback(self, fn):
        if fn in self.callbacks:
            self.callbacks.remove(fn)
