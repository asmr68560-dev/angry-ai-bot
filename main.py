import telebot
from telebot import types
import os
import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ===== ФИКТИВНЫЙ ВЕБ-СЕРВЕР ДЛЯ RENDER =====
# Это нужно, чтобы Render не убивал бота (ему нужен открытый порт)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        pass  # Отключаем логирование

def run_health_server():
    """Запускает HTTP сервер на порту 10000 для Health Check"""
    port = int(os.getenv('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"✅ Health check server running on port {port}")
    server.serve_forever()

# Запускаем health check сервер в отдельном потоке
health_thread = threading.Thread(target=run_health_server, daemon=True)
health_thread.start()
time.sleep(1)  # Даем время запуститься
# ===========================================

# ===== НАСТРОЙКИ =====
TOKEN = os.getenv('BOT_TOKEN')

# СПИСОК АДМИНОВ (ВСЕ РАВНЫ)
ADMIN_IDS = [
    913566244,   # вы
    6108135706,  # админ 2
    5330661807,  # админ 3
]

if not TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    exit(1)

# Конфигурация
PAYMENT_NUMBERS = [
    ["🎮 Проходка на один сезон - 25 руб", "+7 (932) 304-54-76"],
    ["⭐️ Проходка на всегда - 85 руб", "+7 (932) 304-54-76"],
    ["👑 Улучшение проходки - 60 руб", "+7 (932) 304-54-76"]
]

MOD_LINKS = [
    "🔊 **Simple Voice Chat** - https://minecraft-inside.ru/mods/185344-simple-voice-chat.html",
    "🎙 **Voice Messages** - https://modrinth.com/plugin/voicemessages",
    "😃 **Emotecraft** - https://minecraft-inside.ru/mods/150286-emotecraft.html"
]

SERVER_IP = "Oxidized.minerent.io"
SERVER_VERSION = "1.21.11 Fabric"

# ===== ФУНКЦИЯ УДАЛЕНИЯ ВЕБХУКА =====
def delete_webhook():
    """Принудительно удаляем вебхук"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.post(url, json={"drop_pending_updates": True})
        print(f"✅ Вебхук удален: {response.status_code == 200}")
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления вебхука: {e}")
        return False

# Удаляем вебхук перед запуском
delete_webhook()
time.sleep(1)

# ===== ИНИЦИАЛИЗАЦИЯ БОТА =====
bot = telebot.TeleBot(TOKEN)

# Хранилище пользователей
users = {}

# ===== ОБРАБОТЧИКИ =====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Тарифы")
    markup.add("📦 Моды")
    markup.add("❓ Помощь")
    
    bot.send_message(
        message.chat.id,
        "🎮 Бот для оплаты доступа к Minecraft серверу\n\n"
        "💰 Тарифы - посмотреть номера для перевода\n"
        "📦 Моды - скачать моды для сервера",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "💰 Тарифы")
def show_tariffs(message):
    tariffs_text = "💳 **Номера для перевода:**\n\n"
    
    for i, (name, number) in enumerate(PAYMENT_NUMBERS, 1):
        tariffs_text += f"{i}. {name}\n📱 Номер: `{number}`\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, (name, _) in enumerate(PAYMENT_NUMBERS):
        markup.add(types.InlineKeyboardButton(
            name,
            callback_data=f"tariff_{i}"
        ))
    
    bot.send_message(
        message.chat.id,
        tariffs_text,
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('tariff_'))
def process_tariff(call):
    tariff_index = int(call.data.split('_')[1])
    tariff_name, tariff_number = PAYMENT_NUMBERS[tariff_index]
    
    user_id = call.from_user.id
    users[user_id] = users.get(user_id, {})
    users[user_id]['tariff'] = tariff_name
    users[user_id]['number'] = tariff_number
    
    instruction = (
        f"✅ Вы выбрали: {tariff_name}\n\n"
        f"📱 **Номер для перевода:**\n`{tariff_number}`\n\n"
        f"📋 **Как оплатить:**\n"
        f"1. Переведите деньги на этот номер\n"
        f"2. Нажмите кнопку 'Я перевел деньги'\n"
        f"3. Напишите свой ник в Minecraft"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "✅ Я перевел деньги",
        callback_data="paid"
    ))
    markup.add(types.InlineKeyboardButton(
        "◀️ Назад к тарифам",
        callback_data="back_to_tariffs"
    ))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=instruction,
        parse_mode='Markdown',
        reply_markup=markup
    )
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_tariffs")
def back_to_tariffs(call):
    tariffs_text = "💳 **Номера для перевода:**\n\n"
    
    for i, (name, number) in enumerate(PAYMENT_NUMBERS, 1):
        tariffs_text += f"{i}. {name}\n📱 Номер: `{number}`\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, (name, _) in enumerate(PAYMENT_NUMBERS):
        markup.add(types.InlineKeyboardButton(
            name,
            callback_data=f"tariff_{i}"
        ))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=tariffs_text,
        parse_mode='Markdown',
        reply_markup=markup
    )
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "paid")
def paid(call):
    bot.edit_message_text(
        "✅ Отлично! Теперь напиши свой ник в Minecraft:",
        call.message.chat.id,
        call.message.message_id
    )
    
    bot.register_next_step_handler(call.message, get_nickname)

def get_nickname(message):
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    
    if user_id not in users:
        users[user_id] = {}
    
    users[user_id]['nick'] = message.text
    
    tariff_info = users[user_id].get('tariff', 'Не выбран')
    number_info = users[user_id].get('number', 'Не указан')
    
    # Сообщение для админов
    admin_msg = (
        f"🆕 **НОВАЯ ЗАЯВКА НА ОПЛАТУ!**\n\n"
        f"👤 **Пользователь:** @{username}\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"🎮 **Ник Minecraft:** `{message.text}`\n"
        f"💰 **Тариф:** {tariff_info}\n"
        f"📱 **Номер:** {number_info}\n"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "✅ Подтвердить оплату",
        callback_data=f"confirm_{user_id}"
    ))
    markup.add(types.InlineKeyboardButton(
        "❌ Отклонить",
        callback_data=f"reject_{user_id}"
    ))
    markup.add(types.InlineKeyboardButton(
        "💬 Написать пользователю",
        url=f"tg://user?id={user_id}"
    ))
    
    # Отправляем ВСЕМ админам
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, admin_msg, parse_mode='Markdown', reply_markup=markup)
            print(f"✅ Заявка отправлена админу {admin_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки админу {admin_id}: {e}")
    
    bot.send_message(
        message.chat.id,
        "✅ **Заявка отправлена!**\n\n"
        "Администратор проверит оплату и выдаст доступ.\n"
        "⏳ Обычное время ожидания: от 5 минут до 24 часов.",
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def admin_confirm(call):
    # Проверяем, что админ есть в списке
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ У вас нет прав")
        return
    
    user_id = int(call.data.split('_')[1])
    
    if user_id not in users:
        bot.answer_callback_query(call.id, "❌ Пользователь не найден")
        return
    
    nickname = users[user_id].get('nick', 'игрок')
    tariff = users[user_id].get('tariff', 'тариф')
    
    # Отправляем пользователю сообщение об одобрении
    try:
        bot.send_message(
            user_id,
            f"🎉 **Доступ активирован!**\n\n"
            f"✅ Оплата {tariff} подтверждена!\n\n"
            f"📡 **Данные сервера:**\n"
            f"🌐 IP: `{SERVER_IP}`\n"
            f"📦 Версия: `{SERVER_VERSION}`\n\n"
            f"👇 **Моды для комфортной игры:**",
            parse_mode='Markdown'
        )
        
        mods_text = "\n\n".join(MOD_LINKS)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "📥 Simple Voice Chat",
            url="https://modrinth.com/mod/simple-voice-chat"
        ))
        markup.add(types.InlineKeyboardButton(
            "📥 Voice Messages",
            url="https://modrinth.com/mod/voice-messages"
        ))
        markup.add(types.InlineKeyboardButton(
            "📥 Emotecraft",
            url="https://modrinth.com/mod/emotecraft"
        ))
        
        bot.send_message(user_id, mods_text, parse_mode='Markdown', reply_markup=markup)
        bot.send_message(user_id, "🎮 **Удачной игры на сервере!**", parse_mode='Markdown')
        
        print(f"✅ Пользователю {user_id} отправлено подтверждение")
        
    except Exception as e:
        print(f"❌ Ошибка отправки пользователю: {e}")
    
    bot.answer_callback_query(call.id, "✅ Доступ выдан")
    
    # Уведомляем других админов, что заявка обработана
    for admin_id in ADMIN_IDS:
        if admin_id != call.from_user.id:
            try:
                bot.send_message(
                    admin_id,
                    f"✅ Админ @{call.from_user.username or 'админ'} подтвердил оплату для {nickname}"
                )
            except:
                pass
    
    # Обновляем сообщение с заявкой
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=call.message.text + "\n\n✅ **ПОДТВЕРЖДЕНО** ✅",
            parse_mode='Markdown',
            reply_markup=None
        )
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def admin_reject(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ У вас нет прав")
        return
    
    user_id = int(call.data.split('_')[1])
    
    # Отправляем пользователю сообщение об отказе
    try:
        bot.send_message(
            user_id,
            "❌ **Ваша заявка отклонена**\n\n"
            "Возможные причины:\n"
            "• Не подтверждена оплата\n"
            "• Не получен перевод\n"
            "• Некорректные данные\n\n"
            "📞 Для уточнения свяжитесь с поддержкой"
        )
        print(f"✅ Пользователю {user_id} отправлен отказ")
    except Exception as e:
        print(f"❌ Ошибка отправки пользователю: {e}")
    
    bot.answer_callback_query(call.id, "❌ Заявка отклонена")
    
    # Уведомляем других админов
    for admin_id in ADMIN_IDS:
        if admin_id != call.from_user.id:
            try:
                bot.send_message(
                    admin_id,
                    f"❌ Админ @{call.from_user.username or 'админ'} отклонил заявку"
                )
            except:
                pass
    
    # Обновляем сообщение с заявкой
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=call.message.text + "\n\n❌ **ОТКЛОНЕНО** ❌",
            parse_mode='Markdown',
            reply_markup=None
        )
    except:
        pass

@bot.message_handler(func=lambda m: m.text == "📦 Моды")
def show_mods(message):
    mods_text = (
        "📦 **Для комфортной игры на нашем сервере рекомендуем скачать эти моды:**\n\n"
        f"{MOD_LINKS[0]}\n\n"
        f"{MOD_LINKS[1]}\n\n"
        f"{MOD_LINKS[2]}\n\n"
        "💡 **Как установить:**\n"
        "1. Скачай Fabric для версии 1.21.11\n"
        "2. Помести моды в папку .minecraft/mods\n"
        "3. Запусти игру через Fabric"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "📥 Simple Voice Chat",
        url="https://modrinth.com/mod/simple-voice-chat"
    ))
    markup.add(types.InlineKeyboardButton(
        "📥 Voice Messages",
        url="https://modrinth.com/mod/voice-messages"
    ))
    markup.add(types.InlineKeyboardButton(
        "📥 Emotecraft",
        url="https://modrinth.com/mod/emotecraft"
    ))
    
    bot.send_message(
        message.chat.id,
        mods_text,
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def help_msg(message):
    help_text = (
        "💳 **Как оплатить переводом:**\n"
        "1. Нажми '💰 Тарифы'\n"
        "2. Выбери тариф\n"
        "3. Переведи деньги на указанный номер\n"
        "4. Нажми '✅ Я перевел деньги'\n"
        "5. Напиши свой ник Minecraft\n"
        "6. Жди подтверждения от администратора\n\n"
        "📦 **Моды:**\n"
        "Нажми '📦 Моды' чтобы скачать моды для сервера"
    )
    
    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['numbers'])
def show_numbers(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    numbers_text = "📋 **Все номера для оплаты:**\n\n"
    
    for name, number in PAYMENT_NUMBERS:
        numbers_text += f"{name}\n📱 `{number}`\n\n"
    
    bot.send_message(
        message.chat.id,
        numbers_text,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: True)
def other(message):
    bot.send_message(
        message.chat.id,
        "Используй кнопки меню:\n"
        "💰 Тарифы - номера для перевода\n"
        "📦 Моды - скачать моды\n"
        "❓ Помощь - связь с поддержкой"
    )

# ===== ЗАПУСК =====
if __name__ == '__main__':
    print("=" * 50)
    print("🤖 ЗАПУСК БОТА НА RENDER")
    print("=" * 50)
    print(f"👑 Админы ({len(ADMIN_IDS)}):")
    for admin_id in ADMIN_IDS:
        print(f"   • {admin_id}")
    print(f"🌐 Health check port: 10000")
    print("=" * 50)
    
    # Бесконечный цикл с перезапуском при ошибке
    retry_count = 0
    while True:
        try:
            print("✅ Бот запущен и ожидает сообщения...")
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            retry_count += 1
            print(f"❌ Ошибка ({retry_count}): {e}")
            print("🔄 Перезапуск через 5 секунд...")
            delete_webhook()
            time.sleep(5)
