import time

import telebot
import conf  # токен
from rhymes import get_rhyming_lines
from classifier import is_Bunin_ish

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg')
from telebot import types

bot = telebot.TeleBot(conf.TOKEN)
bot.remove_webhook()

users = {}


# самое первое сообщение
@bot.message_handler(commands=['start'])
def send_welcome(message):
    users[message.chat.id] = {
        'N': True,  # допустимо ли рифмовать на сущ
        'V': True,
        'ADJ': True,
        'ADV': True,
        'OTHER': True,
        'state': 'start',  # состояние бота в этом чате
        'line_number': 0,  # сколько раз пользователь попросил дать другую рифму для этого запроса
        'current_rhymes': None  # оставшиеся рифмы для этого запроса
    }
    command_start = types.BotCommand(command='start', description='Запустить бота')
    command_menu = types.BotCommand(command='menu', description='Перейти в основное меню')
    bot.set_my_commands([command_start, command_menu])
    bot.set_chat_menu_button(message.chat.id, types.MenuButtonCommands('commands'))
    bot.send_message(message.chat.id,
                     f"📜Здравствуйте, {message.from_user.first_name}!"
                     f" Это бот, который рифмует ваши предложения со строчками И.А. Бунина.")
    menu(message)


# певый вызов меню
@bot.message_handler(commands=['menu'], func=lambda message: message.chat.id in users)
def send_menu(message):
    menu(message)


# меню - аналог функции хелп. в нем и описание и кнопки
def menu(message):
    if message.chat.id in users:
        users[message.chat.id]['state'] = 'main'

        # создаем клавиатуру
        keyboard_menu = types.InlineKeyboardMarkup()

        # добавляем на нее инлайн кнопки. работают по коллбэкам
        button_pos = types.InlineKeyboardButton(text="🧺Изменить допустимые части речи", callback_data="button_pos")
        button_stat = types.InlineKeyboardButton(text="📔Статистика", callback_data="button_stat")
        button_model = types.InlineKeyboardButton(text="📜Похожа ли строчка на строчку Бунина?",
                                                  callback_data="button_model")
        button_rhyme = types.InlineKeyboardButton(text="🪶Получить рифму!", callback_data="button_rhyme")
        keyboard_menu.add(button_pos)
        keyboard_menu.add(button_stat)
        keyboard_menu.add(button_model)
        keyboard_menu.add(button_rhyme)

        # отправляем сообщение пользователю
        bot.send_message(message.chat.id, "Я умею много разного:\n\n"
                                          "Прежде всего, находить строчки И.А. Бунина, которые рифмуются со строчками, "
                                          "введенными вами.\n"
                                          "\nВы также можете ограничить список частей речи, на которые можно рифмовать.\n"
                                          "Например, сделать так, чтобы нельзя было рифмовать на глаголы\n\n"
                                          "Еще вы можете посмотреть статистику: "
                                          "насколько разным пользователям нравятся их запросы.\n\n"
                                          "А еще вы можете узнать, насколько строчка, которую вы написали,"
                                          " похожа на строчку И.А. Бунина! Особенно полезно это будет в сочетании"
                                          " с моей главной функцией - нахождением рифмы. Вы тоже можете быть Буниным,"
                                          " и даже нейронка не сможет вас различить!\n\n"
                                          "!!Важно: в любой момент вы можете нажать команду \menu,"
                                          " чтобы снова получить доступ к этим функциям.\n\n"
                                          "🤍", reply_markup=keyboard_menu)


# _______________________________________________________rhyming__________________________________________________


# зашли в функцию рифмовки
@bot.callback_query_handler(func=lambda call: call.data == 'button_rhyme')
def gonna_rhyme(call):
    start_rhyming(call.message)


# одна итерация "принятие строчки + рифма в ответ"
def start_rhyming(message):
    if message.chat.id in users:
        users[message.chat.id]['state'] = 'get_rhyme'
        bot.send_message(message.chat.id,
                         "Теперь вы можете отправить мне свое предложение или слово, и я отвечу на него в рифму.\n\n"
                         "Если рифма вам не понравится, нажмите на кнопку 'Другая рифма' после получения рифмы. "
                         "Я постараюсь подобрать другую рифму к этому слову\n"
                         "Если вы хотите вернуться в основное меню, нажмите на команду \menu.\n\n"
                         "Введите, пожалуйста, предложение или слово:")


