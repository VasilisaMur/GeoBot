from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import requests
import random
import codecs



def file_reader(file_name):
    file = codecs.open("capitals1.txt", "r", "utf-8")
    string = file.readlines()
    file.close()
    string = list(map(lambda x: x.strip(), string))
    info = {}
    for i in string:
        info[i.split("\t")[0]] = i.split("\t")[1]
    return info


def get_ll_spn(toponym):
    ll = list(map(lambda x: str(x), toponym["Point"]["pos"].split()))
    lowercorner = list(map(lambda x: float(x), toponym["boundedBy"]["Envelope"]["lowerCorner"].split()))
    uppercorner = list(map(lambda x: float(x), toponym["boundedBy"]["Envelope"]["upperCorner"].split()))
    spn = list(map(lambda x: str(x), [uppercorner[0] - lowercorner[0], uppercorner[1] - lowercorner[1]]))
    return ll, spn


def photo(bot, update, address, text_map=False):
    if text_map:
        text = "Столица страны {} - {}".format(address, info[address])
    else:
        text = "Страна обозначена меткой"
    answer = geocode(address)
    if answer:
        bot.sendPhoto(
            update.message.chat.id,  # Идентификатор чата. Куда посылать картинку.
            # Ссылка на static API по сути является ссылкой на картинку.
            answer,
            text)
    else:
        update.message.reply_text("Упс, кажется, что-то пошло не так.")


def start(bot, update, user_data):
    update.message.reply_text('''
    Привет!✋
Я ГеоБот, приятно познакомиться.😉
Что я умею:
/text_test - тест
/photo_test - тоже тест, но немного другой
/game - игра "Верю - не верю"
/teach *страна* - обучение 	
Итак, немного подробнее. 
Тест №1 - я пишу тебе столицу, а ты должен в ответ написать страну
Тест №2 - я присылаю тебе карту страны, а ты должен в ответ прислать ее столицу
Игра - я присылаю тебе вопрос в формате "страна - столица", а ты отвечаешь - веришь или нет ;-)
Обучение состоит в том, что ты пишешь название страны, а я пишу тебе столицу и присылаю карту этой страны
Если ты что-нибудь забудешь, можешь всегда вызвать команду /help
Если ты захочешь все прекратить, напиши команду /stop
    ''')
    user_data["mode"] = 0
    user_data["dont_changed_mode"] = 1
    user_data["game"] = 0


def exit(bot, update, user_data):
    if user_data["good"] != 0 or user_data["bad"] != 0:
        update.message.reply_text("Результаты теста:\nВсего ответов {}.\n✅Правильных - {}\n❌Неправильных - {}.".format(
            user_data["good"] + user_data["bad"], user_data["good"], user_data["bad"]))
        if user_data["hints_all"]:
            update.message.reply_text("Использование подсказок - {}".format(user_data["hints_all"]))
        else:
            update.message.reply_text("Ты не использовал подсказки.")
        update.message.reply_text("Надеюсь, тебе понравился тест.😊\nЧто будем делать? Напиши команду.")
    else:
        update.message.reply_text("Хорошо. Что будем делать? Напиши команду.")
    user_data["mode"] = 0
    return ConversationHandler.END


def hint_text_test(bot, update, user_data):
    variants = [user_data["country"]]
    for i in range(2):
        country = random.choice(list(info.keys()))
        while country in variants:
            country = random.choice(list(info.keys()))
        variants.append(country)
    reply_keyboard = list(map(lambda x: [x],variants))
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Один из этих вариантов ответа верный:\n{}".format('\n'.join(variants)), reply_markup = markup)


