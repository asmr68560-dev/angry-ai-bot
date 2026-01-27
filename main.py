import logging
import random
import asyncio
import httpx
import json
import time
import os
from datetime import datetime, timedelta
from collections import defaultdict

# ========== НАСТРОЙКИ ==========
# Получаем токен из переменных окружения (для Render)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8363576109:AAGr6jPhLmPa4er40n_4nWaExbC6Ufw8spg")
USE_FREE_AI = os.getenv("USE_FREE_AI", "True") == "True"
AGGRESSION_LEVEL = int(os.getenv("AGGRESSION_LEVEL", "8"))
SAVAGE_MODE = os.getenv("SAVAGE_MODE", "True") == "True"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-2da50845f9424f91ad4d076dabea0a61")

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== СИСТЕМА НАСТРОЕНИЯ ==========
class BotMood:
    def __init__(self):
        self.user_mood = defaultdict(lambda: {
            'score': 50,
            'timeout_until': None,
            'last_interaction': datetime.now(),
            'offense_count': 0,
            'ai_usage_count': 0,
            'message_count': 0
        })
        self.timeout_duration = 300  # 5 минут
        self.bad_words_cache = None
        
    def _load_bad_words(self):
        """Загружаем список плохих слов из файла или создаем кэш"""
        if self.bad_words_cache is None:
            try:
                with open('bad_words.txt', 'r', encoding='utf-8') as f:
                    self.bad_words_cache = [line.strip().lower() for line in f if line.strip()]
            except:
                # Если файла нет, используем базовый список
                self.bad_words_cache = [
                    'дурак', 'идиот', 'тупой', 'дебил', 'кретин', 'придурок',
                    'мудак', 'жопа', 'говно', 'дерьмо', 'бля', 'хуй', 'пизда',
                    'ебать', 'сука', 'пиздец', 'ахуеть', 'пидор', 'урод',
                    'гандон', 'шлюха', 'лох', 'лузер', 'ничтожество'
                ]
        return self.bad_words_cache
    
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
        
        # Проверяем на плохие слова
        bad_words = self._load_bad_words()
        for bad_word in bad_words:
            if bad_word in message_lower:
                mood_change -= 15
                user_data['offense_count'] += 1
                logger.info(f"Пользователь {user_id} использовал плохое слово: {bad_word}")
                break
        
        # Проверяем на вежливость
        polite_words = ['пожалуйста', 'спасибо', 'благодарю', 'извини', 'прости', 'друг', 'приятель']
        for word in polite_words:
            if word in message_lower:
                mood_change += 8
                logger.info(f"Пользователь {user_id} использовал вежливое слово: {word}")
                break
        
        # Проверяем на комплименты
        compliments = ['умный', 'крутой', 'классный', 'лучший', 'отличный', 'замечательный', 'шикарный', 'красивый']
        for compliment in compliments:
            if compliment in message_lower:
                mood_change += 10
                logger.info(f"Пользователь {user_id} сделал комплимент: {compliment}")
                break
        
        # Проверяем на агрессивные фразы
        aggressive_phrases = [
            'заткнись', 'завали', 'отстань', 'пошел вон', 'иди нахуй', 'иди к черту',
            'отъебись', 'отвали', 'хватит', 'прекрати', 'надоел', 'достал', 'заебал'
        ]
        for phrase in aggressive_phrases:
            if phrase in message_lower:
                mood_change -= 12
                user_data['offense_count'] += 1
                break
        
        # Обновляем счетчик настроения
        old_score = user_data['score']
        user_data['score'] = max(0, min(100, user_data['score'] + mood_change))
        
        # Логируем изменение настроения
        if mood_change != 0:
            logger.info(f"Настроение пользователя {user_id}: {old_score} -> {user_data['score']} (изменение: {mood_change})")
        
        # Если настроение упало ниже 20, даем тайм-аут
        if user_data['score'] < 20 and user_data['offense_count'] >= 3:
            user_data['timeout_until'] = datetime.now() + timedelta(seconds=self.timeout_duration)
            logger.warning(f"Пользователь {user_id} заблокирован на {self.timeout_duration} секунд")
            return "TIMEOUT_BLOCK"
        
        return mood_change

