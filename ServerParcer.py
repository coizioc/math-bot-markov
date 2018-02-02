#This file takes in a .json containing the entire server log and outputs the raw messages by user in .txt's
#which are converted into markov chains, represented as .json's. The .json's are what are referenced in the
#main function.

import json
from collections import Counter
import markovify
import re
import os

SERVER = 'SERVER_NAME'

# finds which messages were sent by a particular person and outputs them in a .txt
def save_messages(message_list, name, person_index):
    person_messages = []

    for i in range(len(message_list)):
        if message_list[i]['u'] == person_index:
            person_messages.append(message_list[i]['m'])

    file = open(name + '.txt', 'w', encoding='latin-1')
    for i in person_messages:
        file.write("%s\n" % i)

# takes a .txt and creates a markov chain from it. This is outputted as a .json
def create_markov_json(name):
    with open(name + ".txt", encoding='latin-1') as f:
        text = f.read()
    if text != "":
        text_model = markovify.NewlineText(text)
        cache = text_model.to_json()
        with open(name.lower() + ".json", 'w') as f:
            json.dump(cache, f)


with open('dht.json', 'r', encoding='latin-1') as f:
    server_dict = json.load(f)

names = []  # names array, index corresponds with 'u' of messages
messages = []  # contains message, unix timecode, and user

files = [f for f in os.listdir('.\\txt\\') if os.path.isfile(f)]
for f in files:
    if f.find(".txt") != -1:
        names.append(f[:-4])

for i in server_dict['meta']['users']:
    names.append(server_dict['meta']['users'][i]['name'])

for i in dht_dict['data'][SERVER]:
    messages.append(server_dict['data'][SERVER][i])

PERMITTED_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-"

for i in range(len(names)):
    names[i] = "".join(c for c in names[i] if c in PERMITTED_CHARS)
    save_messages(messages, names[i], i)

for n in names:
    create_markov_json(n)