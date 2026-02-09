import telebot
import json
import os
from telebot import types
from datetime import datetime

BOT_TOKEN = "8338126586:AAGdhwSctAd4gfxFpAzb3Sf-X5sUU8iBLmg"
ADMINS = [1789130787, 8084962225]

LOGS_FILE = "bot_logs.json"

bot = telebot.TeleBot(BOT_TOKEN)

if not os.path.exists(LOGS_FILE):
    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def save_log(user_id, username, first_name, file_type, file_id, caption=None):
    with open(LOGS_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "username": username or "нет",
        "first_name": first_name or "нет",
        "file_type": file_type,
        "file_id": file_id,
        "caption": caption or "без подписи"
    }

    logs.append(log_entry)

    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def get_logs():
    with open(LOGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@bot.message_handler(commands=["start"])
def start_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_photo = types.KeyboardButton("📸 Отправить фото")
    btn_video = types.KeyboardButton("🎥 Отправить видео")
    markup.add(btn_photo, btn_video)

    bot.send_message(
        message.chat.id,
        "👋 Привет! Выберите, что вы хотите отправить:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "📸 Отправить фото")
def photo_mode(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(
        message.chat.id,
        "🖼 Отправьте фото (можно с подписью):",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, handle_photo)


@bot.message_handler(func=lambda message: message.text == "🎥 Отправить видео")
def video_mode(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(
        message.chat.id,
        "🎬 Отправьте видео (можно с подписью):",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, handle_video)


def handle_photo(message):
    if message.photo:
        file_id = message.photo[-1].file_id
        caption = message.caption

        save_log(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            file_type="photo",
            file_id=file_id,
            caption=caption
        )

        success_count = 0
        for admin_id in ADMINS:
            try:
                bot.send_photo(
                    admin_id,
                    file_id,
                    caption=f"👤 Пользователь: @{message.from_user.username or 'нет'} (ID: {message.from_user.id})\n"
                            f"📝 Подпись: {caption or 'без подписи'}\n"
                            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
                success_count += 1
            except Exception as e:
                print(f"❌ Не удалось отправить фото админу {admin_id}: {e}")

        bot.send_message(
            message.chat.id,
            f"✅ Фото отправлено {success_count}/{len(ADMINS)} администраторам!"
        )
    else:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, отправьте именно фото.")
        bot.register_next_step_handler(message, handle_photo)


def handle_video(message):
    if message.video:
        file_id = message.video.file_id
        caption = message.caption

        save_log(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            file_type="video",
            file_id=file_id,
            caption=caption
        )

        success_count = 0
        for admin_id in ADMINS:
            try:
                bot.send_video(
                    admin_id,
                    file_id,
                    caption=f"👤 Пользователь: @{message.from_user.username or 'нет'} (ID: {message.from_user.id})\n"
                            f"📝 Подпись: {caption or 'без подписи'}\n"
                            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
                success_count += 1
            except Exception as e:
                print(f"❌ Не удалось отправить видео админу {admin_id}: {e}")

        bot.send_message(
            message.chat.id,
            f"✅ Видео отправлено {success_count}/{len(ADMINS)} администраторам!"
        )
    else:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, отправьте именно видео.")
        bot.register_next_step_handler(message, handle_video)


@bot.message_handler(commands=["logs"])
def logs_handler(message):
    if message.from_user.id not in ADMINS:
        bot.send_message(message.chat.id, "🔒 У вас нет доступа к этой команде.")
        return

    logs = get_logs()

    if not logs:
        bot.send_message(message.chat.id, "📋 Логи пусты.")
        return

    report = f"📄 Всего записей: {len(logs)}\nПоследние 10:\n\n"
    for log in logs[-10:][::-1]:
        report += (
            f"⏰ {log['timestamp']}\n"
            f"🆔 ID: {log['user_id']}\n"
            f"👤 @{log['username']} ({log['first_name']})\n"
            f"📎 Тип: {log['file_type']}\n"
            f"📝 Подпись: {log['caption']}\n"
            f"{'─' * 30}\n"
        )

    bot.send_message(message.chat.id, report)
    bot.send_document(message.chat.id, open(LOGS_FILE, "rb"), caption="💾 Полный файл логов")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.text.startswith("/"):
        bot.send_message(message.chat.id, "❓ Неизвестная команда. Используйте /start для начала.")
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("📸 Отправить фото", "🎥 Отправить видео")
        bot.send_message(
            message.chat.id,
            "❓ Пожалуйста, выберите действие через меню:",
            reply_markup=markup
        )


if __name__ == "__main__":
    print("✅ Бот запущен!")
    print(f"ℹ️  Список админов: {ADMINS}")
    bot.infinity_polling()