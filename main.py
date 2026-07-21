import os
import re
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
# BUYERGA OZINGIZNING BOTFATHER'DAN OLGAN TOKENINGIZNI YOZING!
BOT_TOKEN = "8766383241:AAE2qEIj-zjEvhKV6OoOg9WKAbQzevPrrlM"  
bot = telebot.TeleBot(BOT_TOKEN)

user_links = {}

def download_full_by_query(chat_id, search_query, status_msg_id, bot_username):
    try:
        bot.edit_message_text("🎧 <b>To'liq versiyasi yuklanmoqda...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")

        full_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/{chat_id}_full.%(ext)s',
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(full_opts) as ydl:
            search_res = ydl.extract_info(search_query, download=True)
            if 'entries' in search_res and len(search_res['entries']) > 0:
                entry = search_res['entries'][0]
                full_filename = ydl.prepare_filename(entry)
                song_name = entry.get('title', 'To\'liq musiqa')
            else:
                bot.edit_message_text("❌ Afsuski, ushbu nom bo'yicha qo'shiq topilmadi.", chat_id=chat_id, message_id=status_msg_id)
                return

        caption_text = f"✅ <b>To'liq qo'shiq yuklab olindi!</b>\n🎵 <b>Nomi:</b> {song_name}\n\n🤖 <b>Bot:</b> @{bot_username}"

        with open(full_filename, 'rb') as audio:
            bot.send_audio(chat_id, audio, caption=caption_text, parse_mode="HTML")

        bot.delete_message(chat_id, status_msg_id)
        if os.path.exists(full_filename): os.remove(full_filename)

    except Exception:
        bot.send_message(chat_id, "❌ Musiqani yuklab bo'lmadi.")

def custom_search(message):
    chat_id = message.chat.id
    query_text = message.text.strip()
    bot_username = bot.get_me().username
    
    status_msg = bot.send_message(chat_id, f"🔍 <b>\"{query_text}\" bo'yicha qidirilmoqda...</b>", parse_mode="HTML")
    search_query = f"ytsearch1:{query_text} full audio"
    download_full_by_query(chat_id, search_query, status_msg.message_id, bot_username)

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

# TUGMALARNI ISHLATISH
@bot.callback_query_handler(func=lambda call: call.data in ["dl_video", "dl_audio", "dl_full"])
def process_download(call):
    chat_id = call.message.chat.id
    url = user_links.get(chat_id)
    status_msg_id = call.message.message_id

    if not url:
        bot.answer_callback_query(call.id, "❌ Havola topilmadi, qaytadan yuboring.")
        return

    bot_username = bot.get_me().username

    if call.data == "dl_video":
        bot.edit_message_text("⏳ <b>Video yuklanmoqda, kuting...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'downloads/{chat_id}_video.%(ext)s',
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            caption_text = f"✅ <b>Mana siz so'ragan video!</b>\n\n🤖 <b>Bot:</b> @{bot_username}"

            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video, caption=caption_text, parse_mode="HTML")

            bot.delete_message(chat_id, status_msg_id)
            if os.path.exists(filename): os.remove(filename)

        except Exception:
            bot.send_message(chat_id, "❌ Videoni yuklashda xatolik bo'ldi.")

    elif call.data == "dl_audio":
        bot.edit_message_text("⏳ <b>Audio yuklanmoqda, kuting...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/{chat_id}_audio.%(ext)s',
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            caption_text = f"✅ <b>Mana siz so'ragan audio!</b>\n\n🤖 <b>Bot:</b> @{bot_username}"

            with open(filename, 'rb') as audio:
                bot.send_audio(chat_id, audio, caption=caption_text, parse_mode="HTML")

            full_markup = InlineKeyboardMarkup()
            btn_full = InlineKeyboardButton("🔍 To'liq versiyani topish (Full MP3)", callback_data="dl_full")
            full_markup.add(btn_full)

            bot.send_message(chat_id, "👇 <i>Ushbu musiqaning to'liq versiyasini yuklab olishni istaysizmi?</i>", reply_markup=full_markup, parse_mode="HTML")

            bot.delete_message(chat_id, status_msg_id)
            if os.path.exists(filename): os.remove(filename)

        except Exception:
            bot.send_message(chat_id, "❌ Audioni ajratishda xatolik bo'ldi.")

    elif call.data == "dl_full":
        status_msg = bot.send_message(chat_id, "🔍 <b>Qo'shiq ma'lumoti olinmoqda...</b>", parse_mode="HTML")
        
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                track_title = info.get('track') or info.get('title') or ""
                artist = info.get('artist') or ""

            clean_title = re.sub(r'#\w+|https?://\S+|original sound|sound|-.*', '', track_title, flags=re.IGNORECASE).strip()

            if len(clean_title) < 3:
                bot.delete_message(chat_id, status_msg.message_id)
                msg = bot.send_message(chat_id, "✏️ <b>Ushbu videodagi qo'shiq nomini yozib yuboring:</b>\n<i>(Masalan: Rayhon - Sevgilim)</i>", parse_mode="HTML")
                bot.register_next_step_handler(msg, custom_search)
                return

            search_query = f"ytsearch1:{artist} {clean_title} full audio".strip()
            download_full_by_query(chat_id, search_query, status_msg.message_id, bot_username)

        except Exception:
            bot.send_message(chat_id, "❌ Ma'lumot olishda xatolik bo'ldi.")

if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    bot.infinity_polling(skip_pending=True)
