import os
import sys
import json
import time
import random
import asyncio
import logging
import httpx
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask
from threading import Thread

# ========== ВЕБ-СЕРВЕР ДЛЯ RENDER ==========
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 Агрессивный Telegram Bot</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 800px;
                width: 90%;
            }
            .emoji {
                font-size: 80px;
                margin-bottom: 20px;
                animation: bounce 2s infinite;
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
            }
            .status {
                color: #4CAF50;
                font-size: 24px;
                font-weight: bold;
                margin: 20px 0;
                padding: 10px;
                background: #f0f9f0;
                border-radius: 10px;
                border-left: 5px solid #4CAF50;
            }
            .info {
                color: #666;
                line-height: 1.6;
                margin: 20px 0;
            }
            .buttons {
                margin-top: 30px;
            }
            .btn {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 12px 24px;
                margin: 0 10px;
                border-radius: 50px;
                text-decoration: none;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            .btn:hover {
                background: #764ba2;
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            }
            .footer {
                margin-top: 30px;
                color: #999;
                font-size: 14px;
            }
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-20px); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="emoji">🤖</div>
            <h1>Агрессивный Telegram Bot с AI</h1>
            <div class="status">✅ Сервис активен и работает!</div>
            <div class="info">
                Этот бот использует искусственный интеллект DeepSeek для генерации саркастичных и агрессивных ответов.

                Настроение бота меняется в зависимости от вашего общения.
            </div>
            <div class="buttons">
                <a href="/health" class="btn">Проверить здоровье</a>
                <a href="/ping" class="btn">Тест Ping</a>
                <a href="https://t.me/your_bot_username" class="btn" target="_blank">Открыть в Telegram</a>
            </div>
            <div class="footer">
                Сервис работает на Render • Авто-деплой из GitHub • Версия 2.0
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    health_status = {
        "status": "healthy",
        "service": "aggressive-telegram-bot",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0",
        "ai_enabled": True,
        "platform": "Render"
    }
    return json.dumps(health_status, ensure_ascii=False, indent=2), 200, {'Content-Type': 'application/json'}

@app.route('/ping')
def ping():
    return "🏓 Pong! Бот активен и готов к работе.", 200

@app.route('/api/status')
def api_status():
    status = {
        "bot": "running",
        "ai": "connected" if os.getenv("DEEPSEEK_API_KEY") else "disabled",
        "start_time": app.config.get('start_time', datetime.now().isoformat()),
        "requests_served": app.config.get('request_count', 0) + 1
    }
    app.config['request_count'] = app.config.get('request_count', 0) + 1
    return json.dumps(status, ensure_ascii=False), 200

def run_web_server():
    """Запускаем Flask сервер в отдельном потоке"""
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Запускаю веб-сервер на порту {port}")
    app.config['start_time'] = datetime.now().isoformat()
    app.config['request_count'] = 0
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Запускаем веб-сервер в отдельном потоке
print("🔄 Инициализация веб-сервера для Render...")
web_thread = Thread(target=run_web_server, daemon=True)
web_thread.start()

# Даем время Flask запуститься
time.sleep(2)
print("✅ Веб-сервер запущен успешно!")

# ========== НАСТРОЙКИ БОТА ==========
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
USE_FREE_AI = os.getenv("USE_FREE_AI", "True") == "True"
AGGRESSION_LEVEL = int(os.getenv("AGGRESSION_LEVEL", "8"))
SAVAGE_MODE = os.getenv("SAVAGE_MODE", "True") == "True"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-2da50845f9424f91ad4d076dabea0a61")

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== ПРОВЕРКА КЛЮЧЕЙ ==========
print("🔑 Проверка конфигурации...")
print(f"   BOT_TOKEN: {'✅ Установлен' if BOT_TOKEN and BOT_TOKEN != '8363576109:AAGr6jPhLmPa4er40n_4nWaExbC6Ufw8spg' else '❌ ОШИБКА: Не установлен!'}")
print(f"   DEEPSEEK_API_KEY: {'✅ Установлен' if DEEPSEEK_API_KEY else '⚠️  Не установлен (AI отключен)'}")
print(f"   AGGRESSION_LEVEL: {AGGRESSION_LEVEL}")
print(f"   USE_FREE_AI: {USE_FREE_AI}")

if not BOT_TOKEN or BOT_TOKEN == "8363576109:AAGr6jPhLmPa4er40n_4nWaExbC6Ufw8spg":
    print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не установлен BOT_TOKEN!")
    print("📝 Инструкция для Render:")
    print("1. Зайдите в Dashboard Render")
    print("2. Выберите ваш сервис")
    print("3. Нажмите 'Environment'")
    print("4. Добавьте переменную: BOT_TOKEN = ваш_токен_от_BotFather")
    print("5. Сохраните и перезапустите сервис")
    sys.exit(1)

