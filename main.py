import os
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. Render serverini uxlab qolmasligi uchun HTTP Server
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK - Media Downloader Bot is running")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --------------------------------------------------
BOT_TOKEN = "8766383241:AAGO-riv8-LPm559x_RzVYN4Hc0dcgxx4Ww"  # BotFather tokeningiz
bot = telebot.TeleBot(BOT_TOKEN)

user_links = {}

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(
        message, 
        "👋 **Salom! Men Video va Audio yuklovchi botman.**\n\n"
        "Menga **Instagram** yoki **TikTok** havolasini yuboring!",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text and ("http://" in message.text or "https://" in message.text))
def handle_link(message):
    url = message.text.strip()
    user_links[message.chat.id] = url

    markup = InlineKeyboardMarkup()
    btn_video = InlineKeyboardButton("🎬 Video (MP4)", callback_data="dl_video")
    btn_audio = InlineKeyboardButton("🎵 Audio (MP3)", callback_data="dl_audio")
    markup.add(btn_video, btn_audio)

    bot.reply_to(message, "📥 **Formatni tanlang:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ["dl_video", "dl_audio"])
def process_download(call):
    chat_id = call.message.chat.id
    url = user_links.get(chat_id)
    status_msg_id = call.message.message_id

    if not url:
        bot.answer_callback_query(call.id, "❌ Havola topilmadi, qaytadan yuboring.")
        return

    bot_username = bot.get_me().username

    if call.data == "dl_video":
        bot.edit_message_text("⏳ **Video yuklanmoqda, kuting...**", chat_id=chat_id, message_id=status_msg_id, parse_mode="Markdown")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'downloads/{chat_id}_video.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            bot.edit_message_text("📤 **Video tayyor! Sizga yuborilmoqda...**", chat_id=chat_id, message_id=status_msg_id, parse_mode="Markdown")
            caption_text = f"✅ **Mana siz so'ragan video yuklab olindi!**\n\n🤖 **Bot:** @{bot_username}"

            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video, caption=caption_text, parse_mode="Markdown")

            bot.delete_message(chat_id, status_msg_id)
            if os.path.exists(filename):
                os.remove(filename)

        except Exception as e:
            bot.send_message(chat_id, f"❌ Videoni yuklashda xatolik bo'ldi.\n\n`{str(e)[:100]}`", parse_mode="Markdown")

    elif call.data == "dl_audio":
        bot.edit_message_text("⏳ **Audio yuklanmoqda, kuting...**", chat_id=chat_id, message_id=status_msg_id, parse_mode="Markdown")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/{chat_id}_audio.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            bot.edit_message_text("📤 **Audio tayyor! Sizga yuborilmoqda...**", chat_id=chat_id, message_id=status_msg_id, parse_mode="Markdown")
            caption_text = f"✅ **Mana siz so'ragan audio yuklab olindi!**\n\n🤖 **Bot:** @{bot_username}"

            with open(filename, 'rb') as audio:
                bot.send_audio(chat_id, audio, caption=caption_text, parse_mode="Markdown")

            bot.delete_message(chat_id, status_msg_id)
            if os.path.exists(filename):
                os.remove(filename)

        except Exception as e:
            bot.send_message(chat_id, f"❌ Audioni ajratishda xatolik bo'ldi.\n\n`{str(e)[:100]}`", parse_mode="Markdown")

if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    bot.infinity_polling(skip_pending=True)
