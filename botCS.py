import telebot
from telebot import types
import sqlite3
# import schedule
import time
import requests

token = '918573896:AAEM0r2hDXAJoCwy5WtTFZJ92iEmhxmoVeM'
bot = telebot.TeleBot(token)

conn = sqlite3.connect('game.db', check_same_thread=False)
cursor = conn.cursor()

try:
    cursor.execute('''CREATE TABLE game 
                    (User_ID integer, Score integer, business text, pin integer)
                    ''')
except sqlite3.OperationalError:
    pass


score = 1000
check = False
gg = False
gg_2 = True
game = False


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привет! Ты зашёл в нашу игру!', reply_markup=keyboard())


@bot.message_handler(commands=["Login"])
def auto_log(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=True, resize_keyboard=True)
    btn_1 = types.KeyboardButton(text="Регистрация/Авторизация", request_contact=True)
    btn_2 = types.KeyboardButton(text='/home')
    keyboard.add(btn_1)
    keyboard.add(btn_2)
    bot.send_message(message.chat.id, "Привет! Нажми на кнопку, чтобы пройти Регистрацию/Авторизацию.", reply_markup=keyboard)


@bot.message_handler(content_types=["contact"])
def contact(message):
    global check, score
    if message.contact is not None:
        contact_one = message.contact
        us_id = "%s" % contact_one.user_id

        args = int(us_id)
        cursor.execute(""" SELECT User_ID FROM game WHERE User_ID = ? """, [args])
        row = cursor.fetchone()

        if row == None:
            cursor.execute('insert into game (User_id, Score, pin) values (?, ?, 0)', (us_id, score))
            print(cursor.execute('select * from game').fetchall())
            conn.commit()
            bot.send_message(message.chat.id, "Вы успешно Зарегистрировались/Авторизовались!", reply_markup=keyboard())
            check = True
            return check
        else:
            bot.send_message(message.chat.id, 'Вы уже Зарегистрированы!', reply_markup=keyboard())
            check = True
            return check


@bot.message_handler(commands=['home'])
def home(message):
    bot.send_message(message.chat.id, 'Вы находитесь на домашней странице!', reply_markup=keyboard())
    print(check)


def get_info(message):
    uid_new = message.text
    us_id = str(message.from_user.id)
    print(uid_new)

    cursor.execute("SELECT Score from game WHERE User_ID=?", [us_id])
    row = cursor.fetchone()
    us_score = row[0]

    if uid_new == '1' and us_score >= 1000:
        cursor.execute('''UPDATE game SET business = 'Магнит' WHERE User_ID = ?''', [us_id])
        cursor.execute(''' update game set Score=Score-1000 where User_ID=?''', [us_id])
        conn.commit()
        bot.send_message(message.chat.id, 'Вы преобрели: Магнит', reply_markup=keyboard())
    elif uid_new == '2' and us_score >=2500:
        cursor.execute('''UPDATE game SET business = 'Пятёрочка' WHERE User_ID = ?''', [us_id])
        cursor.execute(''' update game set Score=Score-2500 where User_ID=?''', [us_id])
        conn.commit()
        bot.send_message(message.chat.id, 'Вы преобрели: Пятёрочку', reply_markup=keyboard())
    elif uid_new == '3' and us_score >= 5000:
        cursor.execute('''UPDATE game SET business = 'DNS' WHERE User_ID = ?''', [us_id])
        cursor.execute(''' update game set Score=Score-5000 where User_ID=?''', [us_id])
        conn.commit()
        bot.send_message(message.chat.id, 'Вы преобрели: DNS', reply_markup=keyboard())
    else:
        bot.send_message(message.chat.id, 'Недостаточно монет!', reply_markup=keyboard())


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
            time.sleep(5)
            clan = data['clan_name']
            bot.send_message(message.chat.id,
                            'Ник: ' + str(nick) + '\n' + 'Сервер: Альфа' + '\n' + 'Ранг: ' + str(rank) + '\n' + 'Exp: ' + str(exp) + '\n' + 'Клан: ' + str(clan),
                            reply_markup=keyboard())
        except KeyError:
            bot.send_message(message.chat.id,
                             'Ник: ' + str(nick) + '\n' + 'Сервер: Альфа' + '\n' + 'Ранг: ' + str(rank) + '\n' + 'Exp: ' + str(exp) + '\n' + 'Клан: No',
                             reply_markup=keyboard())

        # bot.send_message(message.chat.id,
        #                  'Ник: ' + str(nick) + '\n' + 'Сервер: Альфа' + '\n' + 'Ранг: ' + str(rank) + '\n' + 'Exp: ' + str(exp) + '\n' + 'Клан: ' + str(clan),
        #                  reply_markup=keyboard())


