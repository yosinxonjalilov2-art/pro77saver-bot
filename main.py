import os
import threading
import requests
import telebot
from yt_dlp import YoutubeDL
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

BOT_TOKEN = "8766383241:AAGO-riv8-LPm559x_RzVYN4Hc0dcgxx4Ww"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    start_text = (
        "🤖 **Pro 77 Saver - Universal Media Downloader!**\n\n"
        "Men quyidagi tarmoqlardan videolarni yuklab bera olaman:\n"
        "📸 **Instagram**\n"
        "🎵 **TikTok**\n"
        "🔴 **YouTube**\n\n"
        "🔗 **Foydalanish:** Shunchaki video ssilkasini menga yuboring!"
    )
    bot.reply_to(message, start_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()

    if not url.startswith("http"):
        bot.reply_to(message, "Iltimos, to'g'ri video ssilkasini yuboring!")
        return

    status_message = bot.reply_to(message, "⚡ Video izlanmoqda va yuklab olinmoqda, kuting...")

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as video:
            bot.send_video(message.chat.id, video, reply_to_message_id=message.message_id)

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
