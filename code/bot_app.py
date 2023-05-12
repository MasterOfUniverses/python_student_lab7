import telebot
from telebot import types
import psycopg2
import datetime as dt
import termtables

conn = psycopg2.connect(database="bot_timetable",
                        user="bot_tg",
                        password="<your pw",
                        host="localhost",
                        port="5432")
cursor = conn.cursor()

token="<your token>"

bot = telebot.TeleBot(token)

first_study_day = dt.datetime(dt.datetime.now().year,1,31) #odd_week
first_weekday = first_study_day.weekday()
first_odd_monday = first_study_day - dt.timedelta(days=first_weekday-1)
this_day_in_tt = (1,1)

def one_day_tt(message):
    global this_day_in_tt
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("/start", "/media")
    keyboard.row("/timetable")
    keyboard.row("/teachers")
    cursor.execute(f"SELECT tt.id_time, to_char(t.start_time,'HH24:MI') , sj.name, tt.room_numb FROM timetable tt, subject sj, times t WHERE tt.id_time=t.id AND tt.id_subj=sj.id AND is_even_week={bool_to_sql_text(this_day_in_tt[0])} AND day={this_day_in_tt[1]} ORDER BY tt.id_time;")
    records = list(cursor.fetchall())
    result = termtables.to_string(records,
                                header=["Номер пары", "Начало", "Предмет", "Кабинет"],
                                style=termtables.styles.ascii_thin_double,
    )
    bot.send_message(message.chat.id,result,reply_markup=keyboard)

def week_tt(message,is_even):
    global this_day_in_tt
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("/start", "/media")
    keyboard.row("/timetable")
    keyboard.row("/Mo","/Tu","/We")
    keyboard.row("/Th","/Fr","/Sa")
    this_day_in_tt = (bool(is_even), 1)
    for i in range(1,7):
        cursor.execute(f"SELECT tt.id_time, to_char(t.start_time,'HH24:MI') , sj.name, tt.room_numb FROM timetable tt, subject sj, times t WHERE tt.id_time=t.id AND tt.id_subj=sj.id AND tt.is_even_week={bool_to_sql_text(this_day_in_tt[0])} AND tt.day={this_day_in_tt[1]} ORDER BY tt.id_time;")
        records = list(cursor.fetchall())
        result = termtables.to_string(records,
                                header=["Номер пары", "Начало", "Предмет", "Кабинет"],
                                style=termtables.styles.ascii_thin_double,
        )
        bot.send_message(message.chat.id,result,reply_markup=keyboard)
        this_day_in_tt = (is_even, 1+i)

def bool_to_sql_text(some_bool):
    if some_bool:
        return "TRUE"
    else:
        return "FALSE"

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("/media", "/help")
    keyboard.row("/timetable")
    bot.send_message(message.chat.id, 'Это ТГ-бот с расписанием для группы БВТ2202' , reply_markup=keyboard)

@bot.message_handler(commands=['help'])
def help(message):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("/start", "/media")
    keyboard.row("/timetable")
    bot.send_message(message.chat.id, 'Я умею:\n Показывать расписание на сегодня, завтра, текущую и следующую недели:\n /timetable /today /tomorrow \n /this_week /next_week')
    bot.send_message(message.chat.id, 'Выводить расписание пар:\n /lesson_times \n\nВыводить список преподавателей на выбранный день (сначала откройте выбранный день в расписании):\n /teachers')
    bot.send_message(message.chat.id, 'Выдавать список официальных (и не очень) ресурсов о ВУЗе \n /media', reply_markup=keyboard)

@bot.message_handler(commands=['timetable'])
def timetable(message):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("/today","/tomorrow")
    keyboard.row("/this_week","/next_week")
    keyboard.row("/start","/media")
    bot.send_message(message.chat.id,'Расписание для группы БВТ2202',reply_markup=keyboard)

