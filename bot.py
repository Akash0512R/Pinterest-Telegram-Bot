import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables from .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Safety check for token
if not TOKEN:
    raise ValueError(
        "❌ Telegram token not found! "
        "Make sure you have a .env file with TELEGRAM_TOKEN set correctly."
    )

print("✅ Bot token loaded successfully!")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a Pinterest link, and I will fetch the image for you! 🚀"
    )

# Fetch Pinterest image URLs
def get_pinterest_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        meta = soup.find("meta", property="og:image")
        if meta:
            hd_url = meta["content"]
            thumb_url = hd_url + "?w=240"
            return hd_url, thumb_url
    except Exception as e:
        print(f"Error fetching Pinterest image: {e}")
    return None, None

# Handle Pinterest link messages
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "pinterest.com" not in url:
        await update.message.reply_text("❌ Please send a valid Pinterest link!")
        return

    processing_msg = await update.message.reply_text("Processing your request... ⏳")

    hd_url, thumb_url = get_pinterest_image(url)
    if not hd_url:
        await processing_msg.edit_text("⚠️ Could not fetch image.")
        return

    try:
        # Send thumbnail first
        thumb_data = requests.get(thumb_url).content
        thumb_msg = await update.message.reply_photo(photo=thumb_data, caption="Preview…")

        # Send full HD image
        hd_data = requests.get(hd_url).content
        await update.message.reply_photo(photo=hd_data)

        # Delete processing + thumbnail messages
        await processing_msg.delete()
        await thumb_msg.delete()

    except Exception as e:
        await processing_msg.edit_text(f"⚠️ Error sending image: {e}")

# Main
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))

    print("🚀 Bot is running...")
    app.run_polling()
