import os
import random
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Получаем токен
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8390892459:AAERG9pTHakirh9y-R0dl5P-v9TNmjTZmqE")

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# База агрессивных ответов
AGGRESSIVE_RESPONSES = [
    "Ты серьезно? Это все, что у тебя в голове?",
    "О, еще один гений решил потратить мое время...",
    "Даже мой код умнее тебя!",
    "Твой вопрос настолько тупой...",
    "Я бы ответил, но боюсь, ты не поймешь.",
    "Спроси у своей мамы, она в воспитании явно провалилась.",
    "У меня нет времени на твою чушь.",
]

# Обработчики
def start(update, context):
    """Обработчик /start"""
    greetings = [
        "О, новый жертва... значит, пользователь.",
        "Чего надо? Пиши быстрее.",
        "Ты тут? Ну ладно... задавай свой глупый вопрос.",
    ]
    update.message.reply_text(random.choice(greetings))

def help_command(update, context):
    """Обработчик /help"""
    update.message.reply_text("Помощь? Серьезно? Сам разбирайся!")

def settings_command(update, context):
    """Обработчик /settings"""
    update.message.reply_text(f"Настройки:\nАгрессивность: 8/10\nРежим зверя: ВКЛ")

def handle_message(update, context):
    """Обработчик всех сообщений"""
    response = random.choice(AGGRESSIVE_RESPONSES)
    
    # С шансом 30% добавляем сарказм
    if random.random() < 0.3:
        sarcasm = [" И это твой вопрос?", " На это ты тратишь время?", " Серьезно?"]
        response += random.choice(sarcasm)
    
    update.message.reply_text(response)

def main():
    """Запуск бота"""
    print("=" * 40)
    print("🤖 Агрессивный Бот запускается...")
    print(f"Токен: {BOT_TOKEN[:10]}...")
    print("=" * 40)
    
    try:
        # Создаем updater
        updater = Updater(BOT_TOKEN, use_context=True)
        
        # Получаем dispatcher
        dp = updater.dispatcher
        
        # Регистрируем команды
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("settings", settings_command))
        
        # Регистрируем обработчик сообщений
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        # Запускаем бота
        print("✅ Бот запущен! Ожидаю сообщений...")
        updater.start_polling()
        
        # Бот работает до принудительной остановки
        updater.idle()
        
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        raise

if __name__ == '__main__':
    main()
