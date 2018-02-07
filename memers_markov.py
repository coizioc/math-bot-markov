#!/usr/bin/python3.6

import os
import json
import platform
import discord
from discord.ext.commands import Bot
import markovify
from user_exceptions import AmbiguousInputError, NoUserInputError

DEFAULT_NAME = "MemersMarkov"
# I need the absolute path to work with crontab until I figure out how to gracefully do relative
# imports that work with cron
ABSPATH = '/home/austin/Documents/MemersMarkov'
WINDOWS_MEMERS_REPO = ".\\json\\"
WINDOWS_REDDIT_REPO = ".\\rjson\\"
WINDOWS_BOT_TOKEN = ".\\tokens\\bottoken.txt"
LINUX_MEMERS_REPO = f"{ABSPATH}/json/"
LINUX_REDDIT_REPO = f"{ABSPATH}/rjson/"
LINUX_BOT_TOKEN = f"{ABSPATH}/tokens/bottoken.txt"
PLATFORM = platform.system()
if PLATFORM == "Linux":
    MEMERS_REPO = LINUX_MEMERS_REPO
    REDDIT_REPO = LINUX_REDDIT_REPO
    BOT_TOKEN = LINUX_BOT_TOKEN
elif PLATFORM == "Windows":
    MEMERS_REPO = WINDOWS_MEMERS_REPO
    REDDIT_REPO = WINDOWS_REDDIT_REPO
    BOT_TOKEN = WINDOWS_BOT_TOKEN
else:
    print(PLATFORM)
    raise Exception(PLATFORM)

def main():
    """Runs the discord bot."""
    client = Bot(description="MemersMarkov", command_prefix="", pm_help=False)

    @client.event
    async def on_ready():
        """Locally displays runtime info when the bot come online"""
        print(f"Logged in as {client.user.name} (ID:{client.user.id}) | ",
              "Connected to {str(len(client.servers))} servers | ",
              "Connected to {str(len(set(client.get_all_members())))} users")
        print("--------")
        print(f"Current Discord.py Version: {discord.__version__} | ",
              "Current Python Version: {platform.python_version()}")
        print("--------")
        print("Use this link to invite {client.user.name}:")
        print(f"https://discordapp.com/oauth2/authorize?client_id={client.user.id}",
              "&scope=bot&permissions=8")
        return await client.change_presence()

    memers_files = [f for f in os.listdir(MEMERS_REPO)]
    valid_names = [f[:-5] for f in memers_files if f.find(".json") != -1]

    r_files = [f for f in os.listdir(REDDIT_REPO)]
    r_valid_names = [f[:-5] for f in r_files if f.find(".json") != -1]

    def parse_names(name_input, usable_names):
        """Returns a list of possible names from the name substring input."""
        name = []

        for n in name_input:
            current_name = []

            for x in usable_names:
                if n == x:
                    name.append(x)
                    break
                if n in x:
                    current_name.append(x)
            else:
                if len(current_name) == 0:
                    raise NoUserInputError(n, str(current_name))
                elif len(current_name) == 1:
                    name.append(current_name[0])
                else:
                    raise AmbiguousInputError(n, str(current_name))
        else:
            return name

    def generate_models(repo, name):
        """Generates a Markov model from a given json message repo and a name."""
        models = []

        for n in name:
            try:
                with open(f"{repo}{n}.json", 'r', encoding='utf-8-sig') as f:
                    models.append(markovify.Text.from_json(json.load(f)))
            except:
                raise FileNotFoundError()

        return models


    def generate_markov(args, reddit=False):
        """Generates the actual Markov ouput string from the list of args."""
        args_list = args.split(' ')
        name_input = args_list[0].split('+')
        if len(name_input) > 10:
            return ['Error: too many inputs. ({num_names})'.format(num_names=len(name_input)), DEFAULT_NAME]
        root = ''.join([args_list[1] if len(args_list) > 1 else ''])

        try:
            if reddit:
                name_list = r_valid_names
                repo = REDDIT_REPO
            else:
                name_list = valid_names
                repo = MEMERS_REPO

            name = parse_names(name_input, name_list)
            models = generate_models(repo, name)

        except NoUserInputError as no_user:
            msg = f"Error: User not found ({no_user.name})"
            return [msg, DEFAULT_NAME]
        except AmbiguousInputError as bad_input:
            msg = f"Error: Input maps to multiple users. ('{bad_input.name}' -> {bad_input.output})"
            return [msg, DEFAULT_NAME]
        except FileNotFoundError as no_file:
            msg = f"Error: File not found ({no_file.filename}.json)"
            return [msg, DEFAULT_NAME]
        
        nickname = ""
        
        for n in name:
            try:
                with open(f"{repo}{n}.json", 'r', encoding='utf-8-sig') as f:
                    models.append(markovify.Text.from_json(json.load(f)))
            except FileNotFoundError:
                return ['Error: File not found ({name}.json)'.format(name=n), DEFAULT_NAME]

            if len(nickname) + len(n) + 1 <= 30:
                nickname += n + "+"

        if len(nickname[:-1].split('+')) < len(name):
            nickname += str(len(name) - len(nickname[:-1].split('+')))
        else:
            nickname = nickname[:-1]

        text_model = markovify.combine(models)

        for _ in range(50):
            output = None

            if root == "":
                output = text_model.make_sentence(tries=10)
            else:
                output = text_model.make_sentence_with_start(root, tries=10, strict=False)
            if output is not None:
                return [output, nickname.title()]
        else:
            return ['Error: insufficient data for Markov chain.', DEFAULT_NAME]

    @client.command()
    async def mk(*, args: str):
        """Command that generates and returns a Markov string for the given users."""
        out = generate_markov(args)
        servers = client.servers
        for server in servers:
            if server.id == '339514092106678273':
                bot_self = server.me
        await client.change_nickname(bot_self, out[1])
        await client.say(out[0])
        await client.change_nickname(bot_self, DEFAULT_NAME)

    @client.command()
    async def rmk(*, args: str):
        """Command that generates and returns a Markov string for the given users."""
        out = generate_markov(args, reddit=True)
        servers = client.servers
        for server in servers:
            if server.id == '339514092106678273':
                bot_self = server.me
        await client.change_nickname(bot_self, out[1])
        await client.say(out[0])
        await client.change_nickname(bot_self, DEFAULT_NAME)

    @client.command()
    async def pingcoiz():
        """Pings the Markov bot creator."""
        await client.say(f"<@!293219528450637824> :steam_locomotive: girl btw")

    @client.command()
    async def listmarkov():
        """Returns a list of the tracked users."""
        await client.say(valid_names)

    @client.command()
    async def rlistmarkov():
        """Returns a list of the tracked users from the Reddit server."""
        await client.say("The list of valid names can be found at https://pastebin.com/GqxMT5r8")

    @client.command()
    async def am():
        """Call and response command."""
        await client.say("Yes you are.")

    with open(f"{BOT_TOKEN}", "r+") as bottoken:
        token = bottoken.read().strip()
        client.run(token)

if __name__ == "__main__":
    main()
