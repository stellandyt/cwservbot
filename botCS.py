import telebot
from telebot import types
import requests
from telebot import apihelper
import time


token = '918573896:AAEM0r2hDXAJoCwy5WtTFZJ92iEmhxmoVeM'
bot = telebot.TeleBot(token)

apihelper.proxy = {"https": "socks5://163.172.81.30:443"}


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привет! Ты зашёл в нашу игру!', reply_markup=keyboard())


def get_id(message):
    text = message.text
    serv = 'http://api.warface.ru/user/stat/?name=%s&server=1' % text
    print(serv)
    r = requests.get(serv)
    t = str(r)
    data = r.json()
    if t == '<Response [400]>':
        serv = 'http://api.warface.ru/user/stat/?name=%s&server=2' % text
        print(serv)
        r = requests.get(serv)
        t = str(r)
        if t == '<Response [400]>':
            serv = 'http://api.warface.ru/user/stat/?name=%s&server=3' % text
            print(serv)
            r = requests.get(serv)
            t = str(r)
            if t == '<Response [200]>':
                data = r.json()
                print(data)
                nick = data['nickname']
                rank = data['rank_id']
                exp = data['experience']
                try:
                    clan = data['clan_name']
                    bot.send_message(message.chat.id,
                                     'Ник: ' + str(nick) + '\n' + 'Сервер: Чарли' + '\n' + 'Ранг: ' + str(
                                         rank) + '\n' + 'Exp: ' + str(exp) + '\n' + 'Клан: ' + str(clan),
                                     reply_markup=keyboard())
                except KeyError:
                    bot.send_message(message.chat.id,
                                     'Ник: ' + str(nick) + '\n' + 'Сервер: Чарли' + '\n' + 'Ранг: ' + str(
                                         rank) + '\n' + 'Exp: ' + str(exp) + '\n' + 'Клан: No',
                                     reply_markup=keyboard())
            else:
                bot.send_message(message.chat.id, 'Игрок скрыл свою статистику или данный Ник не найден.', reply_markup=keyboard())
                print('error')

        elif t == '<Response [200]>':
            data = r.json()
            print(data)
            nick = data['nickname']
            rank = data['rank_id']
            exp = data['experience']
            try:
                clan = data['clan_name']
                bot.send_message(message.chat.id,
                                 'Ник: ' + str(nick) + '\n' + 'Сервер: Браво' + '\n' + 'Ранг: ' + str(
                                     rank) + '\n' + 'Exp: ' + str(exp) + '\n' + 'Клан: ' + str(clan),
                                 reply_markup=keyboard())
            except KeyError:
                bot.send_message(message.chat.id,
                                 'Ник: ' + str(nick) + '\n' + 'Сервер: Браво' + '\n' + 'Ранг: ' + str(
                                     rank) + '\n' + 'Exp: ' + str(exp) + '\n' + 'Клан: No',
                                 reply_markup=keyboard())

    elif t == '<Response [200]>':
        data = r.json()
        print(data)
        nick = data['nickname']
        rank = data['rank_id']
        exp = data['experience']
        try:
            clan = data['clan_name']
            bot.send_message(message.chat.id,
                            'Ник: ' + str(nick) + '\n' + 'Сервер: Альфа' + '\n' + 'Ранг: ' + str(
                                rank) + '\n' + 'Exp: ' + str(exp) + '\n' + 'Клан: ' + str(clan),
                            reply_markup=keyboard())
        except KeyError:
            bot.send_message(message.chat.id,
                             'Ник: ' + str(nick) + '\n' + 'Сервер: Альфа' + '\n' + 'Ранг: ' + str(
                                 rank) + '\n' + 'Exp: ' + str(exp) + '\n' + 'Клан: No',
                             reply_markup=keyboard())


@bot.message_handler(content_types=['text'])
def get_text_message(message):
    global gg, check
    text = message.text
    if text == 'Привет' or text == 'привет':
        bot.send_message(message.chat.id, 'Хааааай', reply_markup=keyboard())
    elif text == 'Данные игрока':
        sent = bot.send_message(message.chat.id, 'Введите ник игрока.')
        bot.register_next_step_handler(sent, get_id)
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю!', reply_markup=keyboard())


def keyboard():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn_1 = types.KeyboardButton('Help')
    btn_8 = types.KeyboardButton('Данные игрока')
    markup.add(btn_1, btn_8)
    return markup

while True:
    try:
        bot.polling(none_stop=True, timeout=123, interval=0)
    except Exception as E:
        print(E.args)
        time.sleep(2)
