import os
import time
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. Render serverini uyg'oq tutish uchun HTTP Server
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK - Downloader Bot is running")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --------------------------------------------------
# BUYERGA OZINGIZNING TOKENINGIZNI YOZING!
BOT_TOKEN = "8766383241:AAFhA6zLr-GswgjKVFNOUvPdUFe978WxYMM"  
bot = telebot.TeleBot(BOT_TOKEN)

user_links = {}

# START BUYRUG'I
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(
        message, 
        "👋 <b>Salom! Men Video va Audio yuklovchi botman.</b>\n\n"
        "Menga <b>Instagram</b> yoki <b>TikTok</b> havolasini yuboring!",
        parse_mode="HTML"
    )

# HAVOLALARNI QABUL QILISH
@bot.message_handler(func=lambda message: message.text and ("http://" in message.text or "https://" in message.text))
def handle_link(message):
    url = message.text.strip()
    user_links[message.chat.id] = url

    markup = InlineKeyboardMarkup()
    btn_video = InlineKeyboardButton("🎬 Video (MP4)", callback_data="dl_video")
    btn_audio = InlineKeyboardButton("🎵 Audio (MP3)", callback_data="dl_audio")
    markup.add(btn_video, btn_audio)

    bot.reply_to(message, "📥 <b>Formatni tanlang:</b>", reply_markup=markup, parse_mode="HTML")

# YUKLASH TUGMALARI
@bot.callback_query_handler(func=lambda call: call.data in ["dl_video", "dl_audio"])
def process_download(call):
    chat_id = call.message.chat.id
    url = user_links.get(chat_id)
    status_msg_id = call.message.message_id

    if not url:
        bot.answer_callback_query(call.id, "❌ Havola topilmadi, qaytadan yuboring.")
        return

    bot_username = bot.get_me().username

    # 1. VIDEO YUKLASH
    if call.data == "dl_video":
        bot.edit_message_text("🔍 <b>Video izlanmoqda va yuklanmoqda...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'downloads/{chat_id}_video.%(ext)s',
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            # Yuklanib bo'lgandan keyingi bosqichiy matn:
            bot.edit_message_text("📤 <b>Video yuklandi, sizga yuborilmoqda...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")
            time.sleep(1) # Matn o'qilishi uchun 1 soniya kutiladi

            caption_text = f"✅ <b>Mana siz so'ragan video!</b>\n\n🤖 <b>Bot:</b> @{bot_username}"

            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video, caption=caption_text, parse_mode="HTML")

            bot.delete_message(chat_id, status_msg_id)
            if os.path.exists(filename): os.remove(filename)

        except Exception:
            bot.send_message(chat_id, "❌ Videoni yuklashda xatolik bo'ldi. Havolani tekshiring.")

    # 2. AUDIO YUKLASH
    elif call.data == "dl_audio":
        bot.edit_message_text("🔍 <b>Audio izlanmoqda va ajratilmoqda...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/{chat_id}_audio.%(ext)s',
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            # Yuklanib bo'lgandan keyingi bosqichiy matn:
            bot.edit_message_text("📤 <b>Audio yuklandi, sizga yuborilmoqda...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")
            time.sleep(1)

            caption_text = f"✅ <b>Mana siz so'ragan audio!</b>\n\n🤖 <b>Bot:</b> @{bot_username}"

            with open(filename, 'rb') as audio:
                bot.send_audio(chat_id, audio, caption=caption_text, parse_mode="HTML")

            bot.delete_message(chat_id, status_msg_id)
            if os.path.exists(filename): os.remove(filename)

        except Exception:
            bot.send_message(chat_id, "❌ Audioni ajratishda xatolik bo'ldi.")

if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    bot.infinity_polling(skip_pending=True)
