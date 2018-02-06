import markovify
import json

PERMITTED_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-"

f = open('runescape_general.txt', "r", encoding="utf-8-sig")
lines = f.readlines()

names = []
messages = []

current_name = ""

for i in range(8, len(lines)):
    current_line = lines[i]

    if current_line != '\n':
        if lines[i - 1] == '\n' and current_line.find('M]') > -1:
            current_name = current_line.split('#')[0]
        else:
            messages.append((current_name, current_line[:-1]))

for m in messages:
    names.append(m[0])

names = list(set(names))
print(len(names))

for x in range(len(names)):
    print(str(x + 1) + "/" + str(len(names)))

    person_messages = ""

    for i in range(len(messages)):
        if messages[i][0] == names[x]:
            person_messages += messages[i][1] + '\n'

    names[x] = "".join(c for c in names[x] if c in PERMITTED_CHARS)

    if person_messages != "" and person_messages.count('\n') > 499:
        print("Found a user to add!")
        try:
            text_model = markovify.NewlineText(person_messages)
        except KeyError:
            for m in person_messages.split('\n'):
                print(names[x] + ": " + m)
        cache = text_model.to_json()
        with open(f"rjson/{names[x].lower()}.json", 'w') as f:
            json.dump(cache, f)
