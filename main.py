import telebot
from telebot import types
import os
import sys
import time
import requests
import logging
from flask import Flask, request, abort
import traceback

# Глобальный перехват необработанных исключений
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    print("🚨 Необработанная ошибка:", exc_type)
    traceback.print_exception(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = '8247657980:AAE7hrsVNlxoRpWRfrvvutUJNAbRpiUa_p8'

# Админы
ADMIN_IDS = [
    913566244,
    6108135706,
    5330661807,
]

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Конфигурации
PAYMENT_NUMBERS = [
    ["🎮 Проходка на один сезон - 25 руб", "+7 (932) 304-57-76"],
    ["⭐️ Проходка на всегда - 85 руб", "+7 (932) 304-57-76"],
    ["👑 Улучшение проходки - 60 руб", "+7 (932) 304-57-76"]
]

MOD_LINKS = [
    "🔊 Simple Voice Chat - https://minecraft-inside.ru/mods/185344-simple-voice-chat.html",
    "🎙 Voice Messages - https://modrinth.com/plugin/voicemessages",
    "😃 Emotecraft - https://minecraft-inside.ru/mods/150286-emotecraft.html"
]

SERVER_IP = "Oxidized.minerent.io"
SERVER_VERSION = "1.21.11 Fabric"

users = {}
app = Flask(__name__)

# ============================================
# ВЕБ-СЕРВЕР (ДЛЯ WEBHOOK И HEALTH CHECKS)
# ============================================

@app.route('/')
def home():
    return "✅ Бот работает!", 200

@app.route('/health')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает обновления от Telegram"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        abort(403)

# ============================================
# ВСЕ ОБРАБОТЧИКИ КОМАНД (ваши, без изменений)
# ============================================

@bot.message_handler(commands=['start', 'restart'])
def start(message):
    user_id = str(message.from_user.id)
    users[user_id] = {}
    logger.info(f"👤 Новый пользователь: {user_id}")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Тарифы", "📦 Моды", "❓ Помощь")
    bot.send_message(
        message.chat.id,
        "🎮 Бот для оплаты доступа к Minecraft серверу\n\n"
        "💰 Тарифы - посмотреть номера для перевода\n"
        "📦 Моды - скачать моды для сервера",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_username")
def check_username_callback(call):
    """Проверяет, создал ли пользователь username"""
    username = call.from_user.username
    
    if username:
        # Если создал - показываем тарифы
        bot.answer_callback_query(call.id, "✅ Username найден!")
        
        tariffs_text = "💳 Номера для перевода:\n\n"
        for i, (name, number) in enumerate(PAYMENT_NUMBERS, 1):
            tariffs_text += f"{i}. {name}\n📱 Номер: <code>{number}</code>\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, (name, _) in enumerate(PAYMENT_NUMBERS):
            markup.add(types.InlineKeyboardButton(name, callback_data=f"tariff_{i}"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=tariffs_text,
            parse_mode='HTML',
            reply_markup=markup
        )
    else:
        # Если всё ещё нет - показываем ошибку
        bot.answer_callback_query(call.id, "❌ Всё ещё нет username!", show_alert=True)

@bot.message_handler(commands=['status'])
def bot_status(message):
    if not is_admin(message.from_user.id):
        return
    try:
        me = bot.get_me()
        webhook_info = bot.get_webhook_info()
        status = f"✅ Бот @{me.username} работает\n\n"
        status += f"🆔 ID: <code>{me.id}</code>\n"
        status += f"👥 Админов: {len(ADMIN_IDS)}\n"
        status += f"👤 Пользователей в памяти: {len(users)}\n"
        status += f"🔗 Webhook: {webhook_info.url}\n"
        status += f"⏳ Ожидает обновлений: {webhook_info.pending_update_count}"
    except Exception as e:
        status = f"❌ <b>Бот НЕ отвечает!</b>\n\nОшибка: {e}"
    bot.send_message(message.chat.id, status, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == "💰 Тарифы")
def show_tariffs(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Проверяем есть ли username
    if not username:
        # Если нет - просим создать
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Как создать username", url="https://telegram.org/faq#q-как-мне-найти-людей-по-и"))
        markup.add(types.InlineKeyboardButton("🔄 Я создал, проверить", callback_data="check_username"))
        
        bot.send_message(
            message.chat.id,
            "❌ У вас не установлен username!\n\n"
            "Для оплаты и получения доступа к серверу необходимо иметь username в Telegram.\n\n"
            "📋 Как создать:\n"
            "1. Откройте настройки Telegram\n"
            "2. Нажмите на своё имя\n"
            "3. В поле 'Имя пользователя' введите любой ник\n"
            "4. Сохраните изменения\n\n"
            "После создания нажмите кнопку 'Я создал, проверить'",
            parse_mode='HTML',
            reply_markup=markup
        )
        return
    
    # Если username есть - показываем тарифы
    tariffs_text = "💳 Номера для перевода:\n\n"
    for i, (name, number) in enumerate(PAYMENT_NUMBERS, 1):
        tariffs_text += f"{i}. {name}\n📱 Номер: <code>{number}</code>\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, (name, _) in enumerate(PAYMENT_NUMBERS):
        markup.add(types.InlineKeyboardButton(name, callback_data=f"tariff_{i}"))
    
    bot.send_message(
        message.chat.id,
        tariffs_text,
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('tariff_'))
def process_tariff(call):
    tariff_index = int(call.data.split('_')[1])
    tariff_name, tariff_number = PAYMENT_NUMBERS[tariff_index]
    user_id = str(call.from_user.id)
    if user_id not in users:
        users[user_id] = {}
    users[user_id]['tariff'] = tariff_name
    users[user_id]['number'] = tariff_number
    instruction = (
        f"✅ Вы выбрали: {tariff_name}\n\n"
        f"📱 Номер для перевода:\n<code>{tariff_number}</code>\n\n"
        f"📋 Как оплатить:\n"
        f"1. Переведите деньги на этот номер\n"
        f"2. Нажмите кнопку 'Я перевел деньги'\n"
        f"3. Напишите свой ник в Minecraft"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Я перевел деньги", callback_data="paid"))
    markup.add(types.InlineKeyboardButton("◀️ Назад к тарифам", callback_data="back_to_tariffs"))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=instruction,
        parse_mode='HTML',
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_tariffs")
def back_to_tariffs(call):
    show_tariffs(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "paid")
def paid(call):
    bot.edit_message_text(
        "✅ Отлично! Теперь напиши свой ник в Minecraft:",
        call.message.chat.id,
        call.message.message_id
    )
    bot.register_next_step_handler(call.message, get_nickname)

def get_nickname(message):
    """
    Получает ник Minecraft от пользователя после оплаты
    и отправляет заявку админам
    """
    user_id = str(message.from_user.id)
    username = message.from_user.username
    user_nick = message.text.strip()  # Убираем лишние пробелы
    
    # ========== ПРОВЕРКА 1: Есть ли username? ==========
    if not username:
        # Если нет username - отправляем предупреждение
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Как создать username", 
                                             url="https://telegram.org/faq#q-как-мне-найти-людей-по-и"))
        markup.add(types.InlineKeyboardButton("🔄 Я создал, продолжить", 
                                             callback_data=f"retry_nick_{user_id}"))
        
        bot.send_message(
            message.chat.id,
            "❌ Ошибка: отсутствует username!\n\n"
            "Для отправки заявки необходимо иметь username в Telegram.\n"
            "Это нужно чтобы администратор мог связаться с вами.\n\n"
            "📋 Как создать:\n"
            "1. Откройте настройки Telegram\n"
            "2. Нажмите на своё имя\n"
            "3. В поле 'Имя пользователя' введите любой ник\n"
            "4. Сохраните изменения\n\n"
            "После создания нажмите кнопку 'Я создал, продолжить'",
            parse_mode='HTML',
            reply_markup=markup
        )
        
        # Сохраняем ник временно, чтобы не потерять
        if user_id not in users:
            users[user_id] = {}
        users[user_id]['temp_nick'] = user_nick
        return
    
    # ========== ПРОВЕРКА 2: Ник не пустой? ==========
    if not user_nick:
        bot.send_message(
            message.chat.id,
            "❌ Ник не может быть пустым!\n\n"
            "Пожалуйста, напиши свой ник в Minecraft:",
            parse_mode='HTML'
        )
        # Повторно запрашиваем ник
        bot.register_next_step_handler(message, get_nickname)
        return
    
    # ========== ПРОВЕРКА 3: Ник не слишком длинный? ==========
    if len(user_nick) > 16:
        bot.send_message(
            message.chat.id,
            "❌ Слишком длинный ник!\n\n"
            "Ник в Minecraft не может быть длиннее 16 символов.\n"
            "Пожалуйста, введи правильный ник:",
            parse_mode='HTML'
        )
        bot.register_next_step_handler(message, get_nickname)
        return
    
    # ========== ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ ==========
    
    # Сохраняем ник пользователя
    if user_id not in users:
        users[user_id] = {}
    users[user_id]['nick'] = user_nick
    
    # Получаем информацию о тарифе
    tariff_info = users[user_id].get('tariff', 'Не выбран')
    number_info = users[user_id].get('number', 'Не указан')
    
    # Формируем сообщение для админов
    admin_msg = (
        f"🆕 НОВАЯ ЗАЯВКА НА ОПЛАТУ!\n\n"
        f"👤 Пользователь: @{username}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"🎮 Ник Minecraft: <code>{user_nick}</code>\n"
        f"💰 Тариф: {tariff_info}\n"
        f"📱 Номер: {number_info}\n"
    )
    
    # Кнопки для админов
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"confirm_{user_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")
    )
    markup.add(types.InlineKeyboardButton("💬 Написать пользователю", url=f"tg://user?id={user_id}"))
    
    # Отправляем всем админам
    sent_count = 0
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, admin_msg, parse_mode='HTML', reply_markup=markup)
            logger.info(f"✅ Заявка отправлена админу {admin_id}")
            sent_count += 1
        except Exception as e:
            logger.error(f"❌ Ошибка отправки админу {admin_id}: {e}")
    
    # Сообщаем пользователю
    if sent_count > 0:
        bot.send_message(
            message.chat.id,
            "✅ Заявка отправлена!\n\n"
            "Администратор проверит оплату и выдаст доступ.\n"
            "⏳ Обычное время ожидания: от 5 минут до 24 часов.\n\n"
            f"📝 Ваш ник: <code>{user_nick}</code>\n"
            f"👤 Ваш username: @{username}",
            parse_mode='HTML'
        )
    else:
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Ошибка отправки заявки!</b>\n\n"
            "Администраторы временно недоступны. Пожалуйста, попробуйте позже или свяжитесь с поддержкой.",
            parse_mode='HTML'
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def admin_confirm(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав администратора")
        return
    
    user_id_str = call.data.split('_')[1]
    
    # Проверяем, не обработана ли уже заявка
    if call.message.text and "✅ ОПЛАЧЕНО" in call.message.text or "❌ ОТКЛОНЕНО" in call.message.text:
        bot.answer_callback_query(call.id, "❌ Эта заявка уже обработана другим админом!", show_alert=True)
        return
    
    try:
        user_id_int = int(user_id_str)
    except:
        bot.answer_callback_query(call.id, "❌ Ошибка ID")
        return
    
    nickname = users.get(user_id_str, {}).get('nick', 'игрок')
    tariff = users.get(user_id_str, {}).get('tariff', 'тариф')
    
    # Отправляем сообщение пользователю
    try:
        bot.send_message(
            int(user_id_str),
            f"🎉 Доступ активирован!\n\n"
            f"✅ Оплата {tariff} подтверждена!\n\n"
            f"📡 Данные сервера:\n"
            f"🌐 IP: <code>{SERVER_IP}</code>\n"
            f"📦 Версия: <code>{SERVER_VERSION}</code>\n\n"
            f"👇 Для комфортной игры на нашем сервере рекомендуем скачать эти моды:",
            parse_mode='HTML'
        )
        
        mods_text = "\n\n".join(MOD_LINKS)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📥 Simple Voice Chat", url="https://modrinth.com/mod/simple-voice-chat"),
            types.InlineKeyboardButton("📥 Voice Messages", url="https://modrinth.com/mod/voice-messages"),
            types.InlineKeyboardButton("📥 Emotecraft", url="https://modrinth.com/mod/emotecraft")
        )
        bot.send_message(int(user_id_str), mods_text, parse_mode='HTML', reply_markup=markup)
        bot.send_message(int(user_id_str), "🎮 <b>Удачной игры на сервере!</b>", parse_mode='HTML')
        
        logger.info(f"✅ Доступ выдан пользователю {user_id_str} админом {call.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки пользователю {user_id_str}: {e}")
        bot.answer_callback_query(call.id, f"❌ Ошибка: {str(e)[:50]}")
        return
    
    # ИЗМЕНЯЕМ СООБЩЕНИЕ У АДМИНА - убираем кнопки и показываем кто подтвердил
    admin_name = call.from_user.username or f"админ {call.from_user.id}"
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=call.message.text + "\n\n✅ ЗАЯВКА ОДОБРЕНА ✅",
            parse_mode='HTML',
            reply_markup=None  # Убираем кнопки!
        )
    except:
        pass
    
    bot.answer_callback_query(call.id, "✅ Доступ выдан")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def admin_reject(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав администратора")
        return
    
    user_id_str = call.data.split('_')[1]
    
    # Проверяем, не обработана ли уже заявка
    if call.message.text and "✅ ОДОБРЕНО" in call.message.text or "❌ ОТКЛОНЕНО" in call.message.text:
        bot.answer_callback_query(call.id, "❌ Эта заявка уже обработана другим админом!", show_alert=True)
        return
    
    # Отправляем сообщение пользователю об отклонении
    try:
        bot.send_message(
            int(user_id_str),
            "❌ Ваша заявка отклонена\n\n"
            "Возможные причины:\n"
            "• Не подтверждена оплата\n"
            "• Не получен перевод\n"
            "• Некорректные данные\n\n"
            "📞 Для уточнения свяжитесь с поддержкой",
            parse_mode='HTML'
        )
        logger.info(f"❌ Заявка отклонена для пользователя {user_id_str} админом {call.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки пользователю {user_id_str}: {e}")
    
    # ИЗМЕНЯЕМ СООБЩЕНИЕ У АДМИНА - убираем кнопки и показываем кто отклонил
    admin_name = call.from_user.username or f"админ {call.from_user.id}"
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=call.message.text + f"\n\n❌ ЗАЯВКА ОТКЛОНЕНА ❌",
            parse_mode='HTML',
            reply_markup=None  # Убираем кнопки!
        )
    except:
        pass
    
    bot.answer_callback_query(call.id, "❌ Заявка отклонена")

