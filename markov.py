"""Builds Markov chains from Discord chat history and provides a bot command interface
to display them."""
import json
import os
import random
import discord
from discord.ext import commands
import markovify

DEFAULT_NAME = 'MathBot'

MAX_MESSAGE_LENGTH = 1800
MAX_NICKNAME_LENGTH = 30
MAX_NUM_OF_NAMES = 10
MAX_MARKOV_ATTEMPTS = 10

PEOPLE_REPO = './cogs/markov/resources/people/'
FANFIC_REPO = './cogs/markov/resources/fanfic/'

MARKOV_PEOPLE = [f for f in os.listdir(PEOPLE_REPO)]
VALID_NAMES = [f[:-5] for f in MARKOV_PEOPLE if f.find('.json') != -1]

CHARACTERS_FILE = open(f'{FANFIC_REPO}characters.txt', 'r', encoding='utf-8')
CHARACTERS = CHARACTERS_FILE.readlines()

for c in CHARACTERS:
    c = c.rstrip()

class NameNotFoundError(Exception):
    """Error raised for input that refers to no user."""
    def __init__(self, name):
        self.name = name
    # pass

class AmbiguousInputError(Exception):
    """Error raised for input that refers to multiple users"""
    def __init__(self, name, output):
        self.name = name
        self.output = output
    # pass
    

def parse_names(names_input, valid_names):
    """Returns a list of possible names from the name substring input."""
    names = []

    for name in names_input:
        current_name = []

        for valid_name in valid_names:
            if name == valid_name:
                names.append(valid_name)
                break
            if name in valid_name:
                current_name.append(valid_name)
        else:
            if current_name == "":
                raise NameNotFoundError(name)
            elif len(current_name) == 1:
                names.append(current_name[0])
            else:
                raise AmbiguousInputError(name, current_name)
    else:
        return names

def generate_models(repo, names):
    """Generates a Markov model from a given json message repo and a name."""
    models = []
    for name in names:
        try:
            with open(f'{repo}{name}.json', 'r', encoding='utf-8-sig') as json_file:
                models.append(markovify.Text.from_json(json.load(json_file)))
        except FileNotFoundError:
            raise FileNotFoundError()

    return models

def generate_markov(person, root):
    """Using a Markov model, generate a text string."""
    namelist = person.split('+')
    num_names = len(namelist)
    if num_names > MAX_NUM_OF_NAMES:
        return [f'Error: Too many inputs ({num_names}).', DEFAULT_NAME]

    try:
        names = parse_names(namelist, VALID_NAMES)
        models = generate_models(PEOPLE_REPO, names)
    except AmbiguousInputError as bad_input:
        return [f'Error: Input maps to multiple users ("{bad_input.name}" -> {bad_input.output}).',
                DEFAULT_NAME]
    except FileNotFoundError as no_file:
        return [f'Error: File not found ({no_file.filename}.json).', DEFAULT_NAME]
    except NameNotFoundError as no_user:
        return [f'Error: User not found ({no_user.name}).', DEFAULT_NAME]
    except Exception:
        return [f'Error: Unknown error.', DEFAULT_NAME]

    nickname = ''
    for name in names:
        if len(nickname) + len(name) < MAX_NICKNAME_LENGTH:
            nickname += name + '+'

    names_in_nickname = nickname[:-1].split('+')

    if len(names_in_nickname) < len(names):
        nickname += str(len(names) - len(names_in_nickname))
    else:
        nickname = nickname[:-1]

    text_model = markovify.combine(models)

    for _ in range(MAX_MARKOV_ATTEMPTS):
        if root is None:
            output = text_model.make_sentence(tries=MAX_MARKOV_ATTEMPTS)
        else:
            output = text_model.make_sentence_with_start(
                root, tries=MAX_MARKOV_ATTEMPTS, strict=False)
        if output is not None:
            return [output, nickname.title()]
    else:
        return ['Error: insufficient data for Markov chain.', DEFAULT_NAME]

def assign_name():
    """Assigns a name from a pre-loaded list of characters."""
    index = random.randint(0, len(CHARACTERS) - 1)
    return CHARACTERS[index]

def generate_fanfic(person1, person2):
    """Generates a fanfic with the given people."""
    if person1 is None:
        person1 = assign_name()
    if person2 is None:
        person2 = assign_name()

    with open(f'{FANFIC_REPO}corpus.json', 'r', encoding='utf-8-sig') as json_file:
        fanfic_model = markovify.Text.from_json(json.load(json_file))

    paragraph = ''

    while len(paragraph) < MAX_MESSAGE_LENGTH:
        sentence = fanfic_model.make_sentence() + ' '

        if len(paragraph) + len(sentence) < MAX_MESSAGE_LENGTH:
            paragraph += sentence
        else:
            break

    return paragraph.replace('$PERSON_1', person1).replace('$PERSON_2', person2).replace('\n', '')

class Markov():
    """Defines Markov commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['mk', 'rmk'])
    async def markov(self, ctx, person, root=None):
        """Generates a Markov chain based on a user's previous messages."""
        out = generate_markov(person, root)
        guilds = self.bot.guilds
        bot_self = discord.Member
        for guild in guilds:
            if guild.id == 339514092106678273:
                bot_self = guild.me
            if guild.id == 408424622648721408:
                bot_self = guild.me
        await bot_self.edit(nick=out[1])
        await ctx.send(out[0])

    @commands.command(aliases=['ff'])
    async def fanfic(self, ctx, person1=None, person2=None):
        """Generates a Markov chain based on works from fanfiction.net."""
        out = generate_fanfic(person1, person2)
        await ctx.send(out)

    @commands.command(aliases=['lm'])
    async def listmarkov(self, ctx):
        """Lists the people from which you can generate Markov chains."""
        out = []
        message = ''
        for valid_name in VALID_NAMES:
            if len(message) + len(valid_name) < MAX_MESSAGE_LENGTH:
                message += valid_name + ', '
            else:
                out.append(message[:-2])
                print(out)
                message = valid_name + ', '
        else:
            out.append(message[:-2])
        for i in range(len(out)):
            await ctx.send(out[i])

    @commands.command(hidden=True)
    async def pingcoiz(self, ctx):
        """Pings the creator of the Markov commands. Blame her if something goes wrong."""
        await ctx.send(f"<@!293219528450637824> :steam_locomotive: girl btw")

    @commands.command(hidden=True)
    async def pingmath(self, ctx):
        """Pings the host of Mathbot."""
        await ctx.send(f"<@!215367025705484289> :robot: boy btw")

def setup(bot):
    """Adds the cog to the bot."""
    bot.add_cog(Markov(bot))
