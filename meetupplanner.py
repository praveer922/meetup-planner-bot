import json
import requests
import time
import urllib
import random
import os
import traceback

from datetime import datetime, timedelta
import parsedatetime as pdt
from daterangeparser import parse

from dbhelper import DBHelper

db = DBHelper()

TOKEN = "446167556:AAFZkIqi9ungryU8Trq57AIHLQ1l8kDwOrw"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)

def echo_all(updates):
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            send_message(text, chat)
        except Exception as e:
            print(e)

def handle_updates(updates):
    for update in updates["result"]:
        if "text" not in update["message"]:
            break
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        userid = update["message"]["from"]["id"]
        username = update["message"]["from"]["first_name"]
        items = db.get_items(chat)
        users = db.get_users_names(chat)  ##
        if text == "/del" or text == "/delete":
            keyboard = build_keyboard(items)
            send_message("Select an item to delete", chat, keyboard)
        elif text == "/start":
            send_message("YO BITCHES welcome to my bot. /help for updated list of features.", chat)
        elif text == "/help":
            send_message(
            "*TO-DO LIST*\n_Keep a peronal to do list in the chat._\n\nAdd items with add and remove items with delete.\nComplete items with done.\nYou can also use /del or /delete to remove multiple items.\nPin important items with pin.\nShow your current to-do list with /list.\nTry sending 'add group outing' and then 'group outing done'.\n\n*Random Quote*\nUse /quote to get a random quote.", chat)
        elif text == "/list":
            items = db.get_items(chat)  ##
            message = "\n".join(items)
            send_todo_list_message(message, chat)
        elif text == "/quote":
            send_random_quote(chat)
        elif text == "/new" and db.meetup_started:
            send_message("A meetup has already started! Use /show to view or /join to participate", chat)
        elif text == "/new" and not db.meetup_started:
            db.meetup_started = True
            if username not in users:
                db.add_user(userid, username, chat)
            send_message(username + " has started a new meetup! /join to participate.", chat)
        elif text == "/join" and db.meetup_started:
            if username not in users:
                db.add_user(userid, username, chat)
            send_message(username + " has joined! Yay!", chat)
            if len(db.get_users_names(chat)) == 2:
                send_message("When you all free? Tell me the dates", chat)
        elif text == "/join" and not db.meetup_started:
            send_message("There is no meetup yet! /new to start one now.", chat)
        elif text == "/show" and db.meetup_started:
            usersAndTheirFreeDates = db.get_users_names_and_free_dates(chat)
            usersAndTheirFreeDatesString = []
            for x in usersAndTheirFreeDates:
                dates = x[1].replace(",", "-", 1)
                usersAndTheirFreeDatesString.append(x[0] + " _" + dates +"_")
            message = "\n".join(usersAndTheirFreeDatesString)
            send_meetup_message(message, chat)
            bestDateString = getBestDate(chat).strftime("%d %B %Y")
            send_message("Ok lah, you all meet up " + bestDateString + " lah", chat)
        elif text == "/show" and not db.meetup_started:
            send_message("There is no meetup yet! /new to start one now.", chat)
        elif text.startswith("/"):
            continue
        elif isRangeOfDates(text):
            try:
                start, end = parseRangeOfDates(text)
                send_message("Start = " + start.strftime("%d %B %Y") + " End = " + end.strftime("%d %B %Y"), chat)
                db.append_date_to_user(username, text, chat)
            except:
                traceback.print_exc()
        elif isSingleDate(text):
            dt = parseSingleDate(text)
            stringDt = dt.strftime("%d %B %Y")
            send_message(stringDt,chat)
            db.append_date_to_user(username, stringDt, chat)
        elif text.startswith("delete") or text.startswith("Delete") or text.endswith("done") or text.endswith("Done"):
            if not text[7:]:
                break
            elif text[7:] in items:
                text = text[7:]
            elif "*"+text[7:]+"*" in items:
                text = "*"+text[7:]+"*"
            elif text[:-5] in items:
                text = text[:-5]
            else:
                break

            db.delete_item(text, chat)  ##
            items = db.get_items(chat)  ##
            message = "\n".join(items)
            send_todo_list_message(message, chat)
        elif text.startswith("add") or text.startswith("Add"):
            text = text[4:]
            db.add_item(text, chat)  ##
            items = db.get_items(chat)  ##
            message = "\n".join(items)
            send_todo_list_message(message, chat)
        elif text.startswith("pin") or text.startswith("Pin"):
            text = text[4:]
            db.edit_item_text(text, "*"+text+"*", chat)  ##
            items = db.get_items(chat)  ##
            message = "\n".join(items)
            send_todo_list_message(message, chat)

