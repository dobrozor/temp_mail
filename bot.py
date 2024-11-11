import telebot
import requests
import json
import time
import html
from telebot import types

TOKEN = '7781476624:AAEWnVMNlxye2j9leILfmEcKOo3oQI2vWfM' #сюда токен
bot = telebot.TeleBot(TOKEN)

user_emails = {}
user_last_message_id = {}


def get_temp_email():
    response = requests.get('https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1')
    if response.status_code == 200:
        return json.loads(response.text)[0]
    return None


def check_email_inbox(email):
    login, domain = email.split('@')
    response = requests.get(f'https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}')
    if response.status_code == 200:
        return json.loads(response.text)
    return []


def get_message_content(email, message_id):
    login, domain = email.split('@')
    response = requests.get(
        f'https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={message_id}')
    if response.status_code == 200:
        return json.loads(response.text)
    return None


@bot.message_handler(commands=['start'])
def start_message(message):
    welcome_text = (
        "🙋 *Добро пожаловать!*\n\n❓ Это бот для временных почт"
    )

    email = get_temp_email()
    if email:
        user_emails[message.chat.id] = email
        user_last_message_id[message.chat.id] = None

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("✉️Сменить почту✉️"), types.KeyboardButton("❓Информация❓"))

        bot.send_message(message.chat.id, welcome_text, parse_mode='markdown', reply_markup=markup)
        bot.send_message(message.chat.id, f"⚠️ *Ваша временная почта:* `{email}`", parse_mode='markdown')
    else:
        bot.send_message(message.chat.id, "⚠️ *Ошибка при получении почты*", parse_mode='markdown')


@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    if message.text == "✉️Сменить почту✉️":
        new_email = get_temp_email()
        if new_email:
            user_emails[message.chat.id] = new_email
            user_last_message_id[message.chat.id] = None
            bot.send_message(message.chat.id, f"⚠️ *Ваша новая временная почта:* `{new_email}`",
                             parse_mode='markdown')
        else:
            bot.send_message(message.chat.id, "⚠️ *Ошибка при смене почты*", parse_mode='markdown')
    elif message.text == "❓Информация❓":
        bot.send_message(message.chat.id,
                         "Это бот для временных почт, используй его сколько хочешь и как хочешь. "
                         "Можно получить письмо от любых сервисов\n\n"
                         "Если что, сделал @dobrozor")


def check_for_new_emails():
    while True:
        for chat_id, email in user_emails.items():
            messages = check_email_inbox(email)
            if messages:
                last_message = messages[0]
                last_message_id = last_message['id']

                if user_last_message_id.get(chat_id) != last_message_id:
                    user_last_message_id[chat_id] = last_message_id
                    message_content = get_message_content(email, last_message_id)

                    email_from = html.escape(message_content['from'])
                    email_body = html.escape(message_content['textBody'])

                    notification = (
                        f"💬 От: __{email_from}__ \n"
                        f"{email_body}"
                    )

                    bot.send_message(chat_id, notification, parse_mode='markdown')

        time.sleep(5) # Проверка почты (минимум 5 сек)

import threading
email_check_thread = threading.Thread(target=check_for_new_emails)
email_check_thread.start()

bot.polling(none_stop=True)