# отдельная функция, чтобы не спамить в переписку, а красиво редачить сообщение из прошлой функции
@bot.message_handler(content_types=['text'],
                     func=lambda message: message.chat.id in users and users[message.chat.id]['state'] == 'get_rhyme')
def find_rhyming_lines(message):
    users[message.chat.id]['state'] = 'get_another_rhyme'
    # в этом сост новые текстовые сообщения ничего не вызывают, как и в сост main
    word = message.text.strip().split(' ')[-1].lower()
    word = word.replace('.', '').replace('…', '').replace(',', '').replace(';', '').replace(':', '').replace(
        '!', '').replace('?', '').replace('(', '').replace(')', '').replace('"', '').replace("'", '')
    # пока ждем:
    current_search = bot.send_message(message.chat.id,
                                      f'Ищу для вас рифмы к слову "{word}", это может занять минутку...')
    word = word.replace('-', '')
    is_russian = True
    for letter in word:
        if 'а' > letter or letter > 'я':
            is_russian = False
            break
    if not is_russian:
        bot.edit_message_text(chat_id=message.chat.id, message_id=current_search.message_id,
                              text="☁️Пожалуйста, введите строчку, заканчивающуюся словом из кириллицы:")
        users[message.chat.id]['state'] = 'get_rhyme'
    else:
        rhyming_lines = get_rhyming_lines(word, users[message.chat.id])
        if rhyming_lines.empty:
            bot.edit_message_text(chat_id=message.chat.id, message_id=current_search.message_id,
                                  text='☁️К сожалению, я не смог найти строчки, рифмующиеся с этим'
                                       ' предложением/словом.\nВведите, пожалуйста, другое предложение или слово:')
            users[message.chat.id]['state'] = 'get_rhyme'
        else:
            # теперь можно почти бесконечно просить его достать из вытащенного датасета другую рифму
            users[message.chat.id]['current_rhymes'] = rhyming_lines
            rhyme = pretty_line(rhyming_lines.iloc[users[message.chat.id]['line_number']])
            keyboard_rhyme = types.InlineKeyboardMarkup(row_width=2)
            button_rhyme_ok = types.InlineKeyboardButton(text="🪶Взять эту рифму", callback_data="button_rhyme_ok")
            button_rhyme_other = types.InlineKeyboardButton(text="☁️Другая Рифма", callback_data="button_rhyme_other")
            keyboard_rhyme.row(button_rhyme_ok, button_rhyme_other)
            bot.edit_message_text(chat_id=message.chat.id, message_id=current_search.message_id,
                                  text=rhyme, reply_markup=keyboard_rhyme)


# рифма не понравилась - дадим другую или скажем что рифмы кончились
@bot.callback_query_handler(func=lambda call: call.data == 'button_rhyme_other')
def try_other_rhyme(call):
    if users[call.message.chat.id]['current_rhymes'] is None:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text='☁️К сожалению, я не смог найти строчки, рифмующиеся с этим'
                                   ' предложением/словом.\nВведите, пожалуйста, другое предложение или слово:')
        users[call.message.chat.id]['state'] = 'get_rhyme'
    else:
        users[call.message.chat.id]['line_number'] += 1
        if users[call.message.chat.id]['line_number'] >= users[call.message.chat.id]['current_rhymes'].shape[0]:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text='☁️К сожалению, я не смог найти больше рифм.\n'
                                       'Давайте попробуем найти рифмы для другого предложения или слова:')
            # нужен потом для графика
            with open('stats.txt') as file:
                user_stats = list(map(str.strip, file.readlines()))
            flag = True  # еще надо записать в файл со статистикой
            for i in range(len(user_stats)):
                usr = user_stats[i].split(' ')[0]
                if flag and usr == str(call.message.chat.id):
                    flag = False
                    user_stats[i] = user_stats[i] + ' ' + str(users[call.message.chat.id]['line_number'])
            if flag:
                user_stats.append(f"{call.message.chat.id} {users[call.message.chat.id]['line_number']}")
            with open('stats.txt', 'w') as file:
                for i in user_stats:
                    print(i, file=file)
            # готовимся к получению нового запроса
            users[call.message.chat.id]['state'] = 'get_rhyme'
            users[call.message.chat.id]['line_number'] = 0
            users[call.message.chat.id]['current_rhymes'] = None
        else:
            # а вот и коллбэк - с его помощью мы исправим все то же сообщение на другую рифму для этого запроса
            rhyme = pretty_line(
                users[call.message.chat.id]['current_rhymes'].iloc[users[call.message.chat.id]['line_number']])
            keyboard_rhyme = types.InlineKeyboardMarkup(row_width=2)
            button_rhyme_ok = types.InlineKeyboardButton(text="🪶Взять эту рифму", callback_data="button_rhyme_ok")
            button_rhyme_other = types.InlineKeyboardButton(text="☁️Другая Рифма", callback_data="button_rhyme_other")
            keyboard_rhyme.row(button_rhyme_ok, button_rhyme_other)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text=rhyme, reply_markup=keyboard_rhyme)


