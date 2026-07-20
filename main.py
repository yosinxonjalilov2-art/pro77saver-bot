import os
import threading
import requests
import telebot
from yt_dlp import YoutubeDL
from http.server import HTTPServer, BaseHTTPRequestHandler

# Server o'chib qolmasligi uchun
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

CAPTION_TEXT = "🎬 Mana siz so'ragan video!\n\n🤖 Bot: @pro77saver_bot"

@bot.message_handler(commands=['start'])
def start_cmd(message):
    start_text = (
        "🤖 Pro 77 Saver - Media Downloader!\n\n"
        "Men quyidagi tarmoqlardan videolarni yuklab bera olaman:\n"
        "📸 Instagram\n"
        "🎵 TikTok\n\n"
        "🔗 Foydalanish: Shunchaki video ssilkasini menga yuboring!"
    )
    bot.reply_to(message, start_text)

# TikTok uchun 1-API (TikWM)
def get_tiktok_tikwm(url):
    try:
        r = requests.post("https://www.tikwm.com/api/", data={"url": url}, timeout=10).json()
        if r.get("code") == 0 and "data" in r:
            return r["data"]["play"]
    except Exception:
        pass
    return None

# TikTok uchun 2-API (SSSTik Zaxira)
def get_tiktok_ssstik(url):
    try:
        r = requests.post("https://ssstik.io/abc?url=dl", data={"id": url, "locale": "en", "tt": 0}, timeout=10)
        if "href" in r.text:
            import re
            links = re.findall(r'href="(https://ticket\.ssstik\.io/[^"]+)"', r.text)
            if links:
                return links[0]
    except Exception:
        pass
    return None

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()

    if not url.startswith("http"):
        bot.reply_to(message, "Iltimos, to'g'ri video ssilkasini yuboring!")
        return

    # TikToK va Instagram'dan boshqa ssilka bo'lsa ogohlantirish
    if "tiktok.com" not in url and "instagram.com" not in url:
        bot.reply_to(message, "Hozircha faqat Instagram va TikTok havolalarini yuborishingiz mumkin!")
        return

    status_msg = bot.reply_to(message, "⚡ Video izlanmoqda...")

    # --- TIKTOK YUKLASH ---
    if "tiktok.com" in url:
        # 1-urinish
        direct_link = get_tiktok_tikwm(url)
        # 2-urinish (agar 1-si ishlamasa)
        if not direct_link:
            direct_link = get_tiktok_ssstik(url)

        if direct_link:
            try:
                bot.edit_message_text("📥 Video yuklandi va sizga yuborilmoqda...", chat_id=message.chat.id, message_id=status_msg.message_id)
                bot.send_video(
                    message.chat.id, 
                    direct_link, 
                    caption=CAPTION_TEXT, 
                    reply_to_message_id=message.message_id
                )
                bot.delete_message(message.chat.id, status_msg.message_id)
                return
            except Exception:
                pass

    # --- INSTAGRAM YUKLASH (va TikTok zaxira) ---
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True
    }

    try:
        bot.edit_message_text("📥 Video yuklanmoqda...", chat_id=message.chat.id, message_id=status_msg.message_id)

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        bot.edit_message_text("📤 Video sizga yuborilmoqda...", chat_id=message.chat.id, message_id=status_msg.message_id)

        # Fayl hajmini tekshirish (Telegram 50MB cheklovi)
        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        if file_size_mb > 49:
            bot.edit_message_text("❌ Video hajmi juda katta (50MB dan yuqori). Telegram yuborishga ruxsat bermaydi.", chat_id=message.chat.id, message_id=status_msg.message_id)
            if os.path.exists(filename):
                os.remove(filename)
            return

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

    except Exception:
        bot.edit_message_text(
            "❌ Videoni yuklab bo'lmadi. Video yopiq (private) profilda bo'lishi yoki havola noto'g'ri bo'lishi mumkin.",
            chat_id=message.chat.id,
            message_id=status_msg.message_id
        )

if __name__ == "__main__":
    bot.infinity_polling()
