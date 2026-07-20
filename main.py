import os
import telebot
from yt_dlp import YoutubeDL

BOT_TOKEN = "8766383241:AAHosKX3AWD1JM95xv69vJGupv312Csou78"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    start_text = (
        "🤖 **Pro 77 Saver - Universal Media Downloader!**\n\n"
        "Men quyidagi tarmoqlardan videolarni yuklab bera olaman:\n"
        "📸 **Instagram** (Reels, Post)\n"
        "🎵 **TikTok** (Watermark'siz)\n"
        "🔴 **YouTube** (Shorts, Video)\n\n"
        "🔗 **Foydalanish:** Shunchaki video ssilkasini menga yuboring!"
    )
    bot.reply_to(message, start_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()

    if not url.startswith("http"):
        bot.reply_to(message, "Iltimos, to'g'ri video ssilkasini (linkini) yuboring!")
        return

    status_message = bot.reply_to(message, "⚡ Video izlanmoqda va yuklab olinmoqda, kuting...")

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        }
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as video:
            bot.send_video(message.chat.id, video, reply_to_message_id=message.message_id)

        # Faylni yuborgach, server joyini to'ldirmaslik uchun o'chiramiz
        if os.path.exists(filename):
            os.remove(filename)

        bot.delete_message(message.chat.id, status_message.message_id)

    except Exception as e:
        bot.edit_message_text(
            f"❌ Videoni yuklashda xatolik yuz berdi: {str(e)}",
            chat_id=message.chat.id,
            message_id=status_message.message_id
        )

if __name__ == "__main__":
    bot.infinity_polling()