# рифма понравилась и мы готовимся принимать новый запрос
@bot.callback_query_handler(func=lambda call: call.data == 'button_rhyme_ok')
def save_this_rhyme(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text=call.message.text)
    # этот кусок кода из предыдущей функции
    with open('stats.txt') as file:
        user_stats = list(map(str.strip, file.readlines()))
    flag = True
    for i in range(len(user_stats)):
        usr = user_stats[i].split(' ')[0]
        if flag and usr == str(call.message.chat.id):
            flag = False
            user_stats[i] = user_stats[i] + ' ' + str(users[call.message.chat.id]['line_number'])
    if flag:
        user_stats.append(f"{call.message.chat.id} {users[call.message.chat.id]['line_number']}")
    with open('stats.txt', 'w') as file:
        for i in user_stats:
            print(i, file=file)
    users[call.message.chat.id]['line_number'] = 0
    users[call.message.chat.id]['current_rhymes'] = None
    start_rhyming(call.message)


# функция красиво выводит рифму
def pretty_line(line):
    # Канун Купалы; 1903; Застят ели черной хвоей запад,; 6; запад; NOUN
    year = line['Year']
    ln = line['Original_line'].strip(',').strip(';').strip(':').strip('-').strip('(')
    if not year.isdigit():
        year = 'неизвестного'
    res = f"🪶{ln}🪶\n\n📜Это строчка номер {line['Line_number']} из стихотворения {year} года '{line['Title']}'"
    return res


# __________________________________________________POS_________________________________________________


# вызываем по кнопке изменение допустимых частей речи
@bot.callback_query_handler(func=lambda call: call.data == 'button_pos')
def change_poses(call):
    pos_buttons(call)


# изменяем. отдельная функция чтобы инлайн кнопки были как живые
# на нее нажимаешь, а на ней крестик на галочку меняется
# при этом сообщения не валятся, а одно и то же красиво изменяется
def pos_buttons(call):
    keyboard_pos = types.InlineKeyboardMarkup(row_width=2)
    button_noun = types.InlineKeyboardButton(text=f"сущ {'✔️' if users[call.message.chat.id]['N'] else '✖️'}",
                                             callback_data="button_noun")
    button_verb = types.InlineKeyboardButton(text=f"гл {'✔️' if users[call.message.chat.id]['V'] else '✖️'}",
                                             callback_data="button_verb")
    button_adj = types.InlineKeyboardButton(text=f"прил {'✔️' if users[call.message.chat.id]['ADJ'] else '✖️'}",
                                            callback_data="button_adj")
    button_adv = types.InlineKeyboardButton(text=f"нар {'✔️' if users[call.message.chat.id]['ADV'] else '✖️'}",
                                            callback_data="button_adv")
    button_other = types.InlineKeyboardButton(text=f"другие {'✔️' if users[call.message.chat.id]['OTHER'] else '✖️'}",
                                              callback_data="button_other")
    keyboard_pos.row(button_noun, button_verb)
    keyboard_pos.row(button_adj, button_adv)
    keyboard_pos.row(button_other)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=keyboard_pos,
                          text="🧺В этом разделе вы можете ограничить список частей речи, на которые можно рифмовать."
                               "\n\nЯ умею отсеивать:\n"
                               "- существительные\n"
                               "- глаголы (включая инфинитивы, причастия, деепричастия)\n"
                               "- прилагательные (полные/краткие, сравнительной степени)\n"
                               "- наречия\n- остальные части речи: предлоги, числительные и т.д.\n\n"
                               "Нажмите на кнопки внизу, если хотите исключить(✖️) или добавить(✔️) "
                               "определенную часть речи:")


# коллбэки на каждую часть речи = на каждую кнопку. чтобы изменять в словаре с данными этого чата
@bot.callback_query_handler(func=lambda call: call.data == 'button_noun')
def change_poses_noun(call):
    users[call.message.chat.id]['N'] = not users[call.message.chat.id]['N']
    pos_buttons(call)


