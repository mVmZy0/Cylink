[app]
title = NetInspector
package.name = netinspector
package.domain = org.netinspector
source.dir = app
orientation = portrait

# تأكد أن ملفات .kv ضمن source.dir تؤخذ تلقائيًا
# (عادة Kivy يضبط ذلك)
requirements = python3,kivy,pyjnius,kivy_garden.graph

android.permissions = INTERNET, BIND_VPN_SERVICE, WAKE_LOCK
android.add_src = ../android/src

# إعدادات SDK / NDK (قد تحتاج تعديل حسب البيئة)
android.api = 33
android.minapi = 24
android.ndk = 25b

# أيقنة التطبيق (اختياري)
# icon.filename = icon.png
