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

CAPTION_TEXT = "🎬 <b>Mana siz so'ragan video!</b>\n\n🤖 Bot: @pro77saver_bot"

@bot.message_handler(commands=['start'])
def start_cmd(message):
    start_text = (
        "🤖 <b>Pro 77 Saver - Universal Media Downloader!</b>\n\n"
        "Men quyidagi tarmoqlardan videolarni yuklab bera olaman:\n"
        "📸 <b>Instagram</b>\n"
        "🎵 <b>TikTok</b>\n"
        "🔴 <b>YouTube</b>\n\n"
        "🔗 <b>Foydalanish:</b> Shunchaki video ssilkasini menga yuboring!"
    )
    bot.reply_to(message, start_text, parse_mode="HTML")

# TikTok uchun API
def get_tiktok_url(url):
    try:
        r = requests.post("https://www.tikwm.com/api/", data={"url": url}, timeout=7).json()
        if r.get("code") == 0 and "data" in r:
            return r["data"]["play"]
    except Exception:
        pass
    return None

# YouTube uchun zaxirali API infratuzilmasi
def get_youtube_url(url):
    # 1-usul: Cobalt API ochiq serverlari
    cobalt_servers = [
        "https://api.cobalt.tools/api/json",
        "https://cobalt-api.kwiatek.xyz/api/json"
    ]
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = {"url": url, "vQuality": "720"}
    
    for server in cobalt_servers:
        try:
            r = requests.post(server, json=payload, headers=headers, timeout=6)
            if r.status_code == 200:
                data = r.json()
                if data.get("status") in ["stream", "redirect"]:
                    return data.get("url")
        except Exception:
            continue

    # 2-usul: Y2Mate alternatividan to'g'ri silka olish
    try:
        r = requests.post("https://v3.y2mate.is/api/ajax/search", data={"url": url}, timeout=7).json()
        if "formats" in r and "video" in r["formats"]:
            for v in r["formats"]["video"]:
                if v.get("url"):
                    return v["url"]
    except Exception:
        pass

    return None

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()

    if not url.startswith("http"):
        bot.reply_to(message, "Iltimos, to'g'ri video ssilkasini yuboring!")
        return

    status_msg = bot.reply_to(message, "⚡ Video izlanmoqda...")

    direct_link = None

    if "tiktok.com" in url:
        direct_link = get_tiktok_url(url)
    elif "youtube.com" in url or "youtu.be" in url:
        direct_link = get_youtube_url(url)

    if direct_link:
        try:
            bot.edit_message_text(
                "📥 Video yuklandi va sizga yuborilmoqda...",
                chat_id=message.chat.id,
                message_id=status_msg.message_id
            )
            bot.send_video(
                message.chat.id, 
                direct_link, 
                caption=CAPTION_TEXT, 
                parse_mode="HTML", 
                reply_to_message_id=message.message_id
            )
            bot.delete_message(message.chat.id, status_msg.message_id)
            return
        except Exception:
            pass

    # Instagram va qo'shimcha zaxira mexanizmi (yt-dlp + player_client bypass)
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android']
            }
        }
    }

    try:
        bot.edit_message_text(
            "📥 Video yuklanmoqda...",
            chat_id=message.chat.id,
            message_id=status_msg.message_id
        )

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        bot.edit_message_text(
            "📤 Video sizga yuborilmoqda...",
            chat_id=message.chat.id,
            message_id=status_msg.message_id
        )

        with open(filename, 'rb') as video:
            bot.send_video(
                message.chat.id, 
                video, 
                caption=CAPTION_TEXT, 
                parse_mode="HTML", 
                reply_to_message_id=message.message_id
            )

        if os.path.exists(filename):
            os.remove(filename)

        bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        bot.edit_message_text(
            "❌ Videoni yuklab bo'lmadi. Havolani qayta tekshirib yuboring.",
            chat_id=message.chat.id,
            message_id=status_msg.message_id
        )

if __name__ == "__main__":
    bot.infinity_polling()
