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
    welcome_msg = (
        "🤖 *Welcome to Support Bot!*\n\n"
        "Send me any message and I'll forward it to the owner.\n"
        "They will reply to you through this bot.\n\n"
        "📌 *Note:* You can reply to the bot's messages and they will be forwarded as well."
    )
    await update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)

async def forward_to_owner(update: Update, context: CallbackContext):
    """Forward any user message to the owner"""
    user = update.effective_user
    msg = update.message
    
    # Create a nice forward message format
    forward_text = (
        f"📨 *New message from user:*\n"
        f"👤 *User ID:* `{user.id}`\n"
        f"📛 *Name:* {user.first_name}"
    )
    
    if user.last_name:
        forward_text += f" {user.last_name}"
    if user.username:
        forward_text += f"\n🔖 *Username:* @{user.username}"
    
    forward_text += f"\n💬 *Message:* {msg.text}"
    
    # Store user ID in bot data for this conversation
    # Use user.id as key to track conversation
    context.bot_data[user.id] = user.id
    
    # Send formatted message to owner
    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=forward_text,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Also forward the original message as a copy
    await context.bot.copy_message(
        chat_id=OWNER_ID,
        from_chat_id=user.id,
        message_id=msg.message_id
    )
    
    # Notify user that message was sent
    await update.message.reply_text(
        "✅ *Message sent to support!*\n"
        "You'll get a reply here when the owner responds.",
        parse_mode=ParseMode.MARKDOWN
    )

async def reply_to_user(update: Update, context: CallbackContext):
    """Handle owner's replies to users"""
    # Only allow owner to reply
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the bot owner can use this.")
        return
    
    msg = update.message
    
    # Check if replying to a forwarded message
    if msg.reply_to_message:
        reply_text = msg.reply_to_message.text or msg.reply_to_message.caption
        
        # Try to extract user ID from the forwarded message text
        user_id = None
        
        if reply_text:
            lines = reply_text.split('\n')
            for line in lines:
                if '🆔 *User ID:*' in line or '👤 *User ID:*' in line:
                    # Extract ID from markdown format
                    parts = line.split('`')
                    if len(parts) >= 2:
                        try:
                            user_id = int(parts[1])
                            break
                        except ValueError:
                            pass
    
    # If no user ID found in reply, ask owner
    if not user_id:
        await update.message.reply_text(
            "⚠️ *Could not identify user to reply to.*\n\n"
            "Please reply to a forwarded message that contains the user's ID, or use:\n"
            "`/reply USER_ID Your message here`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Send reply to user
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📨 *Reply from support:*\n\n{msg.text}",
            parse_mode=ParseMode.MARKDOWN
        )
        await update.message.reply_text(
            f"✅ *Reply sent to user ID:* `{user_id}`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Failed to send reply:* `{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )

async def reply_command(update: Update, context: CallbackContext):
    """Handle /reply command for owner"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the bot owner can use this.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ *Usage:* `/reply USER_ID Your message here`\n\n"
            "Example: `/reply 123456789 Hello, how can I help?`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        user_id = int(context.args[0])
        reply_text = ' '.join(context.args[1:])
        
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📨 *Reply from support:*\n\n{reply_text}",
            parse_mode=ParseMode.MARKDOWN
        )
        await update.message.reply_text(
            f"✅ *Reply sent to user ID:* `{user_id}`",
            parse_mode=ParseMode.MARKDOWN
        )
    except ValueError:
        await update.message.reply_text(
            "❌ *Invalid user ID.* Please provide a numeric ID.",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Failed to send reply:* `{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )

async def unknown(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "❌ *Unknown command.*\n\n"
        "Available commands:\n"
        "• /start - Start the bot\n"
        "• /reply USER_ID MESSAGE - Reply to a user (owner only)",
        parse_mode=ParseMode.MARKDOWN
    )

# ==========================================

def main():
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"🌐 Flask server running on port {PORT}")
    
    # Start Telegram bot
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_owner))
    app.add_handler(MessageHandler(filters.REPLY, reply_to_user))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    print("🤖 Livegram bot is running...")
    print(f"📨 Forwarding all messages to owner: {OWNER_ID}")
    print("\n💡 How it works:")
    print("1. Any user message (including replies) gets forwarded to owner")
    print("2. Owner can reply by replying to any forwarded message")
    print("3. Or use /reply USER_ID MESSAGE command")
    
    app.run_polling()

if __name__ == "__main__":
    main()