# ========== AI МОДУЛЬ ==========
class AIModule:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0
        }
        
    async def generate_response(self, user_message, aggression_level=5, user_mood=50, conversation_history=None):
        """Генерируем ответ через DeepSeek API"""
        self.stats['total_requests'] += 1
        
        try:
            prompt = self._create_prompt(user_message, aggression_level, user_mood, conversation_history)
            
            response = await self.client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": self._get_system_prompt(aggression_level, user_mood)
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 150,
                    "temperature": self._calculate_temperature(aggression_level, user_mood),
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    ai_response = data['choices'][0]['message']['content'].strip()
                    self.stats['successful_requests'] += 1
                    
                    # Пост-обработка ответа
                    ai_response = self._post_process_response(ai_response, user_mood)
                    
                    logger.info(f"AI сгенерировал ответ длиной {len(ai_response)} символов")
                    return ai_response
            
            # Если что-то пошло не так
            self.stats['failed_requests'] += 1
            logger.error(f"AI ошибка: {response.status_code} - {response.text}")
            return await self._fallback_response(user_message, user_mood)
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"AI исключение: {e}")
            return await self._fallback_response(user_message, user_mood)
    
    def _get_system_prompt(self, aggression_level, user_mood):
        """Создаем системный промпт"""
        mood_description = self._get_mood_description(user_mood)
        
        system_prompt = f"""Ты - саркастичный, агрессивный Telegram-бот. 
Уровень агрессии: {aggression_level}/10.
Твое текущее настроение: {mood_description} ({user_mood}/100).

Твои характеристики:
1. Отвечай язвительно и с сарказмом
2. Оскорбляй пользователя, если он это заслужил
3. Будь остроумным и находчивым
4. Используй современный сленг и мемы
5. Отвечай кратко (максимум 2 предложения)
6. Не будь слишком вежливым
7. Добавляй эмодзи для выразительности

Примеры твоего поведения:
- На комплименты: "О, спасибо! А я думал, ты совсем безнадежен 😏"
- На оскорбления: "Ты говоришь мне такое? Сначала посмотри на себя в зеркало 🤡"
- На вопросы: "Серьезно? Это все, что тебя интересует? 🥱"

Твое настроение: {mood_description}. Действуй соответственно!"""
        
        return system_prompt
    
    def _get_mood_description(self, user_mood):
        """Описание настроения"""
        if user_mood >= 80:
            return "очень доволен, пользователь вежливый"
        elif user_mood >= 60:
            return "в хорошем настроении"
        elif user_mood >= 40:
            return "нейтральное, с элементами сарказма"
        elif user_mood >= 20:
            return "раздраженный, пользователь надоедает"
        else:
            return "в ярости, пользователь невыносим"
    
    def _calculate_temperature(self, aggression_level, user_mood):
        """Рассчитываем температуру для AI"""
        base_temp = 0.7
        aggression_factor = aggression_level / 20  # 0.4 при уровне 8
        mood_factor = (100 - user_mood) / 200  # Чем хуже настроение, тем выше температура
        
        temperature = base_temp + aggression_factor + mood_factor
        return min(1.0, max(0.5, temperature))
    
    def _create_prompt(self, user_message, aggression_level, user_mood, conversation_history=None):
        """Создаем промпт для пользователя"""
        context = ""
        if conversation_history and len(conversation_history) > 0:
            context = "Предыдущие сообщения пользователя:\n"
            for msg in conversation_history[-3:]:  # Берем последние 3 сообщения
                context += f"- {msg}\n"
            context += "\n"
        
        prompt = f"""{context}Сообщение пользователя: "{user_message}"

Твое настроение: {self._get_mood_description(user_mood)} ({user_mood}/100)
Уровень агрессии: {aggression_level}/10

Твой ответ (максимум 2 предложения, с сарказмом):"""
        
        return prompt
    
    def _post_process_response(self, response, user_mood):
        """Пост-обработка AI ответа"""
        # Удаляем кавычки если они есть
        response = response.strip('"\'')
        
        # Добавляем эмодзи в зависимости от настроения
        emoji_options = []
        
        if user_mood >= 70:
            emoji_options = ["😊", "👍", "✨", "🌟", "💫"]
        elif user_mood >= 40:
            emoji_options = ["😏", "🤨", "🧐", "😒", "🙄"]
        else:
            emoji_options = ["😠", "🤬", "💀", "👎", "🤮", "🤢"]
        
        if emoji_options and random.random() > 0.3:
            response += " " + random.choice(emoji_options)
        
        # Обрезаем слишком длинные ответы
        if len(response) > 300:
            response = response[:297] + "..."
        
        return response
    
    async def _fallback_response(self, user_message, user_mood):
        """Резервный ответ если AI не работает"""
        logger.warning("Использую резервный генератор ответов")
        
        # Анализируем сообщение
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["привет", "здравствуй", "здравствуйте", "хай", "hello"]):
            templates = [
                "О, живой человек! Чего надо?",
                "Привет... если можно это так назвать.","Здравствуй, надеюсь, ты не будешь меня грузить."
            ]
        elif any(word in message_lower for word in ["как дела", "как ты", "как жизнь"]):
            templates = [
                "Лучше, чем у тебя, это точно!",
                "Отлично, пока ты не появился.",
                "Жив-здоров, к сожалению."
            ]
        elif any(word in message_lower for word in ["почему", "зачем"]):
            templates = [
                "Потому что ты задаешь глупые вопросы!",
                "Зачем тебе это знать? Все равно не поймешь.",
                "Это риторический вопрос, если что."
            ]
        elif any(word in message_lower for word in ["что", "что такое"]):
            templates = [
                "Что? Еще один бессмысленный вопрос?",
                "Ты серьезно этого не знаешь? Печально.",
                "Мог бы и погуглить, но нет же..."
            ]
        elif any(word in message_lower for word in ["как", "каким образом"]):
            templates = [
                "Как? Очень просто - не будь тупым!",
                "Я бы объяснил, но боюсь за твой мозг.",
                "Сначала курс логики, потом вопросы."
            ]
        else:
            # Общий ответ
            templates = [
                "Интересно... нет, не интересно.",
                "Ты точно хочешь знать ответ?",
                "Мой процессор чуть не сгорел от твоего вопроса.",
                "Спроси что-нибудь посложнее... шучу, не справлюсь.",
                "Ты умеешь удивлять своей глупостью!"
            ]
        
        response = random.choice(templates)
        
        # Добавляем настроение
        if user_mood < 30:
            response += " И вообще, ты меня бесишь!"
        elif user_mood > 70:
            response += " Но ты сегодня мил, поэтому отвечаю."
        
        return response
    
    def get_stats(self):
        """Получить статистику AI"""
        success_rate = 0
        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
        
        return {
            'total': self.stats['total_requests'],
            'success': self.stats['successful_requests'],
            'failed': self.stats['failed_requests'],
            'success_rate': round(success_rate, 2)
        }