def get_money(message):
    text = message.text
    us_id = str(message.from_user.id)
    cursor.execute("SELECT pin from game WHERE User_ID=?", [us_id])
    row = cursor.fetchone()
    us_bus = str(row[0])
    print(us_bus)

    if text == 'stell' and us_bus == '0':
        cursor.execute(''' update game set Score=Score+100 where User_ID=?''', [us_id])
        cursor.execute(''' update game set pin=1 where User_ID=?''', [us_id])
        conn.commit()
        bot.send_message(message.chat.id, 'Пин-код успешно активирован!', reply_markup=keyboard())
    elif us_bus == '1':
        bot.send_message(message.chat.id, 'Вы же активировали пин-код!', reply_markup=keyboard())
    else:
        bot.send_message(message.chat.id, 'Вы ввели некорректный пин-код!', reply_markup=keyboard())


@bot.message_handler(commands=['job'])
def my_funk(message):
    us_id = str(message.from_user.id)
    cursor.execute("SELECT business from game WHERE User_ID=?", [us_id])
    row = cursor.fetchone()
    us_bus = str(row[0])
    print(us_bus)
    if us_bus == 'Магнит':
        bot.send_message(message.chat.id, 'Вы начали работу! Приходите через 24часа!', reply_markup=keyboard())
        time.sleep(60)  #86400 - 24 часа
        cursor.execute(''' update game set Score=Score+100 where User_ID=?''', [us_id])
        conn.commit()
    elif us_bus == 'Пятёрочка':
        bot.send_message(message.chat.id, 'Вы начали работу! Приходите через 24часа!', reply_markup=keyboard())
        time.sleep(60)  #86400 - 24 часа
        cursor.execute(''' update game set Score=Score+500 where User_ID=?''', [us_id])
        conn.commit()
    elif us_bus == 'DNS':
        bot.send_message(message.chat.id, 'Вы начали работу! Приходите через 24часа!', reply_markup=keyboard())
        time.sleep(60)  #86400 - 24 часа
        cursor.execute(''' update game set Score=Score+1000 where User_ID=?''', [us_id])
        conn.commit()
    else:
        bot.send_message(message.chat.id, 'Купите бизнес, чтобы начать получать прибыль!', reply_markup=keyboard())


@bot.message_handler(content_types=['text'])
def get_text_message(message):
    global gg, check
    text = message.text
    if text == 'Привет' or text == 'привет':
        bot.send_message(message.chat.id, 'Хааааай', reply_markup=keyboard())
    elif text == 'Ваш баланс' or text == 'Баланс':
        try:
            us_id = str(message.from_user.id)
            cursor.execute("SELECT Score from game WHERE User_ID=?", [us_id])
            row = cursor.fetchone()
            us_score = row[0]
            bot.send_message(message.chat.id, 'Ваш баланс: ' + str(us_score) + ' монет.')
            print(row[0])
        except TypeError:
            bot.send_message(message.chat.id, 'Зарегистрируйтесь/Войдите')
    elif text == 'Купить':
        sent = bot.send_message(message.chat.id, 'Выберите бизнес:\n1- Магнит\n2- Пятёрочка\n3- DNS')
        bot.register_next_step_handler(sent, get_info)
        # us_id = str(message.from_user.id)
        # cursor.execute("SELECT business from game WHERE User_ID=?", [us_id])
        # row = cursor.fetchone()
        # us_buy = str(row[0])
        # print(us_buy)
        #
        # if us_buy != 'None':
        #     pass
        # elif gg == False:
        #     bot.send_message(message.from_user.id, "Выберите бизнес:\n1 Магнит\n2 Пятёрочка\n3 DNS")
        #
        #     gg = True
        #     print(gg)
        #     if gg == True:
        #         bot.send_message(message.from_user.id, "Вы приобрели бизнес!")

    elif text == 'Мои Бизнесы' or text == 'Бизнесы':
        us_id = str(message.from_user.id)
        cursor.execute("SELECT business from game WHERE User_ID=?", [us_id])
        row = cursor.fetchone()
        us_bus = str(row[0])
        if us_bus == 'None':
            bot.send_message(message.chat.id, 'У Вас нет бизнесов.')
        else:
            bot.send_message(message.chat.id, 'Ваши бизнесы: ' + str(us_bus))
        print(row[0])
    elif text == 'Получить монеты':
        sent = bot.send_message(message.chat.id, 'Введите пин-код:')
        bot.register_next_step_handler(sent, get_money)
    elif text == 'Help' or text == 'Помощь':
        bot.send_message(message.chat.id, 'Помощь во всём!!!', reply_markup=keyboard())
    elif text == 'Данные игрока':
        sent = bot.send_message(message.chat.id, 'Введите ник игрока.')
        bot.register_next_step_handler(sent, get_id)
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю!', reply_markup=keyboard())


def keyboard():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn_1 = types.KeyboardButton('Help')
    btn_2 = types.KeyboardButton('/Login')
    btn_3 = types.KeyboardButton('Баланс')
    btn_4 = types.KeyboardButton('Купить')
    btn_5 = types.KeyboardButton('Мои Бизнесы')
    btn_6 = types.KeyboardButton('Получить монеты')
    btn_7 = types.KeyboardButton('/job')
    btn_8 = types.KeyboardButton('Данные игрока')
    markup.add(btn_1, btn_3)
    markup.add(btn_4, btn_5)
    markup.add(btn_6, btn_7)
    markup.add(btn_2, btn_8)
    return markup





bot.polling(none_stop=True, interval=0)
