import telebot
import pyowm
# import logging
# from flask import Flask, request
# import os
from telebot import types

token = "767640365:AAGLF3nApdXdsJUYXMC-V5VDRIiMaLYoGN8"
tokenOWM = "c687e4132128127329716ffed7313e70"

bot = telebot.TeleBot(token)
owm = pyowm.OWM(tokenOWM, language='ru')

aaa = False
city = ""

@bot.message_handler(commands=['start'])
def Start_bot(message):
    bot.send_message(
        message.chat.id,
        'Привет! :)\nИспользуй: /help,\nчтобы узнать список доступных команд!.\n'
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton(
            'Создатель', url='telegram.me/Stelland'
  )
    )
    bot.send_message(
        message.chat.id,
        '1) Хочешь узнать погоду в своём городе? Напиши просто название города, и узнай температуру! Всё просто :).\n' +
        '2) Раз, два, три.\n' +
        '3) Ещё текст',
        reply_markup=keyboard
    )

@bot.message_handler(commands=['vk'])
def vk_sozdatelya(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton(
            'Жмякай', url='vk.com/stelland'
        )
    )
    bot.send_message(
        message.chat.id,
        'Создатель есть и Вконтакте :)',
        reply_markup=keyboard
    )

@bot.message_handler(commands=["geophone"])
def geophone(message):
    # Эти параметры для клавиатуры необязательны, просто для удобства
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_phone = types.KeyboardButton(text="Узнать свой номер телефона", request_contact=True)
    button_geo = types.KeyboardButton(text="Узнать своё местоположение", request_location=True)
    btn_back = types.KeyboardButton(text='Назад')

    keyboard.add(button_phone, button_geo)
    keyboard.add(btn_back)

    bot.send_message(message.chat.id, "Отправь мне свой номер телефона или поделись местоположением, жалкий человечишка!", reply_markup=keyboard)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    # global aaa, city
    # bot.send_message(message.chat.id, "Введите город/страну!")
    city = message.text
    aaa = True

    if aaa == True:
        try:
            observation = owm.weather_at_place(city)
            w = observation.get_weather()
            temp = w.get_temperature('celsius')["temp"]

            answer = "В г." + city + ',' + " сейчас: " + '\n--> ' + w.get_detailed_status() + ' <--' + "\n"
            answer += "Температура сейчас, в районе: " + str(temp) + " °C"

            bot.send_message(message.from_user.id, answer)
            print(answer)
            asd = False

        except pyowm.exceptions.api_response_error.NotFoundError:
            bot.send_message(message.from_user.id, "Я тебя не понимаю :(", reply_markup=keyboard())



def keyboard():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = types.KeyboardButton('/help')
    btn2 = types.KeyboardButton('/vk')
    btn3 = types.KeyboardButton('/geophone')

    markup.add(btn1, btn2)
    markup.add(btn3)
    return markup


bot.polling(none_stop=True, interval=0)
