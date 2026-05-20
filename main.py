import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from moviepy.video.io.VideoFileClip import VideoFileClip

# Set up clean logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# CREDENTIALS
BOT_TOKEN = "8883987083:AAEC1HbhmaDX3tDJd-qMzU7hHpKlcbil8J4"
RENDER_URL = "https://telegram-file-converter-0xwy.onrender.com" 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙️ Welcome to the File Converter Bot!\n\n"
        "Send me any video file (.mp4) or video note, and I will instantly "
        "strip the video away and send you the clean MP3 audio track!"
    )

async def convert_video_to_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video_object = update.message.video or update.message.document
    if not video_object and update.message.document:
        if not update.message.document.mime_type.startswith("video/"):
            return

    status_message = await update.message.reply_text("📥 Downloading your video file...")
    os.makedirs('converter_downloads', exist_ok=True)
    
    file_id = video_object.file_id
    new_file = await context.bot.get_file(file_id)
    
    input_path = f"converter_downloads/{file_id}_input.mp4"
    output_path = f"converter_downloads/{file_id}_audio.mp3"
    
    try:
        await new_file.download_to_drive(input_path)
        await status_message.edit_text("⚡ Extracting audio and converting to MP3...")
        
        loop = asyncio.get_running_loop()
        def process_audio():
            video = VideoFileClip(input_path, audio=True)
            video.audio.write_audiofile(output_path, logger=None)
            video.close()
            
        await loop.run_in_executor(None, process_audio)
        
        await status_message.edit_text("📤 Uploading your MP3 track...")
        with open(output_path, 'rb') as audio_file:
            await update.message.reply_audio(
                audio=audio_file,
                title="Extracted Audio",
                performer="Converter Bot"
            )
        await status_message.delete()
        
    except Exception as e:
        await status_message.edit_text("❌ Conversion failed. Please ensure the file is an accessible video format.")
        logger.error(f"Error during file conversion: {e}")
        
    finally:
        for path in (input_path, output_path):
            if os.path.exists(path):
                try: os.remove(path)
                except Exception: pass

# Official post-initialization cleanup hook
async def clear_old_webhooks(application: Application) -> None:
    logger.info("Automatically clearing any conflicting webhook pathways...")
    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook cleaned cleanly!")

def main():
    # Pass the cleanup function into the application builder natively
    application = Application.builder().token(BOT_TOKEN).post_init(clear_old_webhooks).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, convert_video_to_mp3))
    
    port = int(os.environ.get("PORT", 8080))
    logger.info("Starting converter webhook gateway...")
    
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,
        webhook_url=f"{RENDER_URL}/{BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()