# ========== СИСТЕМА НАСТРОЕНИЯ ==========
class BotMood:
    def __init__(self):
        self.user_mood = defaultdict(lambda: {
            'score': 50,
            'timeout_until': None,
            'last_interaction': datetime.now(),
            'offense_count': 0,
            'message_count': 0
        })
        self.timeout_duration = 300
    
    def is_user_blocked(self, user_id):
        user_data = self.user_mood[user_id]
        if user_data['timeout_until'] and datetime.now() < user_data['timeout_until']:
            return True
        return False
    
    def get_timeout_remaining(self, user_id):
        user_data = self.user_mood[user_id]
        if user_data['timeout_until']:
            remaining = user_data['timeout_until'] - datetime.now()
            if remaining.total_seconds() > 0:
                return int(remaining.total_seconds())
        return 0
    
    def process_message(self, user_id, message):
        user_data = self.user_mood[user_id]
        
        if self.is_user_blocked(user_id):
            return "TIMEOUT"
        
        user_data['last_interaction'] = datetime.now()
        user_data['message_count'] += 1
        
        message_lower = message.lower()
        mood_change = 0
        
        # Плохие слова
        bad_words = ['дурак', 'идиот', 'тупой', 'дебил', 'мудак', 'жопа', 'говно', 'бля', 'сука', 'пизда']
        for bad_word in bad_words:
            if bad_word in message_lower:
                mood_change -= 15
                user_data['offense_count'] += 1
                logger.info(f"Пользователь {user_id} использовал плохое слово: {bad_word}")
                break
        
        # Вежливые слова
        polite_words = ['пожалуйста', 'спасибо', 'благодарю', 'извини', 'прости']
        for word in polite_words:
            if word in message_lower:
                mood_change += 8
                break
        
        # Комплименты
        compliments = ['умный', 'крутой', 'классный', 'лучший', 'отличный']
        for compliment in compliments:
            if compliment in message_lower:
                mood_change += 10
                break
        
        # Обновляем настроение
        user_data['score'] = max(0, min(100, user_data['score'] + mood_change))
        
        # Тайм-аут при плохом поведении
        if user_data['score'] < 20 and user_data['offense_count'] >= 2:
            user_data['timeout_until'] = datetime.now() + timedelta(seconds=self.timeout_duration)
            logger.warning(f"Пользователь {user_id} заблокирован на 5 минут")
            return "TIMEOUT_BLOCK"
        
        return mood_change

# ========== AI МОДУЛЬ ==========
class AIModule:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=10.0)
        self.stats = {'requests': 0, 'success': 0, 'failed': 0}
    
    async def generate_response(self, user_message, aggression_level, user_mood):
        """Генерируем ответ через DeepSeek API"""
        self.stats['requests'] += 1
        
        if not self.api_key or self.api_key == "sk-2da50845f9424f91ad4d076dabea0a61":
            return await self._fallback_response(user_message, user_mood)
        
        try:
            # Создаем промпт
            mood_desc = "раздраженный" if user_mood < 30 else "саркастичный" if user_mood < 60 else "нейтральный"
            
            prompt = f"""Ты - агрессивный, саркастичный Telegram-бот. Уровень агрессии: {aggression_level}/10.
Твое настроение: {mood_desc} ({user_mood}/100).
Ответь на сообщение пользователя язвительно, с сарказмом. Будь кратким (1-2 предложения).

Сообщение пользователя: "{user_message}"

Твой ответ:"""
            
            response = await self.client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100,
                    "temperature": 0.7 + (aggression_level / 20)
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data['choices'][0]['message']['content'].strip()
                self.stats['success'] += 1
                return ai_response
            else:
                self.stats['failed'] += 1
                return await self._fallback_response(user_message, user_mood)
                
        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f"AI ошибка: {e}")
            return await self._fallback_response(user_message, user_mood)
    
    async def _fallback_response(self, user_message, user_mood):
        """Резервный ответ"""
        responses = [
            "Интересно... нет, не интересно.",
            "Ты серьезно это спрашиваешь?",
            "Мой процессор чуть не сгорел от твоего вопроса.",
            "Спроси что-нибудь посложнее... шучу, не справлюсь."
        ]
        
        response = random.choice(responses)
        
        if user_mood < 30:
            response += " И вообще, ты меня бесишь!"
        elif user_mood > 70:
            response += " Но ты сегодня мил, поэтому отвечаю."
        
        return response
    
    def get_stats(self):
        """Статистика AI"""
        success_rate = (self.stats['success'] / self.stats['requests'] * 100) if self.stats['requests'] > 0 else 0
        return {
            'requests': self.stats['requests'],
            'success': self.stats['success'],
            'failed': self.stats['failed'],
            'success_rate': round(success_rate, 1)
        }

