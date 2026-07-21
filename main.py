import os
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from shazamio import Shazam
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. Render serverini uxlab qolmasligi uchun HTTP Server
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
BOT_TOKEN = "8766383241:AAHXYnHOA8IKbRzNf1XNEs1vK-q-wGwDqh4"  # BotFather tokeningizni kiriting
bot = telebot.TeleBot(BOT_TOKEN)

user_links = {}

# Shazam orqali musiqani tanib olish funksiyasi
async def recognize_song(file_path):
    shazam = Shazam()
    out = await shazam.recognize(file_path)
    return out

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(
        message, 
        "👋 <b>Salom! Men Video va Audio yuklovchi botman.</b>\n\n"
        "Menga <b>Instagram</b> yoki <b>TikTok</b> havolasini yuboring!",
        parse_mode="HTML"
    )

# LINK KELGANDA TUGMALARNI CHIQARISH
@bot.message_handler(func=lambda message: message.text and ("http://" in message.text or "https://" in message.text))
def handle_link(message):
    url = message.text.strip()
    user_links[message.chat.id] = url

    markup = InlineKeyboardMarkup()
    btn_video = InlineKeyboardButton("🎬 Video (MP4)", callback_data="dl_video")
    btn_audio = InlineKeyboardButton("🎵 Audio (MP3)", callback_data="dl_audio")
    markup.add(btn_video, btn_audio)

    bot.reply_to(message, "📥 <b>Formatni tanlang:</b>", reply_markup=markup, parse_mode="HTML")

# TUGMALAR BOSILGANDA ISHLAYDIGAN QISM
@bot.callback_query_handler(func=lambda call: call.data in ["dl_video", "dl_audio", "dl_full"])
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
        bot.edit_message_text("⏳ <b>Video yuklanmoqda, kuting...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")
        ydl_opts = {'format': 'best', 'outtmpl': f'downloads/{chat_id}_video.%(ext)s', 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            bot.edit_message_text("📤 <b>Video tayyor! Sizga yuborilmoqda...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")
            caption_text = f"✅ <b>Mana siz so'ragan video yuklab olindi!</b>\n\n🤖 <b>Bot:</b> @{bot_username}"

            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video, caption=caption_text, parse_mode="HTML")

            bot.delete_message(chat_id, status_msg_id)
            if os.path.exists(filename): os.remove(filename)

        except Exception:
            bot.send_message(chat_id, "❌ Videoni yuklashda xatolik bo'ldi. Havolani tekshiring.")

    # 2. QISQA AUDIO YUKLASH (Audio yuborilgach ostida to'liq versiya tugmasi chiqadi)
    elif call.data == "dl_audio":
        bot.edit_message_text("⏳ <b>Audio yuklanmoqda, kuting...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': f'downloads/{chat_id}_audio.%(ext)s', 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            bot.edit_message_text("📤 <b>Audio tayyor! Sizga yuborilmoqda...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")
            caption_text = f"✅ <b>Mana siz so'ragan audio yuklab olindi!</b>\n\n🤖 <b>Bot:</b> @{bot_username}"

            # Audio ostiga "To'liq versiyani topish" tugmasini qo'shamiz
            full_markup = InlineKeyboardMarkup()
            btn_full = InlineKeyboardButton("🔍 To'liq versiyasini topish (Full MP3)", callback_data="dl_full")
            full_markup.add(btn_full)

            with open(filename, 'rb') as audio:
                bot.send_audio(chat_id, audio, caption=caption_text, reply_markup=full_markup, parse_mode="HTML")

            bot.delete_message(chat_id, status_msg_id)
            if os.path.exists(filename): os.remove(filename)

        except Exception:
            bot.send_message(chat_id, "❌ Audioni ajratishda xatolik bo'ldi.")

    # 3. AUDIOGA ULANIB TO'LIQ MUSIQANI SHAZAM ORQALI TOPISH
    elif call.data == "dl_full":
        bot.send_message(chat_id, "🔍 <b>Qo'shiq Shazam orqali tahlil qilinmoqda, kuting...</b>", parse_mode="HTML")
        
        temp_audio_opts = {'format': 'bestaudio/best', 'outtmpl': f'downloads/{chat_id}_shazam.%(ext)s', 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(temp_audio_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                temp_filename = ydl.prepare_filename(info)

            shazam_res = asyncio.run(recognize_song(temp_filename))
            if os.path.exists(temp_filename): os.remove(temp_filename)

            track_info = shazam_res.get('track')
            if not track_info:
                bot.send_message(chat_id, "❌ Afsuski, bu videodagi musiqani aniqlab bo'lmadi.")
                return

            song_title = track_info.get('title', '')
            song_artist = track_info.get('subtitle', '')
            search_query = f"ytsearch1:{song_artist} - {song_title}"

            status_msg = bot.send_message(chat_id, f"🎧 <b>Topildi:</b> {song_artist} - {song_title}\n\n⏳ <b>To'liq versiyasi yuklanmoqda...</b>", parse_mode="HTML")

            full_audio_opts = {'format': 'bestaudio/best', 'outtmpl': f'downloads/{chat_id}_full.%(ext)s', 'quiet': True}
            with yt_dlp.YoutubeDL(full_audio_opts) as ydl:
                info = ydl.extract_info(search_query, download=True)
                full_filename = ydl.prepare_filename(info['entries'][0])

            caption_text = f"✅ <b>To'liq qo'shiq yuklab olindi!</b>\n🎵 <b>Nomi:</b> {song_artist} - {song_title}\n\n🤖 <b>Bot:</b> @{bot_username}"

            with open(full_filename, 'rb') as audio:
                bot.send_audio(chat_id, audio, caption=caption_text, parse_mode="HTML")

            bot.delete_message(chat_id, status_msg.message_id)
            if os.path.exists(full_filename): os.remove(full_filename)

        except Exception:
            bot.send_message(chat_id, "❌ To'liq musiqani topishda xatolik yuz berdi.")

if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    bot.infinity_polling(skip_pending=True)
