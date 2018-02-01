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

valid_names = []

files = [f for f in os.listdir('.\\json\\')]

for f in files:
    if f.find(".json") != -1:
        valid_names.append(f[:-5])

def generate_markov(name):
    if name.lower() not in valid_names:
        return "Error: name not found."
    else:
        with open(".\\json\\" + name + ".json", "r", encoding='latin-1') as f:
            text_model = markovify.Text.from_json(json.load(f))

        output = "None"

        for i in range(100):
            output = text_model.make_sentence(tries=100)
            if output != "None":
                return output

        return "Error: insufficient data for Markov chain."

@client.command()
async def mk(*, name: str):
    sentence = generate_markov(name)
    await client.say(sentence)

@client.command()
async def listmarkov():
    await client.say(valid_names)

client.run('BOT_KEY_GOES_HERE')