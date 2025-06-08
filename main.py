# =================================================================
#            الكود الكامل والنهائي لملف main.py
# =================================================================

# --- استيراد المكتبات ---
import logging
from logging.handlers import RotatingFileHandler # لاستيراد أداة التحكم في السجلات
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# مكتبات تيليجرام
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telethon import TelegramClient, events

# استيراد وظيفة إبقاء البوت نشطًا من الملف الآخر
from keep_alive import keep_alive


# --- تحميل متغيرات البيئة ---
# على Replit، سيتم تحميلها من أداة "Secrets" تلقائيًا
load_dotenv()

# --- الإعدادات ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
DESTINATION_CHANNEL_ID_STR = os.getenv("DESTINATION_CHANNEL_ID")
SOURCE_CHANNEL_ID_STR = os.getenv("SOURCE_CHANNEL_ID")

# --- التحقق من الإعدادات ---
if not all([TOKEN, API_ID, API_HASH, DESTINATION_CHANNEL_ID_STR, SOURCE_CHANNEL_ID_STR]):
    raise ValueError("يرجى التأكد من تعيين كل المتغيرات في أداة Secrets")

try:
    DESTINATION_CHANNEL_ID = int(DESTINATION_CHANNEL_ID_STR)
    if SOURCE_CHANNEL_ID_STR.lstrip('-').isdigit():
        SOURCE_CHANNEL_ID = int(SOURCE_CHANNEL_ID_STR)
    else:
        SOURCE_CHANNEL_ID = SOURCE_CHANNEL_ID_STR
except ValueError:
    raise ValueError("معرف القناة الهدف يجب أن يكون رقمًا صحيحًا.")


# --- إعدادات التسجيل (Logging) مع التحكم في الحجم (الحل الثاني) ---
# اسم ملف السجل الذي سيظهر في قائمة الملفات على Replit
log_filename = "bot.log"
# الحجم الأقصى للملف الواحد بالميجابايت
max_log_size_mb = 5
# عدد النسخ الاحتياطية التي سيتم الاحتفاظ بها (حسب طلبك)
backup_count = 2

# تهيئة المُعالج (Handler) الذي يقوم بتدوير الملفات
log_handler = RotatingFileHandler(
    log_filename,
    maxBytes=max_log_size_mb * 1024 * 1024, # تحويل الميجابايت إلى بايت
    backupCount=backup_count
)

# تحديد تنسيق الرسائل في السجل
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

# الحصول على المسجل الرئيسي وإضافة المعالج إليه
logger = logging.getLogger()
logger.setLevel(logging.INFO) # نحتفظ بمستوى INFO لأن الحجم الآن تحت السيطرة

# التأكد من عدم وجود معالجات أخرى قد تتعارض
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(log_handler)

# تجاهل رسائل DEBUG من مكتبات أخرى لتقليل الضوضاء
logging.getLogger("httpx").setLevel(logging.WARNING)


# --- متغيرات عامة ---
start_time = datetime.now()


# --- معالجات الأوامر (Handlers) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    uptime = datetime.now() - start_time
    uptime_str = str(uptime).split('.')[0]
    await update.message.reply_html(
        f"مرحبًا {user.first_name}!\n"
        "🤖 <b>بوت نسخ المنشورات</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>المصدر:</b> <code>{SOURCE_CHANNEL_ID}</code>\n"
        f"📤 <b>الهدف:</b> <code>{DESTINATION_CHANNEL_ID}</code>\n"
        f"⏰ <b>وقت التشغيل:</b> {uptime_str}\n"
        "✅ <b>الحالة:</b> يعمل على Replit."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uptime = datetime.now() - start_time
    uptime_str = str(uptime).split('.')[0]
    await update.message.reply_html(
        "📊 <b>حالة البوت</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>الحالة:</b> متصل ويعمل\n"
        f"⏰ <b>مدة التشغيل:</b> {uptime_str}"
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # استخدام المسجل الذي قمنا بإعداده لتسجيل الخطأ في ملف bot.log
    logger.error(f"حدث خطأ: {context.error}", exc_info=True)


# --- الجزء الرئيسي (main) ---
async def main() -> None:
    """
    الإعداد الرئيسي: يشغل خادم الويب، ثم يشغل البوت وعميل Telethon.
    """
    # 1. تشغيل خادم الويب في الخلفية لإبقاء البوت نشطًا
    keep_alive()

    # 2. بدء إعدادات البوت
    global start_time
    start_time = datetime.now()

    telethon_client = TelegramClient('bot_session', int(API_ID), API_HASH)
    ptb_app = Application.builder().token(TOKEN).build()

    ptb_app.add_handler(CommandHandler("start", start))
    ptb_app.add_handler(CommandHandler("status", status))
    ptb_app.add_error_handler(error_handler)

    @telethon_client.on(events.NewMessage(chats=SOURCE_CHANNEL_ID))
    async def handle_new_message(event):
        message = event.message
        logger.info(f"Telethon: تم التقاط منشور جديد ID: {message.id}")
        try:
            await ptb_app.bot.copy_message(
                chat_id=DESTINATION_CHANNEL_ID,
                from_chat_id=message.chat_id,
                message_id=message.id
            )
            logger.info(f"تم نسخ المنشور بنجاح إلى {DESTINATION_CHANNEL_ID}")
        except Exception as e:
            logger.error(f"فشل نسخ المنشور {message.id}: {e}")

    # 3. تشغيل كل شيء معًا
    async with ptb_app:
        await ptb_app.start()
        await ptb_app.updater.start_polling()
        logger.info("بوت الأوامر (python-telegram-bot) بدأ التشغيل...")

        await telethon_client.start(bot_token=TOKEN)
        logger.info("عميل الاستماع (Telethon) بدأ التشغيل...")
        
        await telethon_client.run_until_disconnected()

        await ptb_app.updater.stop()
        await ptb_app.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("تم إيقاف البوت.")
