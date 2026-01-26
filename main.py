import os
import random
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8390892459:AAERG9pTHakirh9y-R0dl5P-v9TNmjTZmqE")

# База ответов
RESPONSES = [
    "Ты серьезно? Это все, что у тебя в голове?",
    "О, еще один гений решил потратить мое время...",
    "Даже мой код умнее тебя!",
    "Твой вопрос настолько тупой...",
    "Я бы ответил, но боюсь, ты не поймешь.",
]

# Обработчики команд
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("О, новый жертва... Чего надо?")

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Помощь? Серьезно? Сам разбирайся!")

def handle_message(update: Update, context: CallbackContext) -> None:
    response = random.choice(RESPONSES)
    update.message.reply_text(response)

def main() -> None:
    print("🤖 Бот запускается...")
    
    # Создаем updater и передаем токен бота
    updater = Updater(BOT_TOKEN)
    
    # Получаем диспетчер для регистрации обработчиков
    dispatcher = updater.dispatcher
    
    # Регистрируем обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Регистрируем обработчик текстовых сообщений
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Запускаем бота
    print("✅ Бот запущен!")
    updater.start_polling()
    
    # Бот работает до принудительной остановки
    updater.idle()

if __name__ == '__main__':
    main()
