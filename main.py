import os
import threading
import requests
import telebot
from yt_dlp import YoutubeDL
from http.server import HTTPServer, BaseHTTPRequestHandler

# Dummy server (Render o'chmasligi uchun)
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

# Oddiy va xatosiz text format (Telegram HTML xatolarini oldini oladi)
CAPTION_TEXT = "🎬 Mana siz so'ragan video!\n\n🤖 Bot: @Pro_77_Saver_bot"

@bot.message_handler(commands=['start'])
def start_cmd(message):
    start_text = (
        "🤖 Pro 77 Saver - Universal Media Downloader!\n\n"
        "Men quyidagi tarmoqlardan videolarni yuklab bera olaman:\n"
        "📸 Instagram\n"
        "🎵 TikTok\n"
        "🔴 YouTube\n\n"
        "🔗 Foydalanish: Shunchaki video ssilkasini menga yuboring!"
    )
    bot.reply_to(message, start_text)

# TikTok uchun bepul ochiq yuklovchi
def get_tiktok_url(url):
    try:
        r = requests.post("https://www.tikwm.com/api/", data={"url": url}, timeout=8).json()
        if r.get("code") == 0 and "data" in r:
            return r["data"]["play"]
    except Exception:
        pass
    return None

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()

    if not url.startswith("http"):
        bot.reply_to(message, "Iltimos, to'g'ri video ssilkasini yuboring!")
        return

    # 1-Bosqich: Izlanmoqda
    status_msg = bot.reply_to(message, "⚡ Video izlanmoqda...")

    # TikTok uchun tezkor usul
    if "tiktok.com" in url:
        tiktok_url = get_tiktok_url(url)
        if tiktok_url:
            try:
                bot.edit_message_text("📥 Video yuklandi va yuborilmoqda...", chat_id=message.chat.id, message_id=status_msg.message_id)
                bot.send_video(message.chat.id, tiktok_url, caption=CAPTION_TEXT, reply_to_message_id=message.message_id)
                bot.delete_message(message.chat.id, status_msg.message_id)
                return
            except Exception:
                pass

    # Instagram va YouTube uchun kuchaytirilgan yt-dlp sozlamasi
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # YouTube botlikka qarshi himoyasini aylanib o'tish parametri:
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web', 'ios'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # 2-Bosqich: Yuklanmoqda
        bot.edit_message_text("📥 Video yuklanmoqda...", chat_id=message.chat.id, message_id=status_msg.message_id)

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # 3-Bosqich: Yuborilmoqda
        bot.edit_message_text("📤 Video sizga yuborilmoqda...", chat_id=message.chat.id, message_id=status_msg.message_id)

        with open(filename, 'rb') as video:
            bot.send_video(
                message.chat.id, 
                video, 
                caption=CAPTION_TEXT, 
                reply_to_message_id=message.message_id
            )

        if os.path.exists(filename):
            os.remove(filename)

        bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        bot.edit_message_text(
            "❌ Videoni yuklab bo'lmadi. Havola noto'g'ri yoki video shaxsiy (private) hisobda.",
            chat_id=message.chat.id,
            message_id=status_msg.message_id
        )

if __name__ == "__main__":
    bot.infinity_polling()
