# main.py
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from monitor import LocalCaptureServer
from kivy.properties import StringProperty, NumericProperty
from jnius import autoclass

class MainWidget(BoxLayout):
    start_btn_text = StringProperty("Start Monitoring")
    total_packets = NumericProperty(0)
    last_packet_len = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server = LocalCaptureServer()
        self.server.register_callback(self._on_new_packet)
        Clock.schedule_once(lambda dt: self._load_initial(), 0.5)
        self.vpn_started = False

    def _load_initial(self):
        from db import DBManager
        db = DBManager()
        rows = db.fetch_latest(50)
        self.total_packets = len(rows)

    def toggle_monitor(self):
        if not self.vpn_started:
            started = self.start_vpn_service()
            if not started:
                return
            self.server.start()
            self.start_btn_text = "Stop Monitoring"
            self.vpn_started = True
        else:
            self.stop_vpn_service()
            self.server.stop()
            self.start_btn_text = "Start Monitoring"
            self.vpn_started = False

    def _on_new_packet(self, info):
        self.total_packets += 1
        payload = info.get('payload', {})
        if 'pkt_len' in payload:
            self.last_packet_len = payload['pkt_len']
        grid = self.ids.list_grid
        from kivy.uix.label import Label
        l = Label(text=f"{info['ts']}: {payload}", size_hint_y=None, height=30)
        grid.add_widget(l, index=0)

    def export_csv(self):
        from db import DBManager
        import json, csv, time
        db = DBManager()
        rows = db.fetch_latest(1000)
        fn = f"/sdcard/NetInspector_export_{int(time.time())}.csv"
        with open(fn, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'ts', 'data_json'])
            for r in rows:
                writer.writerow([r['id'], r['ts'], json.dumps(r['data'])])
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        Popup(title='Exported', content=Label(text="Saved: " + fn), size_hint=(0.8, 0.2)).open()

    def start_vpn_service(self):
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            Intent = autoclass('android.content.Intent')
            ComponentName = autoclass('android.content.ComponentName')
            service_name = 'com.netinspector.VpnServiceCapture'
            intent = Intent()
            intent.setComponent(ComponentName(activity.getPackageName(), service_name))
            activity.startService(intent)
            return True
        except Exception as e:
            from kivy.uix.popup import Popup
            from kivy.uix.label import Label
            Popup(title='Error', content=Label(text=str(e)), size_hint=(0.9, 0.3)).open()
            return False

    def stop_vpn_service(self):
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            Intent = autoclass('android.content.Intent')
            ComponentName = autoclass('android.content.ComponentName')
            service_name = 'com.netinspector.VpnServiceCapture'
            intent = Intent()
            intent.setComponent(ComponentName(activity.getPackageName(), service_name))
            activity.stopService(intent)
            return True
        except Exception:
            return False

class NetInspectorApp(App):
    def build(self):
        Builder.load_file("ui.kv")
        return MainWidget()

if __name__ == '__main__':
    NetInspectorApp().run()