def text_test(bot, update, user_data):
    if user_data["mode"] == 0:
        user_data["mode"] = 1
        update.message.reply_text("Итак, напоминаю. Я присылаю тебе столицу, а ты пишешь страну."
                                  "\nЕсли тебе надоест, напиши /exit.")
        update.message.reply_text("Начнем? (ответь да или нет)")
        user_data["good"] = 0
        user_data["bad"] = 0
        user_data["hints_all"] = 0
        return 1
    else:
        reply_keyboard = [["Да", "Нет"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("Вы уверены, что хотите прервать текущий сеанс?", reply_markup=markup)
        user_data["mode"] = 7


def question_text_test(bot, update, user_data):
    answer = update.message.text.lower()
    if answer == "да":
        country = random.choice(list(info.keys()))
        capital = info[country]
        user_data["country"] = country
        user_data["question_now"] = capital
        if country == "Науру":
            update.message.reply_text("У какой страны нет официальной столицы?\nЕсли хочешь взять подсказку - пиши 'подсказка'")
        else:
            update.message.reply_text("Какой страны столица {} ...?\nЕсли хочешь взять подсказку - пиши 'подсказка'".format(capital))
        user_data["hint"] = False
        return 2
    elif answer == "нет":
        return exit(bot, update, user_data)
    else:
        update.message.reply_text("Кажется, ты ввел что-то не то. Попробуй еще раз (я понимаю только да или нет).")
        return 1


def answer_text_test(bot, update, user_data):
    hint = False
    if user_data["mode"] ==1:
        if user_data["dont_changed_mode"]:
            answer = update.message.text
            true_answer = user_data["country"]
            if answer.lower() == "подсказка":
                if not user_data["hint"]:
                    hint_text_test(bot, update, user_data)
                    user_data["hints_all"] += 1
                    user_data["hint"] = True
                else:
                    update.message.reply_text("Ты уже брал подсказку на этом вопросе!")
                hint = True
            else:
                if answer.lower() == true_answer.lower():
                    if hint:
                        update.message.reply_text("Правильно!", reply_markup=ReplyKeyboardRemove())
                    else:
                        update.message.reply_text("Правильно!")
                    user_data["good"] += 1
                else:
                    if hint:
                        update.message.reply_text("Неправильно", reply_markup=ReplyKeyboardRemove())
                    else:
                        update.message.reply_text("Неправильно")
                    user_data["bad"] += 1
                photo(bot, update, user_data["country"], True)
        if not hint:
            update.message.reply_text("Продолжим? (ответь да или нет)")
            user_data["dont_changed_mode"] = 1
            return 1
        return 2
    else:
        return change_mode(bot, update, user_data, 1)


def photo_test(bot, update, user_data):
    if user_data["mode"] == 0:
        user_data["mode"] = 3
        update.message.reply_text("Итак, напоминаю. Я присылаю тебе карту страны, а ты пишешь столицу."
                                  "\nЕсли тебе надоест, напиши /exit.")
        update.message.reply_text("Начнем? (ответь да или нет)")
        user_data["good"] = 0
        user_data["bad"] = 0
        user_data["hints_all"] = 0
        return 3
    else:
        reply_keyboard = [["Да","Нет"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("Вы уверены, что хотите прервать текущий сеанс?", reply_markup=markup)
        user_data["mode"] = 7


def question_photo_test(bot, update, user_data):
    answer = update.message.text.lower()
    if answer == "да":
        country = random.choice(list(info.keys()))
        user_data["question_now"] = country
        update.message.reply_text("Столица этой страны - ...? (Сейчас пришлю карту)\nЕсли хочешь взять подсказку - пиши 'подсказка'")
        photo(bot, update, country)
        user_data["hint"] = False
        return 4
    elif answer == "нет":
        return exit(bot, update, user_data)
    else:
        update.message.reply_text("Кажется, ты ввел что-то не то. Попробуй еще раз (я понимаю только да или нет).")
        return 3


def hint_photo_test(bot, update, user_data):
    variants = [info[user_data["question_now"]]]
    for i in range(2):
        capital = random.choice(list(info.values()))
        while capital in variants:
            capital = random.choice(list(info.values()))
        variants.append(capital)
    reply_keyboard = list(map(lambda x: [x],variants))
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Один из этих вариантов ответа верный:\n{}".format('\n'.join(variants)),reply_markup=markup)


def answer_photo_test(bot, update, user_data):
    hint = False
    if user_data["mode"] == 3:
        if user_data["dont_changed_mode"]:
            answer = update.message.text.lower()
            true_answer = info[user_data["question_now"]]
            if answer == 'подсказка':
                if not user_data["hint"]:
                    hint_photo_test(bot,update,user_data)
                    user_data["hints_all"] += 1
                    user_data["hint"] = True
                else:
                    update.message.reply_text("Ты уже брал подсказку на этом вопросе!")
                hint = True
            else:
                if answer == true_answer.lower():
                    update.message.reply_text("Правильно!")
                    user_data["good"] += 1
                else:
                    update.message.reply_text("Неправильно")
                    user_data["bad"] += 1
                photo(bot, update, user_data["question_now"], True)
        if not hint:
            update.message.reply_text("Продолжим? (ответь да или нет)")
            user_data["dont_changed_mode"] = 1
            return 3
        return 4
    else:
        return change_mode(bot, update, user_data, 3)


def game(bot, update, user_data):
    if user_data["mode"] == 0:
        update.message.reply_text(
            "Итак, напоминаю. Я присылаю вопрос в формате 'страна - столица', а ты выбираешь на клавиатуре"
            " веришь или нет")
        update.message.reply_text("Начнем? (ответь да или нет)")
        user_data["good"] = 0
        user_data["bad"] = 0
        user_data["mode"] = 5
        user_data["game"] = True
        return 5
    else:
        reply_keyboard = [["Да","Нет"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("Вы уверены, что хотите прервать текущий сеанс?", reply_markup=markup)
        user_data["mode"] = 7


def question_game(bot, update, user_data):
    answer = update.message.text.lower()
    if answer == "да":
        question = random.choice(list(info.keys()))
        user_data["question"] = question
        variants = [info[random.choice(list(info.keys()))] for i in range(2)] + [info[question]]
        variant = random.choice(variants)
        user_data["variant"] = variant
        update.message.reply_text("{} - {}".format(question, variant))
        reply_keyboard = [["Верю", "Не верю"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("Веришь?", reply_markup=markup)
        return 6
    elif answer == "нет":
        return exit_game(bot, update, user_data)
    else:
        update.message.reply_text("Кажется, ты ввел что-то не то. Попробуй еще раз (я понимаю только да или нет).")
        return 5


def answer_game(bot, update, user_data):
    if user_data["mode"] == 5:
        if user_data["dont_changed_mode"]:
            answer = update.message.text
            true_answer = info[user_data["question"]]
            # проверяем совпадение столицы и той столицы, которая выпала
            conformity = bool(true_answer == user_data["variant"])
            if conformity:
                if answer.lower() == "верю":
                    update.message.reply_text("Молодец!")
                    user_data["good"] += 1
                elif answer.lower() == "не верю":
                    update.message.reply_text("А зря!")
                    user_data["bad"] += 1
                else:
                    update.message.reply_text("Кажется, ты ввел что-то не то. Попробуй еще раз, я понимаю только верю и не верю")
                    return 6
            else:
                if answer.lower() == "верю":
                    update.message.reply_text("Зря, я тебя обманул!")
                    user_data["bad"] += 1
                elif answer.lower() == "не верю":
                    update.message.reply_text("И правильно!")
                    user_data["good"] += 1
                else:
                    update.message.reply_text("Кажется, ты ввел что-то не то. Попробуй еще раз, я понимаю только верю и не верю")
                    return 6
            photo(bot, update, user_data["question"], text_map=True)
        update.message.reply_text("Продолжим? ответь да или нет", reply_markup=ReplyKeyboardRemove())
        return 5
    else:
        return change_mode(bot, update, user_data, 3)


def exit_game(bot, update, user_data):
    if user_data["good"] != 0 or user_data["bad"] != 0:
        update.message.reply_text("Подведем итоги игры:\n✅Угадано правильно - {}\n❌Неправильно - {}".format(
            user_data["good"], user_data["bad"]
        ))
        update.message.reply_text("Спасибо за игру! Надеюсь, тебе понравилось.😊\nЧто будем делать? Напиши команду.")
    else:
        update.message.reply_text("Хорошо. Что будем делать? Напиши команду.")
    user_data["mode"] = 0
    return ConversationHandler.END


def change_mode(bot,update, user_data,num):
    answer = update.message.text
    if answer.lower() == "да":
        user_data["mode"] = 0
        if user_data["game"]:
            return exit_game(bot,update,user_data)
        return exit(bot,update,user_data)
    elif answer.lower() == 'нет':
        user_data["mode"] = num
        user_data["dont_changed_mode"] = 0
        update.message.reply_text("Неожиданный соц-опрос. Сколько тебе лет?")
        return num+1
    else:
        update.message.reply_text("Кажется, ты ввел что-то не то. Я понимаю только да или нет. Попробуй еще раз.")
        change_mode(bot, update, user_data)


def teach(bot, update, args):
    if args:
        address = args[0].capitalize()
        if address not in info:
            update.message.reply_text("Такой страны нет")
        else:
            photo(bot, update, address, True)
    else:
        update.message.reply_text("Напоминаю формат ввода - /teach *страна*")


def help(bot, update):
    update.message.reply_text('''
Что я умею:
/text_test - Тест №1 - я пишу тебе столицу, а ты должен в ответ написать страну
/photo_test - Тест №2 - я присылаю тебе карту страны, а ты должен в ответ прислать ее столицу
/game - игра "Верю - не верю" - я присылаю тебе вопрос в формате "страна - столица", а ты отвечаешь - веришь или нет
/teach *страна* - обучение - ты пишешь название страны, а я пишу тебе столицу и присылаю карту этой страны
Если ты захочешь все прекратить, напиши команду /stop
''')


def geocode(address):
    response = None
    try:
        geocoder_uri = geocoder_request_template = "http://geocode-maps.yandex.ru/1.x/"
        response = requests.get(geocoder_uri, params={
            "format": "json",
            "geocode": address
        })
        if response:
            if not response.json()["response"]["GeoObjectCollection"]["featureMember"]:
                return
            else:
                toponym = response.json()["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]

                ll, spn = get_ll_spn(toponym)

                static_api = "http://static-maps.yandex.ru/1.x/?"
                static_api_params = "ll={}&spn={}&l=map&pt={}".format(','.join(ll), ','.join(spn),
                                                                      ','.join(ll) + ",pm2ntm")
                static_api_request = ''.join([static_api, static_api_params])
                return static_api_request
        return
    except:
        return


def stop(bot, update):
    update.message.reply_text("Очень жаль, что ты уходишь. До скорой встречи!")


def main():
    updater = Updater("529825050:AAELw42tGUsiCHecC10H86rontm0Dv1cPnU")

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start, pass_user_data=True))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("teach", teach, pass_args=True))
    conver_handler_text_test = ConversationHandler(
        entry_points=[CommandHandler("text_test", text_test, pass_user_data=True)],
        states={

            1: [MessageHandler(Filters.text, question_text_test, pass_user_data=True)],
            2: [MessageHandler(Filters.text, answer_text_test, pass_user_data=True)]
        },
        fallbacks=[CommandHandler("exit", exit, pass_user_data=True)]

    )
    dp.add_handler(conver_handler_text_test)

    conver_handler_photo_test = ConversationHandler(
        entry_points=[CommandHandler("photo_test", photo_test, pass_user_data=True)],
        states={
            3: [MessageHandler(Filters.text, question_photo_test, pass_user_data=True)],
            4: [MessageHandler(Filters.text, answer_photo_test, pass_user_data=True)]
        },
        fallbacks=[CommandHandler("exit", exit, pass_user_data=True)]
    )
    dp.add_handler(conver_handler_photo_test)

    conver_handler_game = ConversationHandler(
        entry_points=[CommandHandler("game", game, pass_user_data=True)],
        states={
            5: [MessageHandler(Filters.text, question_game, pass_user_data=True)],
            6: [MessageHandler(Filters.text, answer_game, pass_user_data=True)]
        },
        fallbacks=[CommandHandler("exit", exit_game, pass_user_data=True)]
    )
    dp.add_handler(conver_handler_game)
    print('bot started')
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    info = file_reader("capitals1.txt")
    main()