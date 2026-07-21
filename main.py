import os
import threading
import asyncio
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from shazamio import Shazam
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
BOT_TOKEN = "8766383241:AAE2qEIj-zjEvhKV6OoOg9WKAbQzevPrrlM"  # BotFather tokeningiz
bot = telebot.TeleBot(BOT_TOKEN)

user_links = {}

# Shazam funksiyasi uchun xavfsiz async-loop
async def recognize_song(file_path):
    shazam = Shazam()
    out = await shazam.recognize(file_path)
    return out

def get_shazam_result(file_path):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res = loop.run_until_complete(recognize_song(file_path))
    loop.close()
    return res

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(
        message, 
        "👋 <b>Salom! Men Video va Audio yuklovchi botman.</b>\n\n"
        "Menga <b>Instagram</b> yoki <b>TikTok</b> havolasini yuboring!",
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda message: message.text and ("http://" in message.text or "https://" in message.text))
def handle_link(message):
    url = message.text.strip()
    user_links[message.chat.id] = url

    markup = InlineKeyboardMarkup()
    btn_video = InlineKeyboardButton("🎬 Video (MP4)", callback_data="dl_video")
    btn_audio = InlineKeyboardButton("🎵 Audio (MP3)", callback_data="dl_audio")
    markup.add(btn_video, btn_audio)

    bot.reply_to(message, "📥 <b>Formatni tanlang:</b>", reply_markup=markup, parse_mode="HTML")

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
            caption_text = f"✅ <b>Mana siz so'ragan video!</b>\n\n🤖 <b>Bot:</b> @{bot_username}"

            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video, caption=caption_text, parse_mode="HTML")

            bot.delete_message(chat_id, status_msg_id)
            if os.path.exists(filename): os.remove(filename)

        except Exception as e:
            bot.send_message(chat_id, "❌ Videoni yuklashda xatolik bo'ldi. Havolani tekshiring.")

    # 2. AUDIO YUKLASH
    elif call.data == "dl_audio":
        bot.edit_message_text("⏳ <b>Audio yuklanmoqda, kuting...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': f'downloads/{chat_id}_audio.%(ext)s', 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            bot.edit_message_text("📤 <b>Audio tayyor! Sizga yuborilmoqda...</b>", chat_id=chat_id, message_id=status_msg_id, parse_mode="HTML")
            caption_text = f"✅ <b>Mana siz so'ragan audio!</b>\n\n🤖 <b>Bot:</b> @{bot_username}"

            full_markup = InlineKeyboardMarkup()
            btn_full = InlineKeyboardButton("🔍 To'liq versiyasini topish (Full MP3)", callback_data="dl_full")
            full_markup.add(btn_full)

            with open(filename, 'rb') as audio:
                bot.send_audio(chat_id, audio, caption=caption_text, reply_markup=full_markup, parse_mode="HTML")

            bot.delete_message(chat_id, status_msg_id)
            if os.path.exists(filename): os.remove(filename)

        except Exception as e:
            bot.send_message(chat_id, "❌ Audioni ajratishda xatolik bo'ldi.")

    # 3. TO'LIQ MUSIQANI SHAZAM ORQALI TOPISH
    elif call.data == "dl_full":
        status_msg = bot.send_message(chat_id, "🔍 <b>Qo'shiq Shazam orqali tahlil qilinmoqda...</b>", parse_mode="HTML")
        
        temp_opts = {'format': 'bestaudio/best', 'outtmpl': f'downloads/{chat_id}_shazam.%(ext)s', 'quiet': True}
        try:
            # 1. Videodan audioni yuklab olamiz
            with yt_dlp.YoutubeDL(temp_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                temp_filename = ydl.prepare_filename(info)

            # 2. Shazam orqali qo'shiqni aniqlaymiz
            shazam_res = get_shazam_result(temp_filename)
            if os.path.exists(temp_filename): 
                os.remove(temp_filename)

            track_info = shazam_res.get('track')
            if not track_info:
                bot.edit_message_text("❌ Afsuski, bu videodagi musiqani Shazam topa olmadi.", chat_id=chat_id, message_id=status_msg.message_id)
                return

            song_title = track_info.get('title', '')
            song_artist = track_info.get('subtitle', '')
            search_query = f"ytsearch1:{song_artist} - {song_title}"

            bot.edit_message_text(f"🎧 <b>Topildi:</b> {song_artist} - {song_title}\n\n⏳ <b>To'liq versiyasi yuklanmoqda...</b>", chat_id=chat_id, message_id=status_msg.message_id, parse_mode="HTML")

            # 3. YouTube'dan to'liq qo'shiqni yuklaymiz
            full_opts = {'format': 'bestaudio/best', 'outtmpl': f'downloads/{chat_id}_full.%(ext)s', 'quiet': True}
            with yt_dlp.YoutubeDL(full_opts) as ydl:
                search_res = ydl.extract_info(search_query, download=True)
                if 'entries' in search_res and len(search_res['entries']) > 0:
                    full_filename = ydl.prepare_filename(search_res['entries'][0])
                else:
                    full_filename = ydl.prepare_filename(search_res)

            caption_text = f"✅ <b>To'liq qo'shiq yuklab olindi!</b>\n🎵 <b>Nomi:</b> {song_artist} - {song_title}\n\n🤖 <b>Bot:</b> @{bot_username}"

            with open(full_filename, 'rb') as audio:
                bot.send_audio(chat_id, audio, caption=caption_text, parse_mode="HTML")

            bot.delete_message(chat_id, status_msg.message_id)
            if os.path.exists(full_filename): os.remove(full_filename)

        except Exception as err:
            bot.send_message(chat_id, "❌ To'liq musiqani topishda xatolik yuz berdi. Boshqa video bilan sinab ko'ring.")

if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    bot.infinity_polling(skip_pending=True)
