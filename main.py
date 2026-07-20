import os
import telebot
from yt_dlp import YoutubeDL

BOT_TOKEN = "8766383241:AAF56ne5E598UOex04TWxKy3k8ktS81cPFw"

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

    status_message = bot.reply_to(message, "⚡️ Video izlanmoqda va yuklab olinmoqda, kuting...")

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        bot.edit_message_text("🚀 Video Telegram'ga yuklanmoqda...", chat_id=message.chat.id, message_id=status_message.message_id)
        
        with open(filename, 'rb') as video:
            bot.send_video(message.chat.id, video, caption="Mana siz so'ragan video! @pro77saver_bot")
        
        os.remove(filename)
        bot.delete_message(message.chat.id, status_message.message_id)

    except Exception as e:
        bot.edit_message_text(
            "❌ **Xatolik yuz berdi!**\n\nSsilka noto'g'ri bo'lishi mumkin yoki ushbu video yuklanmadi.",
            chat_id=message.chat.id, 
            message_id=status_message.message_id
        )

if __name__ == "__main__":
    bot.infinity_polling()
