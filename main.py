import os
import threading
from flask import Flask
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ========== CONFIGURATION ==========
BOT_TOKEN = "8705756650:AAFUd0sFYQgOdj99-2yWJdKC88kxTsVnD4g"  # Replace with your real token
OWNER_ID = 6810494746  # Your Telegram ID
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
    
    # Skip if the message is from owner
    if user.id == OWNER_ID:
        return
    
    msg = update.message
    
    # Forward the message to owner
    forwarded = await context.bot.forward_message(
        chat_id=OWNER_ID,
        from_chat_id=user.id,
        message_id=msg.message_id
    )
    
    # Store mapping of forwarded message ID to user ID
    context.bot_data[forwarded.message_id] = user.id
    print(f"📨 Forwarded message {forwarded.message_id} from user {user.id}")

async def reply_to_user(update: Update, context: CallbackContext):
    # Only owner can reply
    if update.effective_user.id != OWNER_ID:
        return
    
    reply_to = update.message.reply_to_message
    if not reply_to:
        await update.message.reply_text("⚠️ Reply to a forwarded message.")
        return
    
    # Try to get user_id from the forwarded message
    user_id = context.bot_data.get(reply_to.message_id)
    
    if not user_id:
        await update.message.reply_text("❌ Could not find original user. Make sure you're replying to a forwarded message.")
        return
    
    try:
        # Send the reply to the original user
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📨 Reply from owner:\n\n{update.message.text}"
        )
        await update.message.reply_text(f"✅ Reply sent to user {user_id}.")
        print(f"✅ Reply sent to user {user_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send: {e}")
        print(f"❌ Error sending reply: {e}")

async def unknown(update: Update, context: CallbackContext):
    await update.message.reply_text("❌ Unknown command. Use /start")
# ==========================================

def main():
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"🌐 Flask server running on port {PORT}")
    
    # Start Telegram bot
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    # Forward ALL non-command messages from non-owner users
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_owner))
    # Handle owner's replies to forwarded messages
    app.add_handler(MessageHandler(filters.REPLY, reply_to_user))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    print("🤖 Livegram bot is running...")
    print(f"📨 Forwarding messages to owner: {OWNER_ID}")
    
    app.run_polling()

if __name__ == "__main__":
    main()
