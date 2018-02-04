# MemersMarkov was created by Coizioc: https://github.com/coizioc/MemersMarkov
# Basic Bot was created by Habchy: https://github.com/Habchy/BasicBot
# Markovify was created by jsvine: https://github.com/jsvine/markovify

import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import platform
import markovify
import os
import json

client = Bot(description="MemersMarkov", command_prefix="", pm_help = False)
@client.event
async def on_ready():
    print('Logged in as '+client.user.name+' (ID:'+client.user.id+') | Connected to '+str(len(client.servers))+' servers | Connected to '+str(len(set(client.get_all_members())))+' users')
    print('--------')
    print('Current Discord.py Version: {} | Current Python Version: {}'.format(discord.__version__, platform.python_version()))
    print('--------')
    print('Use this link to invite {}:'.format(client.user.name))
    print('https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=8'.format(client.user.id))
    print('--------')
    print('Support Discord Server: https://discord.gg/FNNNgqb')
    print('Github Link: https://github.com/Habchy/BasicBot')
    print('--------')
    print('You are running BasicBot v2.1')
    print('Created by Habchy#1665')
    return await client.change_presence()

DEFAULT_NAME = "MemersMarkov"
valid_names = []

files = [f for f in os.listdir('.\\json\\')]

for f in files:
    if f.find(".json") != -1:
        valid_names.append(f[:-5])


def generate_markov(args):
    args_list = args.split(' ')

    name_input = args_list[0].split('+')
    root = ""

    if len(args_list) > 1:
        root += args_list[1]

    models = []
    name = []

    for n in name_input:
        count = 0

        for x in valid_names:
            if n in x:
                count += 1
                name.append(x)

        if count > 1:
            return ["Error: Input maps to multiple names. (" + n + ")", DEFAULT_NAME]

    nickname = ""

    for n in name:
        try:
            with open(".\\json\\" + n + ".json", "r", encoding='utf-8-sig') as f:
                models.append(markovify.Text.from_json(json.load(f)))
        except:
            return ["Error: Name not found (" + n + ")", DEFAULT_NAME]

        nickname += n + "+"

    text_model = markovify.combine(models)

    output = "None"
    for i in range(50):
        if root != "":
            output = text_model.make_sentence_with_start(root, tries=10, strict=False)
        else:
            output = text_model.make_sentence(tries=100)
        if output is not None:
            return [output, nickname[:-1].title()]

    return ["Error: insufficient data for Markov chain.", DEFAULT_NAME]

@client.command()
async def mk(*, args: str):
    out = generate_markov(args)
    #await client.change_nickname(discord.Member.nick, out[1])
    await client.say("**" + out[1] + "**: " + out[0])

@client.command()
async def pingcoiz() :
    await client.say(":steam_locomotive: girl btw")

@client.command()
async def listmarkov():
    await client.say(valid_names)

@client.command()
async def am():
    await client.say("Yes you are.")


client.run('BOT_KEY_GOES HERE')