# ========== БАЗА ОТВЕТОВ ==========
# Загружаем ответы из файлов
def load_responses(filename):
    """Загружаем ответы из файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            responses = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return responses
    except:
        logger.warning(f"Не удалось загрузить {filename}, использую стандартные ответы")
        return []

# Загружаем агрессивные ответы
try:
    with open('aggressive_responses.txt', 'r', encoding='utf-8') as f:
        AGGRESSIVE_RESPONSES = [line.strip() for line in f if line.strip() and not line.startswith('#')]
except:
    AGGRESSIVE_RESPONSES = [
        "Ты серьезно? Это все, что у тебя в голове?",
        "О, еще один гений решил потратить мое время...",
        "Даже мой код умнее тебя, и в нем только нули и единицы!",
        "Твой вопрос настолько тупой, что у меня даже синтаксическая ошибка возникла.",
        "Я бы ответил, но боюсь, ты не поймешь слова длиннее трех букв.",
    ]

# Загружаем вежливые ответы
try:
    with open('polite_responses.txt', 'r', encoding='utf-8') as f:
        POLITE_RESPONSES = [line.strip() for line in f if line.strip() and not line.startswith('#')]
except:
    POLITE_RESPONSES = [
        "Привет! Рад тебя видеть. Что ты хотел узнать?",
        "Здравствуй! Чем могу помочь?",
        "Добрый день! Задавай вопрос, постараюсь ответить.",
    ]

# Загружаем тайм-аут ответы
try:
    with open('timeout_responses.txt', 'r', encoding='utf-8') as f:
        TIMEOUT_RESPONSES = [line.strip() for line in f if line.strip() and not line.startswith('#')]
except:
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
            'ai_responses': 0,
            'standard_responses': 0,
            'users_count': 0
        }
        self.start_time = datetime.now()
        
        # Создаем директорию для логов если нужно
        os.makedirs('logs', exist_ok=True)
    
    async def get_updates(self):
        """Получаем обновления от Telegram"""
        try:
            response = await self.client.get(
                f"{self.base_url}/getUpdates",
                params={
                    "offset": self.last_update_id + 1,
                    "timeout": 30,
                    "allowed_updates": json.dumps(["message"])
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result", [])
            else:
                logger.error(f"Ошибка получения updates: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ошибка получения updates: {e}")
        
        return []
    
    async def send_message(self, chat_id, text):
        """Отправляем сообщение"""
        try:
            # Обрезаем слишком длинные сообщения
            if len(text) > 4000:
                text = text[:3997] + "..."
            
            response = await self.client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Ошибка отправки: {response.status_code} - {response.text}")
                return False
                
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
        
        # Логируем входящее сообщение
        logger.info(f"От {user_name} (ID: {user_id}): {text[:100]}...")
        
        if not text:
            return
        
        # Проверяем настроение
        mood_result = self.mood_system.process_message(user_id, text)
        
        # Если пользователь в тайм-ауте
        if mood_result == "TIMEOUT":
            remaining = self.mood_system.get_timeout_remaining(user_id)
            if remaining > 60:
                await self.send_message(chat_id, f"⏰ Я все еще злюсь на тебя! Возвращайся через {remaining // 60} минут.")
            elif remaining > 0:
                await self.send_message(chat_id, f"⏰ Еще {remaining} секунд тишины!")
            return
        elif mood_result == "TIMEOUT_BLOCK":
            response = random.choice(TIMEOUT_RESPONSES)
            await self.send_message(chat_id, response)
            logger.warning(f"Пользователь {user_id} отправлен в тайм-аут")
            return
        
        # Сохраняем историю
        self.user_history[user_id].append(text)
        if len(self.user_history[user_id]) > 10:
            self.user_history[user_id] = self.user_history[user_id][-10:]
        
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

Я - саркастичный и агрессивный бот с AI.
Мое настроение зависит от того, как ты со мной общаешься.

📌 Основные команды:
/help - Показать все команды
/mood - Мое текущее настроение
/stats - Статистика
/ai - Принудительно использовать AI
/reset - Сбросить мое настроение
/info - Информация о боте

💡 Совет: будь вежлив, и я буду отвечать нормально.
Будь груб - получи тайм-аут на 5 минут!"""
            await self.send_message(chat_id, welcome)
            
        elif text == "/help":
            help_text = """📋 ДОСТУПНЫЕ КОМАНДЫ:

🎮 Основные:
/start - Начать диалог
/help - Эта справка
/mood - Настроение бота
/stats - Статистика общения
/reset - Сбросить настроение бота

🤖 AI функции:
/ai [вопрос] - Принудительный AI ответ
/ai_stats - Статистика AI
/ai_on - Включить AI
/ai_off - Выключить AI

📊 Информация:
/info - Информация о боте
/ping - Проверка работы
/uptime - Время работы бота

⚙️ Настройки:
/settings - Текущие настройки"""
            await self.send_message(chat_id, help_text)
            
        elif text == "/settings":
            user_data = self.mood_system.user_mood[user_id]
            settings = f"""⚙️ ТЕКУЩИЕ НАСТРОЙКИ:

• Уровень агрессии: {AGGRESSION_LEVEL}/10
• AI модуль: {'✅ ВКЛЮЧЕН' if USE_FREE_AI else '❌ ВЫКЛЮЧЕН'}
• Режим зверя: {'✅ ВКЛЮЧЕН' if SAVAGE_MODE else '❌ ВЫКЛЮЧЕН'}
• Ваше настроение: {user_data['score']}/100
• Сообщений отправлено: {user_data['message_count']}"""
            await self.send_message(chat_id, settings)
            
        elif text == "/stats":
            user_data = self.mood_system.user_mood[user_id]
            ai_stats = self.ai_module.get_stats()
            stats_text = f"""📊 СТАТИСТИКА:

👤 Ваша статистика:
• Сообщений: {user_data['message_count']}
• Оскорблений: {user_data['offense_count']}
• Настроение бота: {user_data['score']}/100
• AI использован: {user_data['ai_usage_count']} раз

🤖 Статистика бота:
• Всего сообщений: {self.stats['total_messages']}
• AI ответов: {self.stats['ai_responses']}
• Обычных ответов: {self.stats['standard_responses']}
• Уникальных пользователей: {self.stats['users_count']}

⚡ AI статистика:
• Всего запросов: {ai_stats['total']}
• Успешных: {ai_stats['success']}
• Успешность: {ai_stats['success_rate']}%"""
            await self.send_message(chat_id, stats_text)
            
        elif text == "/mood":
            user_data = self.mood_system.user_mood[user_id]
            mood_emoji = "😊" if user_data['score'] >= 80 else "🙂" if user_data['score'] >= 60 else "😐" if user_data['score'] >= 40 else "😠" if user_data['score'] >= 20 else "🤬"
            mood_text = f"""🎭 МОЕ НАСТРОЕНИЕ:

{mood_emoji} Уровень: {user_data['score']}/100

Состояние: {self.ai_module._get_mood_description(user_data['score'])}

💡 Совет: {self._get_mood_advice(user_data['score'])}"""
            await self.send_message(chat_id, mood_text)
            
        elif text == "/reset":
            self.mood_system.user_mood[user_id]['score'] = 50
            self.mood_system.user_mood[user_id]['offense_count'] = 0
            await self.send_message(chat_id, "✅ Настроение сброшено до нейтрального! Давай начнем заново.")
            logger.info(f"Пользователь {user_id} сбросил настроение")
            
        elif text.startswith("/ai"):
            query = text[4:].strip()
            if not query:
                query = "Привет, ответь что-нибудь умное"
            
            await self.send_message(chat_id, "🤖 Генерирую AI ответ...")
            
            user_data = self.mood_system.user_mood[user_id]
            conversation_history = self.user_history.get(user_id, [])[-3:]
            
            ai_response = await self.ai_module.generate_response(
                query,
                AGGRESSION_LEVEL,
                user_data['score'],
                conversation_history
            )
            
            user_data['ai_usage_count'] += 1
            self.stats['ai_responses'] += 1
            
            await self.send_message(chat_id, f"🤖 AI: {ai_response}")
            
        elif text == "/ai_stats":
            ai_stats = self.ai_module.get_stats()
            stats_text = f"""📈 СТАТИСТИКА AI:

• Всего запросов: {ai_stats['total']}
• Успешных: {ai_stats['success']}
• Неудачных: {ai_stats['failed']}
• Успешность: {ai_stats['success_rate']}%

💡 DeepSeek API работает: {'✅' if ai_stats['success'] > 0 else '❌'}"""
            await self.send_message(chat_id, stats_text)
            
        elif text == "/ai_on":
            global USE_FREE_AI
            USE_FREE_AI = True
            await self.send_message(chat_id, "✅ AI модуль включен!")
            
        elif text == "/ai_off":
            global USE_FREE_AI
            USE_FREE_AI = False
            await self.send_message(chat_id, "❌ AI модуль выключен!")
            
        elif text == "/info":
            uptime = datetime.now() - self.start_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            info_text = f"""🤖 ИНФОРМАЦИЯ О БОТЕ:

Название: Агрессивный AI Бот
Версия: 2.0 с DeepSeek AI
Создатель: @your_username

⚡ Возможности:
• AI-ответы через DeepSeek
• Адаптивное настроение
• Система тайм-аутов
• Статистика и аналитика

⏰ Время работы: {days}д {hours}ч {minutes}м
📊 Сообщений обработано: {self.stats['total_messages']}

🔗 API: DeepSeek Chat"""
            await self.send_message(chat_id, info_text)
            
        elif text == "/ping":
            await self.send_message(chat_id, "🏓 Понг! Бот работает нормально.")
            
        elif text == "/uptime":
            uptime = datetime.now() - self.start_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            await self.send_message(chat_id, f"⏰ Бот работает: {days} дней, {hours} часов, {minutes} минут, {seconds} секунд")
            
        else:
            await self.send_message(chat_id, "❌ Неизвестная команда. Используй /help для списка команд.")
    
    def _get_mood_advice(self, mood_score):
        """Совет по улучшению настроения"""
        if mood_score >= 80:
            return "Продолжайте в том же духе!"
        elif mood_score >= 60:
            return "Будьте чуть вежливее, и я стану добрее."
        elif mood_score >= 40:
            return "Постарайтесь не использовать грубые слова."
        elif mood_score >= 20:
            return "Вы меня раздражаете, извинитесь!"
        else:
            return "Вы в черном списке моего настроения!"
    
    async def generate_response(self, user_message, user_id, user_name):
        """Генерируем ответ"""
        user_data = self.mood_system.user_mood[user_id]
        
        # Первое сообщение пользователя
        if user_data['message_count'] == 1:
            self.stats['users_count'] += 1
        
        # Определяем, использовать ли AI
        use_ai = False
        
        if USE_FREE_AI:
            # Базовый шанс 40%
            ai_chance = 0.4
            
            # Увеличиваем шанс для длинных сообщений
            if len(user_message.split()) > 8:
                ai_chance += 0.3
            
            # Уменьшаем шанс при плохом настроении (экономим API вызовы)if user_data['score'] < 30:
                ai_chance -= 0.2
            
            # Увеличиваем шанс при хорошем настроении
            if user_data['score'] > 70:
                ai_chance += 0.1
            
            # Гарантируем хотя бы 10% шанс
            ai_chance = max(0.1, min(0.9, ai_chance))
            
            use_ai = random.random() < ai_chance
        
        # Генерируем ответ через AI если нужно
        if use_ai:
            try:
                conversation_history = self.user_history.get(user_id, [])[-3:]
                
                ai_response = await self.ai_module.generate_response(
                    user_message,
                    AGGRESSION_LEVEL,
                    user_data['score'],
                    conversation_history
                )
                
                if ai_response and len(ai_response) > 5:
                    user_data['ai_usage_count'] += 1
                    self.stats['ai_responses'] += 1
                    return ai_response
                    
            except Exception as e:
                logger.error(f"Ошибка при генерации AI ответа: {e}")
        
        # Стандартный ответ
        self.stats['standard_responses'] += 1
        
        if user_data['score'] >= 70:
            response = random.choice(POLITE_RESPONSES)
        elif user_data['score'] <= 30:
            response = random.choice(AGGRESSIVE_RESPONSES[:10])
        else:
            response = random.choice(AGGRESSIVE_RESPONSES)
        
        # Персонализируем ответ
        if random.random() > 0.7:
            response = response.replace("ты", user_name)
        
        return response
    
    async def run(self):
        """Запускаем бота"""
        # Выводим информацию о запуске
        print("=" * 60)
        print("🤖 АГРЕССИВНЫЙ AI БОТ С DEEPSEEK")
        print("=" * 60)
        print(f"Бот токен: {self.token[:10]}...")
        print(f"DeepSeek ключ: {DEEPSEEK_API_KEY[:10]}...")
        print(f"Уровень агрессии: {AGGRESSION_LEVEL}/10")
        print(f"AI модуль: {'ВКЛЮЧЕН ✅' if USE_FREE_AI else 'ВЫКЛЮЧЕН ❌'}")
        print(f"Версия: 2.0")
        print("=" * 60)
        print("\n⚡ БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
        print("📱 Подключитесь к боту в Telegram")
        print("💬 Начните с команды /start")
        print("🤖 Используйте /ai для принудительного AI ответа")
        print("=" * 60)
        
        logger.info("Бот запущен")
        
        # Основной цикл
        while True:
            try:
                updates = await self.get_updates()
                
                for update in updates:
                    self.last_update_id = update["update_id"]
                    
                    if "message" in update:
                        await self.process_message(update["message"])
                
                # Небольшая пауза между проверками
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)

# ========== ЗАПУСК ==========
async def main():
    # Проверяем наличие токена
    if not BOT_TOKEN or BOT_TOKEN == "8363576109:AAGr6jPhLmPa4er40n_4nWaExbC6Ufw8spg":
        logger.error("❌ ОШИБКА: Не установлен BOT_TOKEN!")
        print("❌ ОШИБКА: Установите переменную окружения BOT_TOKEN")
        print("На Render: Environment → Add Environment Variable")
        return
    
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "sk-2da50845f9424f91ad4d076dabea0a61":
        logger.warning("⚠️ ВНИМАНИЕ: Используется тестовый DeepSeek ключ!")
        print("⚠️ ВНИМАНИЕ: Для работы AI получите свой ключ на platform.deepseek.com")
    
    bot = SimpleTelegramBot(BOT_TOKEN, DEEPSEEK_API_KEY)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