@bot.callback_query_handler(func=lambda call: call.data == 'button_verb')
def change_poses_verb(call):
    users[call.message.chat.id]['V'] = not users[call.message.chat.id]['V']
    pos_buttons(call)


@bot.callback_query_handler(func=lambda call: call.data == 'button_adj')
def change_poses_adj(call):
    users[call.message.chat.id]['ADJ'] = not users[call.message.chat.id]['ADJ']
    pos_buttons(call)


@bot.callback_query_handler(func=lambda call: call.data == 'button_adv')
def change_poses_adv(call):
    users[call.message.chat.id]['ADV'] = not users[call.message.chat.id]['ADV']
    pos_buttons(call)


# это всякие местоимения и разные несамостоятельные части речи
@bot.callback_query_handler(func=lambda call: call.data == 'button_other')
def change_poses_other(call):
    users[call.message.chat.id]['OTHER'] = not users[call.message.chat.id]['OTHER']
    pos_buttons(call)


# _________________________________________________stat___________________________________________________


@bot.callback_query_handler(func=lambda call: call.data == 'button_stat')
def display_stats(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="📔В этом разделе вы можете посмотреть, сколько раз каждый пользователь просил"
                               "подобрать для него другую рифму к слову. На этом графике также есть вы!.\n"
                               "Для возврата в главное меню нажмите команду \menu.")
    with open('stats.txt') as file:
        user_stats = list(map(str.strip, file.readlines()))
    counter = 0
    # для каждого юзера достаем данные из файла и строим линию на графике
    for i in user_stats:
        y = list(map(int, i.split(' ')[1:]))
        x = []
        for j in range(len(y)):
            x.append(j + 1)
        if str(call.message.chat.id) == i.split(' ')[0]:
            plt.plot(x, y, label="Вы")
        else:
            counter += 1
            plt.plot(x, y, label=f"Пользователь {counter}")  # GUI outside of the main thread???
    plt.legend()
    plt.ylabel('Номер запроса')
    plt.ylabel('Количество попыток')
    plt.title('Количество попыток до получения нравящейся рифмы\nдля разных пользователей')

    plt.savefig('plot.png', dpi=300)
    bot.send_photo(call.message.chat.id, photo=open('plot.png', 'rb'))
    plt.clf() # иначе он будет добавлять по линии каждый раз как мы вызываем статистику


# _______________________________________________________model_______________________________________________


# вау функционал - моделька считает похожа ли строчка на строчку бунина
@bot.callback_query_handler(func=lambda call: call.data == 'button_model')
def start_Bunin_model(call):
    users[call.message.chat.id]['state'] = 'model'
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text="📜В этом разделе вы можете узнать, похожа ли ваша строчка на строчку И.А. Бунина.\n"
                               "Для этого просто отправьте мне строчку!\n")


@bot.message_handler(content_types=['text'],
                     func=lambda message: message.chat.id in users and users[message.chat.id]['state'] == 'model')
def Bunin_model(message):
    # я вот это делаю с состояниями чтобы бота нельзя было завалить кучей текстовых запросов пока он обрабатывает 1
    # с состояниями он один раз берет текст - а затем все последующие текст. запросы игнорирует
    users[message.chat.id]['state'] = 'main'
    line = message.text
    current_message = bot.send_message(message.chat.id, 'Оцениваю вашу строчку, это может занять минутку...')
    try:
        if is_Bunin_ish(line):
            bot.edit_message_text(chat_id=message.chat.id, message_id=current_message.message_id,
                                  text="🪶Ухты! Ваша строчка похожа на строчку Бунина! Вернемся в главное меню!")
        else:
            bot.edit_message_text(chat_id=message.chat.id, message_id=current_message.message_id,
                                  text="☁️Ваша строчка не похожа на строчку Бунина. Вернемся в главное меню")
    except Exception as e:
        # потому что мб есть такая штука, которая положит векторайзер. в этом случае деликатно уходит от ответа
        bot.edit_message_text(chat_id=message.chat.id, message_id=current_message.message_id,
                              text="☁️Ваша строчка не похожа на строчку Бунина. Вернемся в главное меню")
    # чтобы дать прочитать ответ, там дальше шмат текста из меню отправляется
    time.sleep(2)
    menu(message)


# потому что amvera не требует вебхук
if __name__ == '__main__':
    bot.polling(none_stop=True)