@bot.message_handler(commands=['today'])
def today(message):
    global this_day_in_tt
    today = dt.datetime.now()
    delta = today - first_odd_monday
    is_even = (delta.days//7)%2
    weekday = today.weekday()+1
    if today.weekday() == 7:
        weekday = 1
        is_even= (is_even+1)%2
    this_day_in_tt=(bool(is_even),weekday)
    one_day_tt(message)

@bot.message_handler(commands=['tomorrow'])
def tomorrow(message):
    global this_day_in_tt
    tomorrow = dt.datetime.now() + dt.timedelta(days=1)
    delta = tomorrow - first_odd_monday
    is_even = (delta.days//7)%2
    weekday = tomorrow.weekday()+1
    if tomorrow.weekday() == 7:
        weekday = 1
        is_even= (is_even+1)%2
    this_day_in_tt=(bool(is_even),weekday)
    one_day_tt(message)

@bot.message_handler(commands=['next_week'])
def next_week(message):
    today = dt.datetime.now()
    delta = today - first_odd_monday
    is_even = (delta.days//7 +1)%2
    week_tt(message,is_even)

@bot.message_handler(commands=['this_week'])
def this_week(message):
    today = dt.datetime.now()
    delta = today - first_odd_monday
    is_even = (delta.days//7)%2
    week_tt(message,is_even)


@bot.message_handler(commands=['lesson_times'])
def lesson_times(message):
    cursor.execute("SELECT id,to_char(start_time,'HH24:MI'),to_char(end_time,'HH24:MI') FROM times ORDER BY start_time")
    records = list(cursor.fetchall())
    result = termtables.to_string(records,
                                header=["Номер пары", "Начало", "Конец"],
                                style=termtables.styles.ascii_thin_double,
    )
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("/start", "/help")
    keyboard.row("/timetable")
    bot.send_message(message.chat.id,result,reply_markup=keyboard)

@bot.message_handler(commands=['Mo'])
def Monday(message):
    global this_day_in_tt
    this_day_in_tt=(this_day_in_tt[0],1)
    one_day_tt(message)

@bot.message_handler(commands=['Tu'])
def Tuesday(message):
    global this_day_in_tt
    this_day_in_tt=(this_day_in_tt[0],2)
    one_day_tt(message)

@bot.message_handler(commands=['We'])
def Wednesday(message):
    global this_day_in_tt
    this_day_in_tt=(this_day_in_tt[0],3)
    one_day_tt(message)

@bot.message_handler(commands=['Th'])
def Thursday(message):
    global this_day_in_tt
    this_day_in_tt=(this_day_in_tt[0],4)
    one_day_tt(message)

@bot.message_handler(commands=['Fr'])
def Friday(message):
    global this_day_in_tt
    this_day_in_tt=(this_day_in_tt[0],5)
    one_day_tt(message)

@bot.message_handler(commands=['Sa'])
def Saturday(message):
    global this_day_in_tt
    this_day_in_tt=(this_day_in_tt[0],6)
    one_day_tt(message)

@bot.message_handler(commands=['teachers'])
def teachers(message):
    global this_day_in_tt
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("/start", "/media")
    keyboard.row("/timetable")
    cursor.execute(f"SELECT tt.id_time, sj.name, t.surname, t.name FROM timetable tt, subject sj, teachers t WHERE sj.id_teacher=t.id AND tt.id_subj=sj.id AND tt.is_even_week={bool_to_sql_text(this_day_in_tt[0])} AND tt.day={this_day_in_tt[1]} ORDER BY tt.id_time;")
    records = list(cursor.fetchall())
    result = termtables.to_string(records,
                                header=["Номер пары", "Предмет", "Фамилия", "Имя"],
                                style=termtables.styles.ascii_thin_double,
    )
    bot.send_message(message.chat.id,result,reply_markup=keyboard)
@bot.message_handler(commands=['media'])
def media(message):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("/start", "/help")
    keyboard.row("Оф. сайт", "Канал ТГ")
    keyboard.row("Физ. культ.", "Туризм")
    keyboard.row("/timetable")
    bot.send_message(message.chat.id,'Выберите из доступных источников: Оф. сайт , Оф. канал в телеграм, группа спортклуба МТУСИ, группа турклуба МТУСИ ',reply_markup=keyboard)
@bot.message_handler(content_types=['text'])
def answer(message):
    if (message.text.lower() == "оф. сайт") or (message.text.lower() == "сайт") or (message.text.lower() == "website"):
        keyboard = types.ReplyKeyboardMarkup()
        keyboard.row("/start", "/help")
        keyboard.row("/media","/timetable")
        bot.send_message(message.chat.id, 'https://mtuci.ru/', reply_markup=keyboard)
    elif (message.text.lower() == "канал тг") or (message.text.lower() == "тг") or (message.text.lower() == "tg"):
        keyboard = types.ReplyKeyboardMarkup()
        keyboard.row("/start", "/help")
        keyboard.row("/media","/timetable")
        bot.send_message(message.chat.id, 'https://t.me/mtuci_official \n @mtuci_official', reply_markup=keyboard)
    elif (message.text.lower() == "физ. культ.") or (message.text.lower() == "физра") or (message.text.lower() == "pe") or (message.text.lower() == "mssk") or (message.text.lower() == "мсск") or (message.text.lower() == "связист"):
        keyboard = types.ReplyKeyboardMarkup()
        keyboard.row("/start", "/help")
        keyboard.row("/media","/timetable")
        bot.send_message(message.chat.id, 'https://vk.com/mssksvyazist', reply_markup=keyboard)
    elif (message.text.lower() == "туризм") or (message.text.lower() == "тк") or (message.text.lower() == "tourism"):
        keyboard = types.ReplyKeyboardMarkup()
        keyboard.row("/start", "/help")
        keyboard.row("/media","/timetable")
        bot.send_message(message.chat.id, 'https://vk.com/stmtuci', reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Извините, я вас не понял. Пожалуйста обратитесь через список команд')
        help(message)


bot.polling(none_stop=True, interval=0)
