import telebot
import config
import sqlite3
import re
from telebot import types

#clients = [1269424044]
bot = telebot.TeleBot(config.token)
admins = []
GROUP_CV_ID = -4695163369
GROUP_ID = -1002663440792
CHANNEL_USERNAME = "@lilalylove"

conn = sqlite3.connect("users.db", check_same_thread= False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(id INT);")
cur.execute('''
CREATE TABLE IF NOT EXISTS feedbacks (
    user_id INTEGER PRIMARY KEY,
    feedback TEXT,
    is_sent INTEGER DEFAULT 0
)
''')
conn.commit()

link = ""
text = ""

def is_user_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'creator', 'administrator']
    except Exception as e:
        print(f'Ошибка проверки подписки: {e}')
        return False

@bot.message_handler(commands=['help', 'start'])
def start(message):
    global admins
    user_id = message.from_user.id
    if is_user_subscribed(user_id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("\U0001F4C4 Проверить мое резюме", "\U0001F4EC Посмотреть фидбэк")
        bot.send_message(user_id, "Добро пожаловать! 🎉 Вы подписаны на канал и можете пользоваться ботом.", reply_markup=markup)
        # Тут можно показать кнопки или команды
        help_user(message)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")
        markup.add(btn)
        bot.send_message(user_id, "😕 Для использования бота нужно подписаться на канал.", reply_markup=markup)
    if message.chat.id in admins:
        help(message)
    try:
        # clients.append(message.chat.id)
        id = message.chat.id
        info = cur.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchall()
        if not info:
            cur.execute(f"INSERT INTO users (id) VALUES ({id})")
            conn.commit()
            bot.send_message(message.chat.id, "Теперь вы  можете получать рассылку!")
        else:
            pass
    except:
        pass
def help_user(message):
    user_markup = types.ReplyKeyboardMarkup()
    user_markup .add(types.KeyboardButton(text="Изменить текст"))
    user_markup .add(types.KeyboardButton(text="Изменить ссылку"))
    user_markup .add(types.KeyboardButton(text="Показать сообщение"))
    user_markup .add(types.KeyboardButton(text="Начать рассылку"))
    user_markup.add(types.KeyboardButton(text="Меню"))
    bot.send_message(message.chat.id,
                     "Команды бота:\n\
/start - начать использовать/перезапустить бота\n\
/menu - показать все команды \n\
Все команды также доступны в меню.\n",
                     reply_markup=admin_markup)
def help(message):
    admin_markup = types.ReplyKeyboardMarkup()
    admin_markup.add(types.KeyboardButton(text = "Изменить текст"))
    admin_markup.add(types.KeyboardButton(text="Изменить ссылку"))
    admin_markup.add(types.KeyboardButton(text="Показать сообщение"))
    admin_markup.add(types.KeyboardButton(text="Начать рассылку"))
    admin_markup.add(types.KeyboardButton(text="Помощь"))
    bot.send_message(message.chat.id,
                     "Команды бота:\n\
/edit_message - редактирование текста рассылки\n\
/edit_link - изменение ссылки, прикрепленной к тексту рассылки\n\
/show - показать сообщение для отправления\n\
/send - запуск рассылки \n\
/help - показать все команды \n\
Все команды также доступны в меню.\n",
                     reply_markup=admin_markup)

@bot.message_handler(func=lambda m: m.text == "\U0001F4C4 Проверить мое резюме")
def ask_resume(message):
    bot.send_message(message.chat.id, "Пожалуйста, отправь файл с резюме (PDF, DOC и т.п.).")


@bot.message_handler(content_types=['document'])
def handle_resume(message):
    user = message.from_user
    caption = f"\U0001F4C4 Резюме от @{user.username or user.first_name} (ID: {user.id})"
    try:
        bot.send_document(GROUP_CV_ID, message.document.file_id, caption=caption)
        bot.send_message(message.chat.id, "Спасибо! Резюме отправлено экспертам. Ожидай фидбэк.")
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка при отправке. Попробуй позже.")
        print("Ошибка:", e)


@bot.message_handler(func=lambda m: m.chat.id == GROUP_CV_ID and m.reply_to_message is not None)
def handle_expert_reply(message):
    original = message.reply_to_message
    match = re.search(r"ID: (\d+)", original.caption or original.text or "")
    if match:
        user_id = int(match.group(1))
        feedback_text = message.text
        cur.execute("REPLACE INTO feedbacks (user_id, feedback, is_sent) VALUES (?, ?, ?)", (user_id, feedback_text, 0))
        conn.commit()
        try:
            bot.send_message(user_id, f"\U0001F4DD Твой фидбэк готов:\n\n{feedback_text}")
            cur.execute("UPDATE feedbacks SET is_sent = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
        except Exception as e:
            print("Ошибка отправки фидбэка:", e)
    else:
        bot.send_message(GROUP_CV_ID, "Не удалось определить пользователя для фидбэка.")


@bot.message_handler(func=lambda m: m.text == "\U0001F4EC Посмотреть фидбэк")
def show_feedback(message):
    user_id = message.from_user.id
    cur.execute("SELECT feedback FROM feedbacks WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    if result:
        bot.send_message(user_id, f"\U0001F4AC Вот твой фидбэк от эксперта:\n\n{result[0]}")
    else:
        bot.send_message(user_id, "\u23F3 Пока нет фидбэка. Он появится, как только эксперт его отправит.")


@bot.message_handler(commands=['get_id'])
def get_id(message):
    bot.send_message(message.chat.id, "Ваше id:" + str(message.chat.id))

@bot.message_handler(commands=['test'])
def test_command(message):
    bot.send_message(message.chat.id, "Я вижу вашу команду!")

@bot.message_handler(commands= ["edit_message"])
def edit_message(message):
    if message.chat.id in admins:
        m = bot.send_message(message.chat.id, "Введите текст рассылки:")
        bot.register_next_step_handler(m, add_text)
def add_text(message):
    global text
    text = message.text
    if text not in ["Изменить текст", "Изменить ссылку", "Показать сообщение", "Начать рассылку", "Помощь"]:
        bot.send_message(message.chat.id, "Сохраненный текст: ")
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "Ошибка!")
@bot.message_handler(commands= ["edit_link"])
def edit_link(message):
    if message.chat.id in admins:
        m = bot.send_message(message.chat.id, "Введите нужную ссылку:")
        bot.register_next_step_handler(m, add_link)

def add_link(message):
    global link
    if message.text is not None:
        link=message.text
        bot.send_message(message.chat.id, "Сохраненная ссылка: ")
        bot.send_message(message.chat.id, link)
    else:
        bot.send_message(message.chat.id, "Неверная ссылка! ")
        m = bot.send_message(message.chat.id, "Введите нужную ссылку:")
        bot.register_next_step_handler(m, add_link)

# @bot.message_handler(commands= ["send"])
# def send_message(message):
#     global text
#     global link
#     if text != "":
#         if link != "":
#             for i in clients:
#                 sending(i)
#             else:
#                 text = ""
#                 link =""
#         else:
#             bot.send_message(message.chat.id, "Отсутствует ссылка!")
#     else:
#         bot.send_message(message.chat.id, "Отсутствует текст!")
#
# def sending(client_id):
#     global link
#     try:
#        markup_keyboard =types.InlineKeyboardMarkup()
#        link_button = types.InlineKeyboardButton(text= "Ссылка на сайт", url = link)
#        markup_keyboard.add(link_button)
#        bot.send_message(client_id, text, reply_markup=markup_keyboard)
#     except:
#         pass

@bot.message_handler(commands=["send"])
def send_message(message):
    if message.chat.id in admins:
        global link
        global text
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Начать рассылку", callback_data = "go"))
        markup.add(types.InlineKeyboardButton(text="Отмена", callback_data="cancel"))
        if text and link:
            bot.send_message(message.chat.id, "Подтвердите начало рассылки", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Отсутствует текст рассылки или ссылка")

def send():
    global text
    global link
    if text and link:
        inline_keyboard = types.InlineKeyboardMarkup()
        inline_keyboard.add(types.InlineKeyboardButton(text="Перейти", url=link))
        cur.execute("SELECT id FROM users")
        massive = cur.fetchall()
        for i in massive:
            id = i[0]
            try:
                bot.send_message(id, text, reply_markup=inline_keyboard)
            except:
                pass
        else:
            pass

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "go":
        send()
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = "Рассылка началась", reply_markup=None)
    elif call.data == "cancel":
        bot.answer_callback_query(call.id, show_alert=True, text = "Рассылка отменена")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id= call.message.message_id, text = "Рассылка отменена. \nТекст и ссылка сохранены.", reply_markup=None)

@bot.message_handler(content_types=["text"])
def info(message):
    if message.chat.id == GROUP_ID:
        if message.text.lower() == "привет":
            user_id = message.from_user.id
            if is_user_subscribed(user_id):
                bot.send_message(user_id, "🎁 Вот ваш секретный контент!")
            else:
                bot.send_message(user_id, "❌ Вы не подписаны. Подпишитесь на канал, чтобы получить доступ.")
    if message.chat.id in admins:
        if message.text =="Изменить текст":
            m= bot.send_message(message.chat.id, "Введите текст рассылки")
            bot.register_next_step_handler(m, add_text)
        elif message.text == "Изменить ссылку":
            m = bot.send_message(message.chat.id, "Введите ссылку рассылки")
            bot.register_next_step_handler(m, add_link)
        elif message.text == "Показать сообщение":
            show(message)
        elif message.text == "Начать рассылку":
            global link
            global text
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text="Начать рассылку", callback_data="go"))
            markup.add(types.InlineKeyboardButton(text="Отмена", callback_data="cancel"))
            if text and link:
                bot.send_message(message.chat.id, "Подтвердите начало рассылки", reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "Отсутствует текст рассылки или ссылка")
        elif message.text == "Помощь":
            help(message)
        else:
            help(message)



def is_valid_url(url):
    return re.match(r'^https?:\/\/', url) is not None

@bot.message_handler(commands= ["show"])
def show_message(message):
    if message.chat.id in admins:
        bot.register_next_step_handler(message, show)

def show(message):
    global text
    global link
    if not is_valid_url(link):
        bot.send_message(message.chat.id, "⚠️ Некорректная ссылка. Введите ссылку заново.")
        return
    markup=types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Перейти", url=link))
    bot.send_message(message.chat.id, "Ваша рассылка будет выглядеть вот так)")
    bot.send_message(message.chat.id, text, reply_markup=markup)


bot.infinity_polling(skip_pending=True)



