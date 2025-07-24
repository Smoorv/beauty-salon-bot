import telebot
from telebot import types
import sqlite3
import logging

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Токен бота должен быть в файле .env
token = os.getenv('YOUR_TOKEN_HERE')
bot = telebot.TeleBot("YOUR_TOKEN_HERE")

#Для демо версии временная БД
conn = sqlite3.connect(':memory:', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS requests
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT,
                   phone TEXT)''')

#Главное меню
def get_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("Прайс"),
        types.KeyboardButton("Контакты"),
        types.KeyboardButton("Оставить заявку")
    ]
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 
                    "Добро пожаловать в демо-бот салона красоты!",
                    reply_markup=get_keyboard())

#Прайс лист
@bot.message_handler(func=lambda msg: msg.text == "Прайс")
def show_price(message):

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Волосы", callback_data="hair"),
        types.InlineKeyboardButton("Ногти", callback_data="nails")
    )
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)

#Начало оформление заявки
@bot.message_handler(func=lambda msg: msg.text == "Оставить заявку")
def request(message):
    msg = bot.send_message(message.chat.id, "Введите ваше имя:")
    bot.register_next_step_handler(msg, process_name)
    
#Обработка имени пользователя
def process_name(message):
    name = message.text
    if len(name) < 2:
        bot.send_message(message.chat.id, "Имя слишком короткое")
        return
    msg = bot.send_message(message.chat.id, "Введите телефон (формат: +79991234567):")
    bot.register_next_step_handler(msg, process_phone, name)

#Обработка номера телефона и сохранение заявки
def process_phone(message, name):
    phone = message.text
    if not phone.startswith("+7") or len(phone) != 12:
        bot.send_message(message.chat.id, "Неверный формат телефона")
        return
    
    try:
        cursor.execute("INSERT INTO requests (name, phone) VALUES (?, ?)", (name, phone))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Заявка принята! Пример сохранения в БД:")
        
        # Демонстрация работы с БД (для портфолио)
        cursor.execute("SELECT * FROM requests")
        last_request = cursor.fetchone()
        bot.send_message(message.chat.id, 
                        f"Последняя запись в БД:\nИмя: {last_request[1]}\nТелефон: {last_request[2]}")
    except Exception as e:
        logger.error(f"Database error: {e}")
        bot.send_message(message.chat.id, "⚠️ Ошибка сохранения")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    """Обработчик inline-кнопок"""
    if call.data == "hair":
        bot.send_message(call.message.chat.id, "💇 Услуги для волос:\n- Стрижка: 1500р\n- Окрашивание: 2500р")
    elif call.data == "nails":
        bot.send_message(call.message.chat.id, "💅 Маникюр:\n- Классический: 1000р\n- Дизайн: +300р")

if __name__ == "__main__":
    logger.info("Бот запущен (демо-версия для портфолио)")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        conn.close()
