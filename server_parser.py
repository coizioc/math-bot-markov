#!/usr/bin/python3.6
# This file takes in a .json containing the entire server log and outputs the raw messages
# By user in .txts, which are converted into markov chains, represented as .json's.
# The .jsons are what are referenced in the main function.

import os
import platform
import json
import markovify

SERVER = 'SERVER_NAME'
ABSPATH = '/home/austin/Documents/MemersMarkov'
WINDOWS_MEMERS_REPO = ".\\json\\"
WINDOWS_REDDIT_REPO = ".\\rjson\\"
LINUX_MEMERS_REPO = f"{ABSPATH}/json/"
LINUX_REDDIT_REPO = f"{ABSPATH}/rjson/"
PLATFORM = platform.system()
if PLATFORM == "Linux":
    MEMERS_REPO = LINUX_MEMERS_REPO
    REDDIT_REPO = LINUX_REDDIT_REPO
elif PLATFORM == "Windows":
    MEMERS_REPO = WINDOWS_MEMERS_REPO
    REDDIT_REPO = WINDOWS_REDDIT_REPO
else:
    print(PLATFORM)
    raise Exception(PLATFORM)

def save_messages(message_list, name, person_index):
    """Finds which messages were sent by a particular person and outputs them in a .txt."""
    person_messages = []

    for k in range(len(message_list)):
        if message_list[k]['u'] == person_index:
            person_messages.append(message_list[k]['m'])

    file = open(name + '.txt', 'w', encoding='latin-1')
    for j in person_messages:
        file.write("%s\n" % j)

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