# ========== БАЗА ОТВЕТОВ ==========
AGGRESSIVE_RESPONSES = [
    "Ты серьезно? Это все, что у тебя в голове?",
    "О, еще один гений решил потратить мое время...",
    "Даже мой код умнее тебя, и в нем только нули и единицы!",
    "Твой вопрос настолько тупой, что у меня даже синтаксическая ошибка возникла.",
    "Я бы ответил, но боюсь, ты не поймешь слова длиннее трех букв.",
    "Ты - ошибка в матрице, которую нужно исправить.",
    "Даже спам-боты полезнее тебя.",
    "Твое существование - аргумент против теории эволюции.",
]

POLITE_RESPONSES = [
    "Привет! Рад тебя видеть. Что ты хотел узнать?",
    "Здравствуй! Чем могу помочь?",
    "Добрый день! Задавай вопрос, постараюсь ответить.",
    "О, здравствуй! Что тебя интересует?",
    "Приветствую! Готов ответить на твои вопросы.",
]

TIMEOUT_RESPONSES = [
    "Ты меня так достал, что я решил взять перерыв на 5 минут.",
    "Всё, хватит! Я ухожу в игнор на 5 минут.",
    "Мое терпение лопнуло! Возвращайся через 5 минут.",
]

# ========== ТЕЛЕГРАМ БОТ ==========
class SimpleTelegramBot:
    def __init__(self, token, deepseek_api_key):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = 0
        self.client = httpx.AsyncClient(timeout=30.0)
        self.mood_system = BotMood()
        self.ai_module = AIModule(deepseek_api_key)
        self.user_history = defaultdict(list)
        self.stats = {
            'total_messages': 0,
            'users': set(),
            'start_time': datetime.now()
        }
        
        # Проверяем токен
        self._check_token()
    
    async def _check_token(self):
        """Проверяем, что токен рабочий"""
        try:
            response = await self.client.get(f"{self.base_url}/getMe")
            if response.status_code == 200:
                bot_info = response.json()['result']
                print(f"✅ Бот подключен: @{bot_info['username']} ({bot_info['first_name']})")
                return True
            else:
                print(f"❌ Ошибка подключения: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка проверки токена: {e}")
            return False
    
    async def get_updates(self):
        """Получаем обновления от Telegram"""
        try:
            response = await self.client.get(
                f"{self.base_url}/getUpdates",
                params={
                    "offset": self.last_update_id + 1,
                    "timeout": 10,
                    "allowed_updates": ["message"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result", [])
        except Exception as e:
            logger.error(f"Ошибка получения updates: {e}")
        
        return []
    
    async def send_message(self, chat_id, text):
        """Отправляем сообщение"""
        try:
            # Обрезаем длинные сообщения
            if len(text) > 4000:
                text = text[:3997] + "..."
            
            response = await self.client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
            )
            
            return response.status_code == 200
            except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            return False
    
    async def process_message(self, message):
        """Обрабатываем сообщение"""
        self.stats['total_messages'] += 1
        
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        user_name = message["from"].get("first_name", "Аноним")
        text = message.get("text", "").strip()
        
        if not text:
            return
        
        # Добавляем пользователя в статистику
        self.stats['users'].add(user_id)
        
        # Проверяем настроение
        mood_result = self.mood_system.process_message(user_id, text)
        
        # Тайм-аут
        if mood_result == "TIMEOUT":
            remaining = self.mood_system.get_timeout_remaining(user_id)
            if remaining > 0:
                await self.send_message(chat_id, f"⏰ Я все еще злюсь на тебя! Возвращайся через {remaining} секунд.")
            return
        elif mood_result == "TIMEOUT_BLOCK":
            await self.send_message(chat_id, random.choice(TIMEOUT_RESPONSES))
            return
        
        # Сохраняем историю
        self.user_history[user_id].append(text)
        if len(self.user_history[user_id]) > 5:
            self.user_history[user_id] = self.user_history[user_id][-5:]
        
        # Команды
        if text.startswith("/"):
            await self._handle_command(chat_id, user_id, text, user_name)
            return
        
        # Обычные сообщения
        response = await self.generate_response(text, user_id, user_name)
        await self.send_message(chat_id, response)
    
    async def _handle_command(self, chat_id, user_id, text, user_name):
        """Обработка команд"""
        if text == "/start":
            welcome = f"""🤖 Привет, {user_name}!

Я - саркастичный бот с AI. Мое настроение зависит от твоего общения.

📌 Команды:
/help - Справка
/mood - Мое настроение
/stats - Статистика
/ai - AI ответ
/reset - Сбросить настроение

💡 Будь вежлив, и я буду отвечать нормально!"""
            await self.send_message(chat_id, welcome)
            
        elif text == "/help":
            help_text = """📋 КОМАНДЫ:

/start - Начало
/help - Эта справка
/mood - Настроение бота
/stats - Статистика
/ai - AI ответ
/reset - Сбросить настроение
/ping - Проверка работы"""
            await self.send_message(chat_id, help_text)
            
        elif text == "/mood":
            user_data = self.mood_system.user_mood[user_id]
            mood_emoji = "😊" if user_data['score'] >= 70 else "🙂" if user_data['score'] >= 40 else "😠"
            await self.send_message(chat_id, f"{mood_emoji} Настроение: {user_data['score']}/100")
            
        elif text == "/stats":
            user_data = self.mood_system.user_mood[user_id]
            ai_stats = self.ai_module.get_stats()
            stats_text = f"""📊 СТАТИСТИКА:

Сообщений от вас: {user_data['message_count']}
Настроение: {user_data['score']}/100
Оскорблений: {user_data['offense_count']}

🤖 AI статистика:
Запросов: {ai_stats['requests']}
Успешно: {ai_stats['success_rate']}%"""
            await self.send_message(chat_id, stats_text)
            
        elif text == "/reset":
            self.mood_system.user_mood[user_id]['score'] = 50
            self.mood_system.user_mood[user_id]['offense_count'] = 0
            await self.send_message(chat_id, "✅ Настроение сброшено!")
            
        elif text.startswith("/ai"):
            query = text[4:].strip() or "Привет, ответь что-нибудь"
            await self.send_message(chat_id, "🤖 Генерирую ответ...")
            user_data = self.mood_system.user_mood[user_id]
            response = await self.ai_module.generate_response(query, AGGRESSION_LEVEL, user_data['score'])
            await self.send_message(chat_id, f"🤖 {response}")
            
        elif text == "/ping":
            await self.send_message(chat_id, "🏓 Понг! Бот работает.")else:
            await self.send_message(chat_id, "❌ Неизвестная команда. /help для списка команд.")
    
    async def generate_response(self, user_message, user_id, user_name):
        """Генерируем ответ"""
        user_data = self.mood_system.user_mood[user_id]
        
        # Используем AI с вероятностью 50%
        use_ai = USE_FREE_AI and random.random() < 0.5
        
        if use_ai:
            try:
                ai_response = await self.ai_module.generate_response(
                    user_message, AGGRESSION_LEVEL, user_data['score']
                )
                if ai_response:
                    return ai_response
            except:
                pass
        
        # Стандартный ответ
        if user_data['score'] >= 70:
            response = random.choice(POLITE_RESPONSES)
        elif user_data['score'] <= 30:
            response = random.choice(AGGRESSIVE_RESPONSES[:5])
        else:
            response = random.choice(AGGRESSIVE_RESPONSES)
        
        # Персонализация
        if random.random() > 0.5:
            response = response.replace("ты", user_name)
        
        return response
    
    async def run(self):
        """Запускаем бота"""
        print("=" * 60)
        print("🤖 ЗАПУСК TELEGRAM БОТА")
        print("=" * 60)
        print(f"👤 Уникальных пользователей: {len(self.stats['users'])}")
        print(f"📨 Всего сообщений: {self.stats['total_messages']}")
        print("=" * 60)
        print("\n✅ Бот активен! Ожидаю сообщений...")
        
        while True:
            try:
                updates = await self.get_updates()
                
                for update in updates:
                    self.last_update_id = update["update_id"]
                    
                    if "message" in update:
                        await self.process_message(update["message"])
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)

# ========== ЗАПУСК ==========
async def main():
    print("\n" + "=" * 60)
    print("🚀 ИНИЦИАЛИЗАЦИЯ БОТА")
    print("=" * 60)
    
    bot = SimpleTelegramBot(BOT_TOKEN, DEEPSEEK_API_KEY)
    await bot.run()

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 АГРЕССИВНЫЙ TELEGRAM БОТ С DEEPSEEK AI")
    print("=" * 60)
    print("🌐 Веб-сервер: http://localhost:10000")
    print("🔗 Health check: /health")
    print("📱 Telegram: откройте бота и напишите /start")
    print("=" * 60)
    
    # Запускаем асинхронный бот
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        print("Проверьте переменные окружения в Render!")