def getBestDate(chat):
    usersAndTheirFreeDates = db.get_users_names_and_free_dates(chat)
    freeDatesOfUsersArray = []
    for x in usersAndTheirFreeDates:
        dates = x[1].replace(", ", "", 1)
        freeDatesOfUsersArray.append(dates)
    earliestDate = getEarliestDate(freeDatesOfUsersArray)
    lastDate = getLastDate(freeDatesOfUsersArray)
    dateMatrix = createDateMatrix(earliestDate,lastDate,chat)
    counter = 0
    for x in freeDatesOfUsersArray:
        #x is string of dates of a single user, update matrix array with these dates
        arrayOfDates = x.split(",")
        for y in arrayOfDates:
            date = parseSingleDate(y)
            dateMatrix = updateMatrix(dateMatrix,date, earliestDate, counter)
        counter = counter +1
    bestDateIndex = calculateMaxOccurenceFromDateMatrix(dateMatrix)
    return earliestDate + timedelta(days=bestDateIndex)

def calculateMaxOccurenceFromDateMatrix(dateMatrix):
    maxCount = 0
    best_i = 0
    for i in range(0,len(dateMatrix[0])):
        count = 0
        for j in range(0, len(dateMatrix)):
            if dateMatrix[j][i] == 1:
                count = count +1
        if count > maxCount:
            maxCount = count
            best_i = i
    return best_i


def updateMatrix(dateMatrix,date, earliestDate, user):
    delta = date - earliestDate
    print(len(dateMatrix))
    print(len(dateMatrix[0]))
    print(delta.days)
    dateMatrix[user][delta.days] = 1
    return dateMatrix

def createDateMatrix(earliestDate,lastDate,chat):
    delta = lastDate - earliestDate
    w = delta.days + 1
    h = getNumUsers(chat)
    dateMatrix = [[0 for x in range(w)] for y in range(h)]
    return dateMatrix

def getNumUsers(chat):
    users = db.get_users_names(chat)
    count = 0
    for x in users:
        count = count +1
    return count

def getEarliestDate(freeDatesOfUsersArray):
    firstDate = datetime.today().replace(year = 2100)
    for dates in freeDatesOfUsersArray:
        firstDateOfUser = getFirstDateOfSingleUser(dates)
        if firstDateOfUser.date() < firstDate.date():
            firstDate = firstDateOfUser
    return firstDate

def getFirstDateOfSingleUser(dates):
    arrayOfDates = dates.split(",")
    firstDate = datetime.today().replace(year = 2100)
    for x in arrayOfDates:
        date = parseSingleDate(x)
        if date.date() < firstDate.date():
            firstDate = date
    return firstDate

def getLastDate(freeDatesOfUsersArray):
    lastDate = datetime.today()
    for dates in freeDatesOfUsersArray:
        lastDateofUser = getLastDateOfSingleUser(dates)
        if lastDateofUser.date() > lastDate.date():
            lastDate = lastDateofUser
    return lastDate

def getLastDateOfSingleUser(dates):
    arrayOfDates = dates.split(",")
    lastDate = datetime.today()
    for x in arrayOfDates:
        date = parseSingleDate(x)
        if date.date() > lastDate.date():
            lastDate = date
    return lastDate

def isSingleDate(text):
    return parseSingleDate(text).date() != datetime.today().date()

def isRangeOfDates(text):
    if "-" in text:
        possibleDates = text.split("-")
        lastDate = possibleDates[len(possibleDates)-1]
        if(isSingleDate(lastDate)):
            return True
    elif "to" in text:
        possibleDates = text.split("to")
        lastDate = possibleDates[len(possibleDates)-1]
        if(isSingleDate(lastDate)):
            return True
    else:
        return False

def parseSingleDate(text):
    cal = pdt.Calendar()
    time_struct, parse_status = cal.parse(text)
    dt = datetime(*time_struct[:6])
    return dt

def parseRangeOfDates(text):
    return parse(text)

def build_keyboard(items):
    keyboard = [["delete " +item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)

def send_random_quote(chat):
    quote_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'quotes.txt')
    f = open(quote_file, 'r')
    txt = f.read()
    lines = txt.split('\n.\n')

    message = random.choice(lines)
    send_message(message,chat)

def send_todo_list_message(text,chat_id, reply_markup=None):
    text = "*#### TO-DO LIST ####*\n" + text
    send_message(text,chat_id,reply_markup)

def send_meetup_message(text,chat_id, reply_markup=None):
    text = "*#### MEETUP ####*\n" + text
    send_message(text,chat_id,reply_markup)

def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)



def main():
    db.setup()
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
