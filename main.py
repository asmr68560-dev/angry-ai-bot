import telebot
from telebot import types
import os
import signal
import sys
import time
import threading

# Настройки из переменных окружения
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '913566244'))

if not TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
    sys.exit(1)

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

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

# Хранилище пользователей
users = {}

# Флаг для остановки бота
running = True

def signal_handler(signum, frame):
    """Обработка сигналов остановки"""
    global running
    print("\n🛑 Получен сигнал остановки, завершаем работу...")
    running = False
    bot.stop_polling()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

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
    
    # Отправляем админу
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
    
    try:
        bot.send_message(ADMIN_ID, admin_msg, parse_mode='Markdown', reply_markup=markup)
    except Exception as e:
        print(f"Ошибка отправки админу: {e}")
    
    bot.send_message(
        message.chat.id,
        "✅ **Заявка отправлена!**\n\n"
        "Администратор проверит оплату и выдаст доступ.\n"
        "⏳ Обычное время ожидания: от 5 минут до 24 часов.",
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def admin_confirm(call):
    user_id = int(call.data.split('_')[1])
    
    if user_id not in users:
        bot.answer_callback_query(call.id, "Пользователь не найден в базе")
        return
    
    nickname = users[user_id].get('nick', 'игрок')
    tariff = users[user_id].get('tariff', 'тариф')
    
    try:
        bot.send_message(
            user_id,
            f"🎉 **Доступ активирован!**\n\n"
            f"✅ Оплата {tariff} подтверждена!\n\n"
            f"📡 **Данные сервера:**\n"
            f"🌐 IP: `{SERVER_IP}`\n"
            f"📦 Версия: `{SERVER_VERSION}`\n\n"
            f"👇 **Для комфортной игры на нашем сервере рекомендуем скачать эти моды:**",
            parse_mode='Markdown'
        )
        
        mods_text = "\n\n".join(MOD_LINKS)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "📥 Скачать Simple Voice Chat",
            url="https://modrinth.com/mod/simple-voice-chat"
        ))
        markup.add(types.InlineKeyboardButton(
            "📥 Скачать Voice Messages",
            url="https://modrinth.com/mod/voice-messages"
        ))
        markup.add(types.InlineKeyboardButton(
            "📥 Скачать Emotecraft",
            url="https://modrinth.com/mod/emotecraft"
        ))
        
        bot.send_message(
            user_id,
            mods_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
        bot.send_message(
            user_id,
            "🎮 **Удачной игры на сервере!**",
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Ошибка отправки пользователю: {e}")
    
    bot.answer_callback_query(call.id, "✅ Доступ выдан")
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=call.message.text + "\n\n✅ **ОПЛАТА ПОДТВЕРЖДЕНА** ✅",
        parse_mode='Markdown',
        reply_markup=None
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def admin_reject(call):
    user_id = int(call.data.split('_')[1])
    
    try:
        bot.send_message(
            user_id,
            "❌ **Ваша заявка отклонена**\n\n"
            "Возможные причины:\n"
            "• Не подтверждена оплата\n"
            "• Не получен перевод\n"
            "• Некорректные данные\n\n"
            "📞 Для уточнения свяжитесь с поддержкой: @support_username"
        )
    except Exception as e:
        print(f"Ошибка отправки пользователю: {e}")
    
    bot.answer_callback_query(call.id, "❌ Заявка отклонена")
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=call.message.text + "\n\n❌ **ОТКЛОНЕНО** ❌",
        parse_mode='Markdown',
        reply_markup=None
    )

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
        "3. Запусти игру через Fabriс"
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
def show_all_numbers(message):
    if message.from_user.id != ADMIN_ID:
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

def keep_alive():
    """Функция для поддержания активности на Render"""
    while running:
        time.sleep(60)  # Каждую минуту
        try:
            bot.get_me()
            print(f"✅ Пинг бота: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"❌ Ошибка пинга: {e}")

if __name__ == '__main__':
    print("🤖 Бот запускается на Render...")
    print(f"💰 Режим: оплата переводом по номеру телефона")
    print(f"📦 Моды: Simple Voice, Voice Messages, Emotecraft")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("🔄 Режим: поллинг (без вебхука)")
    
    # Запускаем поток для поддержания активности
    alive_thread = threading.Thread(target=keep_alive, daemon=True)
    alive_thread.start()
    
    # Запускаем бота
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"❌ Ошибка polling: {e}")
        time.sleep(5)
        # Перезапуск при ошибке
        if running:
            print("🔄 Перезапуск...")
            os.execv(sys.executable, ['python'] + sys.argv)
