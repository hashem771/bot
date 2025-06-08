# اسم الملف: keep_alive.py

from flask import Flask
from threading import Thread

# تهيئة تطبيق فلاسك
app = Flask('')

# تعريف مسار (route) أساسي
@app.route('/')
def home():
    # هذه الرسالة ستظهر في نافذة Webview على Replit
    return "Bot server is alive!"

# دالة لتشغيل الخادم
def run():
  app.run(host='0.0.0.0', port=8080)

# دالة لبدء الخادم في خيط (thread) منفصل
# هذا يضمن أن خادم الويب لا يمنع البوت من العمل
def keep_alive():
    t = Thread(target=run)
    t.start()
