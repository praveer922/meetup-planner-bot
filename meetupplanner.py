import json
import requests
import time
import urllib
import random
import os

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
        items = db.get_items(chat)  ##
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
        elif db.meetup_started and text == "/new":
            send_message("A meetup has already started! Use /show to view or /join to participate", chat)
        elif not db.meetup_started and text == "/new":
            db.meetup_started = True
            db.add_user(userid, username)
            send_message(username + " has started a new meetup! /join to participate.", chat)
        elif text.startswith("/"):
            continue
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
