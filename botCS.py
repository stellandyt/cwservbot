import telebot
import pymysql
# from telebot import types
import requests
from flask import Flask, request
import os

bot = telebot.TeleBot("824295335:AAGK4j81vjcKoRsNd_1mWOwMPafNRfhWqhY")
server = Flask(__name__)
asd = False


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global asd
    if message.text == '/start':
        conn = pymysql.connect('91.134.194.237', 'gs9966', 'STelland3102YT', 'gs9966')
        cursor = conn.cursor()
        name = message.from_user.id
        print(name)
        query = "SELECT api_key from users WHERE user_id=%s "
        args = (str(name))
        cursor.execute(query, args)
        row = cursor.fetchone()
        print(row)
        conn.close()
        if row != None:
            api_key = str(row[0])
            servstop = "https://cw-serv.ru/api/key/%s/action/start" % api_key
            print(servstop)
            print(api_key)
            requests.post(servstop)
            # markup = types.InlineKeyboardMarkup()
            # btn_my_site = types.InlineKeyboardButton(text='Наш сайт', url=api_key)
            # markup.add(btn_my_site)
            # bot.send_message(message.chat.id, "Нажми на кнопку и перейди на наш сайт.", reply_markup=markup)
        elif asd == False:
            bot.send_message(message.from_user.id, "Введите api key: ")
            asd = True
            print(asd)
    elif message.text == '/stop':
        conn = pymysql.connect('91.134.194.237', 'gs9966', 'STelland3102YT', 'gs9966')
        cursor = conn.cursor()
        name = message.from_user.id
        print(name)
        query = "SELECT api_key from users WHERE user_id=%s "
        args = (str(name))
        cursor.execute(query, args)
        row = cursor.fetchone()
        print(row)
        conn.close()
        if row != None:
            api_key = str(row[0])
            servstop = "https://cw-serv.ru/api/key/%s/action/stop" % api_key
            print(servstop)
            print(api_key)
            requests.post(servstop)

    elif message.text == '/status':
        conn = pymysql.connect('91.134.194.237', 'gs9966', 'STelland3102YT', 'gs9966')
        cursor = conn.cursor()
        name = message.from_user.id
        print(name)
        query = "SELECT api_key from users WHERE user_id=%s "
        args = (str(name))
        cursor.execute(query, args)
        row = cursor.fetchone()
        print(row)
        conn.close()
        if row != None:
            api_key = str(row[0])
            servstat = "https://cw-serv.ru/api/key/%s/action/data" % api_key
            print(servstat)
            print(api_key)
            r = requests.get(servstat)
            ntext = str(r.json())
            newtext = ntext.replace(',', '\n')
            print(newtext)
            bot.send_message(message.from_user.id, newtext)
    elif asd == True:
        conn = pymysql.connect('91.134.194.237', 'gs9966', 'STelland3102YT', 'gs9966')
        cursor = conn.cursor()
        name = message.from_user.id
        print(name)
        query = "INSERT INTO `users` (`user_id`, `api_key`) VALUES (%s, %s) "
        args = (str(name), str(message.text))
        print(args)
        cursor.execute(query, args)
        conn.commit()
        conn.close()
        print(message.text)
        asd = False
        print(asd)


@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://quiet-crag-65971.herokuapp.com/')
    return "!", 200


if __name__ == "__name__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))


bot.polling(none_stop=True, interval=0)