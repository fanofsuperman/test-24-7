import os
import threading
from flask import Flask
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ========== CONFIGURATION ==========
BOT_TOKEN = "8705756650:AAFUd0sFYQgOdj99-2yWJdKC88kxTsVnD4g"
OWNER_ID = 6810494746
PORT = int(os.environ.get("PORT", 8080))
# ===================================

# Flask app for uptime monitoring
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is alive!", 200

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    flask_app.run(host='0.0.0.0', port=PORT)

# ========== TELEGRAM BOT CODE ==========
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "MESSAGE THIS BOT IF YOU NEED HELP WITH THE INJECTOR OR IF YOU WANT TO BUY A VIP INJECTOR. I'LL GET BACK TO YOU AS SOON AS POSSIBLE.",
        parse_mode=ParseMode.MARKDOWN
    )

async def forward_to_owner(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.message

    forwarded = await context.bot.forward_message(
        chat_id=OWNER_ID,
        from_chat_id=user.id,
        message_id=msg.message_id
    )

    context.bot_data[forwarded.message_id] = user.id

async def reply_to_user(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        return

    reply_to = update.message.reply_to_message
    if not reply_to:
        return

    user_id = context.bot_data.get(reply_to.message_id)
    if not user_id:
        return

    try:
        if update.message.text:
            await context.bot.send_message(
                chat_id=user_id,
                text=update.message.text
            )

        elif update.message.photo:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=update.message.photo[-1].file_id,
                caption=update.message.caption
            )

        elif update.message.video:
            await context.bot.send_video(
                chat_id=user_id,
                video=update.message.video.file_id,
                caption=update.message.caption
            )

        elif update.message.document:
            await context.bot.send_document(
                chat_id=user_id,
                document=update.message.document.file_id,
                caption=update.message.caption
            )

        elif update.message.voice:
            await context.bot.send_voice(
                chat_id=user_id,
                voice=update.message.voice.file_id,
                caption=update.message.caption
            )

        elif update.message.audio:
            await context.bot.send_audio(
                chat_id=user_id,
                audio=update.message.audio.file_id,
                caption=update.message.caption
            )

        elif update.message.sticker:
            await context.bot.send_sticker(
                chat_id=user_id,
                sticker=update.message.sticker.file_id
            )

        elif update.message.video_note:
            await context.bot.send_video_note(
                chat_id=user_id,
                video_note=update.message.video_note.file_id
            )

        elif update.message.animation:
            await context.bot.send_animation(
                chat_id=user_id,
                animation=update.message.animation.file_id,
                caption=update.message.caption
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")

async def unknown(update: Update, context: CallbackContext):
    await update.message.reply_text("❌ Unknown command. Use /start")
# ==========================================

def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"🌐 Flask server running on port {PORT}")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            ~filters.COMMAND & ~filters.REPLY,
            forward_to_owner
        )
    )

    app.add_handler(
        MessageHandler(
            filters.REPLY,
            reply_to_user
        )
    )

    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("🤖 Livegram bot is running...")
    print(f"📨 Forwarding messages to owner: {OWNER_ID}")

    app.run_polling()

if __name__ == "__main__":
    main()
