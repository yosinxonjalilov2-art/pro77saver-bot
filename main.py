import os
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot

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

    try:
        api_url = "https://api.cobalt.tools/api/json"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "vQuality": "max"
        }

        response = requests.post(api_url, json=payload, headers=headers, timeout=20)
        data = response.json()

        if data.get("status") in ["stream", "redirect"]:
            video_url = data.get("url")
            bot.send_video(message.chat.id, video_url, reply_to_message_id=message.message_id)
            bot.delete_message(message.chat.id, status_message.message_id)
        elif data.get("status") == "picker":
            picker_items = data.get("picker", [])
            if picker_items and picker_items[0].get("type") == "video":
                video_url = picker_items[0].get("url")
                bot.send_video(message.chat.id, video_url, reply_to_message_id=message.message_id)
                bot.delete_message(message.chat.id, status_message.message_id)
            else:
                bot.edit_message_text("❌ Ushbu havoladan video topilmadi.", chat_id=message.chat.id, message_id=status_message.message_id)
        else:
            bot.edit_message_text("❌ Videoni yuklashning imkoni bo'lmadi yoki havola xato.", chat_id=message.chat.id, message_id=status_message.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)}", chat_id=message.chat.id, message_id=status_message.message_id)

if __name__ == "__main__":
    bot.infinity_polling()
