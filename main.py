import telebot
from telebot import types
import os
import signal
import sys
import time
import threading
import requests
import atexit
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настройки из переменных окружения
TOKEN = os.getenv('BOT_TOKEN')

# ===== СПИСОК ВСЕХ АДМИНОВ =====
ADMIN_IDS = [
    913566244,   # ваш ID
    6108135706,  # первый админ
    5330661807,  # второй админ
]

if not TOKEN:
    logger.error("❌ ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
    sys.exit(1)

# Функция для полной очистки вебхука
def cleanup_telegram():
    """Принудительно очищаем все предыдущие подключения"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.post(url, json={"drop_pending_updates": True})
        logger.info(f"✅ Вебхук удален: {response.status_code == 200}")
        
        url = f"https://api.telegram.org/bot{TOKEN}/close"
        response = requests.post(url)
        logger.info(f"✅ Сессии закрыты: {response.status_code == 200}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка очистки: {e}")
        return False

# Очищаем перед запуском
logger.info("🔄 Очистка предыдущих подключений...")
cleanup_telegram()
time.sleep(2)

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
    logger.info("🛑 Получен сигнал остановки, завершаем работу...")
    running = False
    try:
        bot.stop_polling()
        cleanup_telegram()
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(lambda: cleanup_telegram())

def is_admin(user_id):
    """Проверяет, является ли пользователь админом"""
    return user_id in ADMIN_IDS

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    users[user_id] = {}
    logger.info(f"👤 Новый пользователь: {user_id}")
    
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
    
    user_id = str(call.from_user.id)
    if user_id not in users:
        users[user_id] = {}
    
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
    user_id = str(message.from_user.id)
    username = message.from_user.username or "без username"
    
    # Принимаем любой текст без проверок
    user_nick = message.text
    
    if user_id not in users:
        users[user_id] = {}
    
    users[user_id]['nick'] = user_nick
    
    tariff_info = users[user_id].get('tariff', 'Не выбран')
    number_info = users[user_id].get('number', 'Не указан')
    
    # Формируем сообщение для админов
    admin_msg = (
        f"🆕 **НОВАЯ ЗАЯВКА НА ОПЛАТУ!**\n\n"
        f"👤 **Пользователь:** @{username}\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"🎮 **Ник Minecraft:** `{user_nick}`\n"
        f"💰 **Тариф:** {tariff_info}\n"
        f"📱 **Номер:** {number_info}\n"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            "✅ Подтвердить оплату",
            callback_data=f"confirm_{user_id}"
        ),
        types.InlineKeyboardButton(
            "❌ Отклонить",
            callback_data=f"reject_{user_id}"
        )
    )
    markup.add(types.InlineKeyboardButton(
        "💬 Написать пользователю",
        url=f"tg://user?id={user_id}"
    ))
    
    # Отправляем каждому админу из списка
    sent_count = 0
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, admin_msg, parse_mode='Markdown', reply_markup=markup)
            logger.info(f"✅ Заявка отправлена админу {admin_id}")
            sent_count += 1
        except Exception as e:
            logger.error(f"❌ Ошибка отправки админу {admin_id}: {e}")
    
    if sent_count == 0:
        logger.error("🚨 НИ ОДНОМУ АДМИНУ НЕ ОТПРАВЛЕНА ЗАЯВКА!")
        # Отправляем первому админу для проверкиtry:
        try:
            bot.send_message(ADMIN_IDS[0], f"⚠️ КРИТИЧЕСКАЯ ОШИБКА: Заявка от {user_id} не доставлена админам!\n\n{admin_msg}", parse_mode='Markdown')
        except:
            pass
    
    bot.send_message(
        message.chat.id,
        "✅ **Заявка отправлена!**\n\n"
        "Администратор проверит оплату и выдаст доступ.\n"
        "⏳ Обычное время ожидания: от 5 минут до 24 часов.",
        parse_mode='Markdown'
    )
    
    logger.info(f"📨 Заявка от пользователя {user_id} обработана")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def admin_confirm(call):
    # Проверяем, что админ есть в списке
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав администратора")
        return
    
    user_id = call.data.split('_')[1]
    
    if user_id not in users:
        bot.answer_callback_query(call.id, "❌ Пользователь не найден в базе")
        # Но всё равно пробуем отправить доступ
        user_id_int = int(user_id)
    else:
        user_id_int = int(user_id)
    
    nickname = users.get(user_id, {}).get('nick', 'игрок')
    tariff = users.get(user_id, {}).get('tariff', 'тариф')
    
    try:
        # Отправляем пользователю доступ
        bot.send_message(
            user_id_int,
            f"🎉 **Доступ активирован!**\n\n"
            f"✅ Оплата {tariff} подтверждена!\n\n"
            f"📡 **Данные сервера:**\n"
            f"🌐 IP: `{SERVER_IP}`\n"
            f"📦 Версия: `{SERVER_VERSION}`\n\n"
            f"👇 **Для комфортной игры на нашем сервере рекомендуем скачать эти моды:**",
            parse_mode='Markdown'
        )
        
        mods_text = "\n\n".join(MOD_LINKS)
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(
                "📥 Simple Voice Chat",
                url="https://modrinth.com/mod/simple-voice-chat"
            ),
            types.InlineKeyboardButton(
                "📥 Voice Messages",
                url="https://modrinth.com/mod/voice-messages"
            ),
            types.InlineKeyboardButton(
                "📥 Emotecraft",
                url="https://modrinth.com/mod/emotecraft"
            )
        )
        
        bot.send_message(
            user_id_int,
            mods_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
        bot.send_message(
            user_id_int,
            "🎮 **Удачной игры на сервере!**",
            parse_mode='Markdown'
        )
        
        logger.info(f"✅ Доступ выдан пользователю {user_id} админом {call.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки пользователю {user_id}: {e}")
        bot.answer_callback_query(call.id, f"❌ Ошибка: {str(e)[:50]}")
        return
    
    bot.answer_callback_query(call.id, "✅ Доступ выдан")
    
    # Уведомляем других админов
    admin_name = call.from_user.username or f"ID {call.from_user.id}"
    for admin_id in ADMIN_IDS:
        if admin_id != call.from_user.id:
            try:
                bot.send_message(
                    admin_id,
                    f"✅ Админ @{admin_name} подтвердил оплату для пользователя {nickname} (ID: {user_id})"
                )
            except:
                pass
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=call.message.text + "\n\n✅ **ОПЛАТА ПОДТВЕРЖДЕНА** ✅",
            parse_mode='Markdown',
            reply_markup=None
        )
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def admin_reject(call):
    # Проверяем, что админ есть в списке
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав администратора")
        return
    
    user_id = call.data.split('_')[1]
    
    try:
        bot.send_message(
            int(user_id),
            "❌ **Ваша заявка отклонена**\n\n"
            "Возможные причины:\n"
            "• Не подтверждена оплата\n"
            "• Не получен перевод\n"
            "• Некорректные данные\n\n"
            "📞 Для уточнения свяжитесь с поддержкой"
        )
        logger.info(f"❌ Заявка отклонена для пользователя {user_id} админом {call.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки пользователю {user_id}: {e}")
    
    bot.answer_callback_query(call.id, "❌ Заявка отклонена")
    
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
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            "📥 Simple Voice Chat",
            url="https://modrinth.com/mod/simple-voice-chat"
        ),
        types.InlineKeyboardButton(
            "📥 Voice Messages",
            url="https://modrinth.com/mod/voice-messages"
        ),
        types.InlineKeyboardButton(
            "📥 Emotecraft",
            url="https://modrinth.com/mod/emotecraft"
        )
    )
    
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
        "Нажми '📦 Моды' чтобы скачать моды для сервера\n\n"
        "❓ **Проблемы:**\n"
        "Если заявка не отправляется - напиши сюда и мы поможем!"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "📞 Связаться с поддержкой",
        url=f"tg://user?id={ADMIN_IDS[0]}"
    ))
    
    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(commands=['numbers'])
def show_all_numbers(message):
    # Проверяем, что админ есть в списке
    if not is_admin(message.from_user.id):
        return
    
    numbers_text = "📋 **Все номера для оплаты:**\n\n"
    
    for name, number in PAYMENT_NUMBERS:
        numbers_text += f"{name}\n📱 `{number}`\n\n"
    
    bot.send_message(
        message.chat.id,
        numbers_text,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['test'])
def test_bot(message):
    """Команда для проверки работы бота"""
    if not is_admin(message.from_user.id):
        return
    
    bot.send_message(
        message.chat.id,
        "✅ **Бот работает исправно!**\n\n"
        f"👑 Админов в списке: {len(ADMIN_IDS)}\n"
        f"👤 Пользователей в памяти: {len(users)}\n"
        f"🔄 Режим: поллинг",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    """Отправить сообщение всем пользователям (только для админов)"""
    if not is_admin(message.from_user.id):
        return
    
    msg = bot.send_message(
        message.chat.id,
        "📢 Введитесообщение для рассылки всем пользователям:"
    )
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    if not is_admin(message.from_user.id):
        return
    
    text = message.text
    sent = 0
    failed = 0
    
    for user_id in users.keys():
        try:
            bot.send_message(int(user_id), f"📢 **Рассылка:**\n\n{text}", parse_mode='Markdown')
            sent += 1
            time.sleep(0.05)  # Чтобы не превысить лимиты Telegram
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

def keep_alive():
    """Функция для поддержания активности на Render"""
    while running:
        time.sleep(300)  # Каждые 5 минут
        try:
            bot.get_me()
            logger.info(f"✅ Пинг бота: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"❌ Ошибка пинга: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 ЗАПУСК БОТА НА RENDER")
    print("=" * 60)
    print(f"💰 Режим: оплата переводом по номеру телефона")
    print(f"📦 Моды: Simple Voice, Voice Messages, Emotecraft")
    print(f"👑 Админы ({len(ADMIN_IDS)} человек):")
    for i, admin_id in enumerate(ADMIN_IDS, 1):
        print(f"   {i}. ID: {admin_id}")
    print(f"🔄 Режим: поллинг (без вебхука)")
    print("=" * 60)
    
    # Проверка доступности админов
    logger.info("🔍 Проверка доступности админов...")
    for admin_id in ADMIN_IDS:
        try:
            bot.send_chat_action(admin_id, 'typing')
            logger.info(f"✅ Админ {admin_id} доступен")
        except:
            logger.warning(f"⚠️ Админ {admin_id} НЕДОСТУПЕН (возможно не начал чат с ботом)")
    
    # Финальная очистка перед запуском
    logger.info("🔄 Финальная очистка подключений...")
    cleanup_telegram()
    time.sleep(3)
    
    # Запускаем поток для поддержания активности
    alive_thread = threading.Thread(target=keep_alive, daemon=True)
    alive_thread.start()
    
    # Запускаем бота с обработкой ошибок
    retry_count = 0
    max_retries = 10
    
    while running and retry_count < max_retries:
        try:
            logger.info("✅ Бот запущен и ожидает сообщения...")
            bot.polling(none_stop=True, interval=1, timeout=30, skip_pending=True)
        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Ошибка polling (попытка {retry_count}/{max_retries}): {e}")
            
            if "409" in str(e):
                logger.info("🔄 Обнаружен конфликт, выполняем глубокую очистку...")
                cleanup_telegram()
                time.sleep(5)
            
            if running and retry_count < max_retries:
                wait_time = min(30, 5 * retry_count)
                logger.info(f"🔄 Перезапуск через {wait_time} секунд...")
                time.sleep(wait_time)
            else:
                logger.error("❌ Превышено количество попыток перезапуска")
                break