@bot.message_handler(func=lambda m: m.text == "📦 Моды")
def show_mods(message):
    mods_text = (
        "📦 Для комфортной игры на нашем сервере рекомендуем скачать эти моды:\n\n"
        f"{MOD_LINKS[0]}\n\n"
        f"{MOD_LINKS[1]}\n\n"
        f"{MOD_LINKS[2]}\n\n"
        "💡 Как установить:\n"
        "1. Скачай Fabric для версии 1.21.11\n"
        "2. Помести моды в папку .minecraft/mods\n"
        "3. Запусти игру через Fabric"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📥 Simple Voice Chat", url="https://modrinth.com/mod/simple-voice-chat"),
        types.InlineKeyboardButton("📥 Voice Messages", url="https://modrinth.com/mod/voice-messages"),
        types.InlineKeyboardButton("📥 Emotecraft", url="https://modrinth.com/mod/emotecraft")
    )
    bot.send_message(
        message.chat.id,
        mods_text,
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def help_msg(message):
    help_text = (
        "💳 Как оплатить переводом:\n"
        "1. Нажми '💰 Тарифы'\n"
        "2. Выбери тариф\n"
        "3. Переведи деньги на указанный номер\n"
        "4. Нажми '✅ Я перевел деньги'\n"
        "5. Напиши свой ник Minecraft\n"
        "6. Жди подтверждения от администратора\n\n"
        "📦 Моды:\n"
        "Нажми '📦 Моды' чтобы скачать моды для сервера\n\n"
        "❓ Проблемы:\n"
        "Если заявка не отправляется - напиши сюда и мы поможем!"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📞 Связаться с поддержкой", url=f"tg://user?id={ADMIN_IDS[0]}"))
    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(commands=['numbers'])
def show_all_numbers(message):
    if not is_admin(message.from_user.id):
        return
    numbers_text = "📋 <b>Все номера для оплаты:</b>\n\n"
    for name, number in PAYMENT_NUMBERS:
        numbers_text += f"{name}\n📱 <code>{number}</code>\n\n"
    bot.send_message(
        message.chat.id,
        numbers_text,
        parse_mode='HTML'
    )

@bot.message_handler(commands=['test'])
def test_bot(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(
        message.chat.id,
        f"✅ Бот работает исправно!\n\n"
        f"👑 Админов в списке: {len(ADMIN_IDS)}\n"
        f"👤 Пользователей в памяти: {len(users)}\n"
        f"🔗 Режим: webhook",
        parse_mode='HTML'
    )

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.send_message(message.chat.id, "📢 Введите сообщение для рассылки всем пользователям:")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    if not is_admin(message.from_user.id):
        return
    text = message.text
    sent = 0
    failed = 0
    for user_id in list(users.keys()):
        try:
            bot.send_message(int(user_id), f"📢 <b>Рассылка:</b>\n\n{text}", parse_mode='HTML')
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1
    bot.send_message(
        message.chat.id,
        f"✅ Рассылка завершена!\n"
        f"📨 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
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

def is_admin(user_id):
    return user_id in ADMIN_IDS

def check_admins():
    """Проверка доступности админов"""
    for admin_id in ADMIN_IDS:
        try:
            bot.send_chat_action(admin_id, 'typing')
            logger.info(f"✅ Админ {admin_id} доступен")
        except:
            logger.warning(f"⚠️ Админ {admin_id} НЕДОСТУПЕН (нужно написать /start)")

# ============================================
# ЗАПУСК
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 ЗАПУСК БОТА НА RENDER (WEBHOOK)")
    print("=" * 60)
    print(f"💰 Тарифов: {len(PAYMENT_NUMBERS)}")
    print(f"📦 Модов: {len(MOD_LINKS)}")
    print(f"👑 Админы ({len(ADMIN_IDS)} человек):")
    for i, admin_id in enumerate(ADMIN_IDS, 1):
        print(f"   {i}. ID: {admin_id}")
    print("=" * 60)
    
    # Получаем URL Render
    render_url = os.environ.get('RENDER_EXTERNAL_URL')
    if not render_url:
        print("⚠️ ВНИМАНИЕ: RENDER_EXTERNAL_URL не найден!")
        print("📌 Если вы тестируете локально, используйте ngrok")
        print("📌 На Render этот URL создается автоматически")
        render_url = "https://ваш-сервер.render.com"  # Заглушка
    
    webhook_url = f"{render_url}/webhook"
    print(f"🔗 Webhook URL: {webhook_url}")
    
    # Устанавливаем webhook
    print("\n🔄 Удаляем старый webhook...")
    bot.remove_webhook()
    time.sleep(1)
    
    print("🔄 Устанавливаем новый webhook...")
    try:
        bot.set_webhook(url=webhook_url)
        print("✅ Webhook успешно установлен!")
        
        # Проверяем webhook
        webhook_info = bot.get_webhook_info()
        print(f"📊 Информация о webhook:")
        print(f"   • URL: {webhook_info.url}")
        print(f"   • Ожидает обновлений: {webhook_info.pending_update_count}")
        print(f"   • Ошибок: {webhook_info.last_error_message or 'нет'}")
        
    except Exception as e:
        print(f"❌ Ошибка установки webhook: {e}")
        print("🔄 Пробуем альтернативный метод...")
        try:
            requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
            time.sleep(1)
            requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", 
                         json={"url": webhook_url})
            print("✅ Webhook установлен через requests")
        except Exception as e2:
            print(f"❌ И этот метод не сработал: {e2}")
    
    print("\n🚀 Запуск Flask сервера...")
    print("=" * 60)
    
    # Проверяем админов
    check_admins()
    
    # Запускаем Flask
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
