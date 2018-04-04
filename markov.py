"""Builds Markov chains from Discord chat history and provides a bot command interface
to display them."""
import json
import os
import random
import discord
from discord.ext import commands
import markovify
import datetime
import traceback

DEFAULT_NAME = 'MathBot'
FILTERED_PREFIXES = ('mk', 'rmk', 'markov', '$', '!', '--', 'fanfic', 'listmarkov', 'rlistmarkov')

MAX_MESSAGE_LENGTH = 1800
MAX_NICKNAME_LENGTH = 30
MAX_NUM_OF_NAMES = 10
MAX_MARKOV_ATTEMPTS = 10

RESOURCES_REPO = './cogs/markov/resources/'
PEOPLE_REPO = f'{RESOURCES_REPO}people/'
FANFIC_REPO = f'{RESOURCES_REPO}fanfic/'
CASAL_FILE = f'{RESOURCES_REPO}casallist.txt'
TIMESTAMP_FILE = f'{RESOURCES_REPO}lastupdate.txt'
MARKOV_MODULE_CREATOR_ID_FILE = f'{RESOURCES_REPO}markovcreatorid.txt'

MARKOV_PEOPLE = [f for f in os.listdir(PEOPLE_REPO)]
VALID_NAMES = [f[:-5] for f in MARKOV_PEOPLE if f.find('.json') != -1]

CHARACTERS_FILE = open(f'{FANFIC_REPO}characters.txt', 'r', encoding='utf-8')
CHARACTERS = CHARACTERS_FILE.readlines()

with open(MARKOV_MODULE_CREATOR_ID_FILE, 'r') as f:
    MARKOV_MODULE_CREATORS_ID = int(f.readline())

PERMITTED_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-"

for c in CHARACTERS:
    c = c.rstrip()


class NameNotFoundError(Exception):
    """Error raised for input that refers to no user."""
    def __init__(self, name):
        self.name = name


class AmbiguousInputError(Exception):
    """Error raised for input that refers to multiple users"""
    def __init__(self, name, output):
        self.name = name
        self.output = output


def save_timestamp(timestamp):
    timestamp_string = timestamp.isoformat(' ')
    with open(TIMESTAMP_FILE, 'w') as f:
        f.write(timestamp_string)


def load_timestamp():
    with open(TIMESTAMP_FILE, 'r') as f:
        timestamp_string = f.readline()
    return datetime.datetime.strptime(timestamp_string, '%Y-%m-%d %H:%M:%S.%f')


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
            if not current_name:
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
    """Using a Markov model, generates a text string."""
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


def update_markov_people(new_messages, authors):
    """Updates current Markov models and outputs them as .json files. It finally returns a confirmation message."""
    num_of_new_names = 0
    num_of_updated_names = 0
    num_of_messages = len(new_messages)
    models = []
    print("Updating Markov models...")
    for index, author in enumerate(authors, 1):
        print(str(index) + "/" + str(len(authors)) + ": " + author.name)
        corpus = ''
        count = 0

        for message in new_messages:
            if message.author.id == author.id:
                corpus += message.content + '\n'
                count += 1
        if count > 2:
            new_model = markovify.NewlineText(corpus)
            models.append(new_model)
            cleaned_name = "".join(c for c in author.name if c in PERMITTED_CHARS).lower()
            try:
                if cleaned_name in VALID_NAMES:
                    num_of_updated_names += 1
                    with open(f'{PEOPLE_REPO}{cleaned_name}.json', 'r', encoding='utf-8-sig') as json_file:
                        original_model = markovify.NewlineText.from_json(json.load(json_file))
                    updated_model = markovify.combine([original_model, new_model])
                    new_json = updated_model.to_json()
                    with open(f"{PEOPLE_REPO}{cleaned_name}.json", 'w') as json_file:
                        json.dump(new_json, json_file)
                else:
                    new_json = new_model.to_json()
                    VALID_NAMES.append(cleaned_name)
                    num_of_new_names += 1
                    with open(f"{PEOPLE_REPO}{cleaned_name}.json", 'w') as json_file:
                        json.dump(new_json, json_file)
            except FileNotFoundError:
                return f"Error: File not found ({cleaned_name}.json)."
            except Exception:
                traceback.print_exc()
                return f"Error: Unknown Error."
        else:
            print('User skipped due to inactivity.')
    print("Updating Memers model...")
    memers_model = markovify.combine(models)
    with open(f"{PEOPLE_REPO}memers.json", 'w') as json_file:
        json.dump(memers_model.to_json(), json_file)
    print("Update Successful.")
    return f"Corpus successfully updated with {num_of_messages} new messages, " \
           f"{num_of_updated_names} updated people, and {num_of_new_names} new people."


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


def format_casal(casal_list):
    header = '```\n-----------\nCasal List:\n-----------\n\n'

    names = ''
    for index, name in enumerate(casal_list, 1):
        names += f'{index}. {name}'

    footer = ("\n * indicates that this person was outdpsed in a pvm situation with more than two people.\n"
              "** indicates that this person is a nitpicky ass.\n\n"
              "Type '$casal help' for more information on what this is.```")

    out = header + names + footer

    return out


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
            if guild.id == 339514092106678273 or guild.id == 408424622648721408:
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
                message = valid_name + ', '
        else:
            out.append(message[:-2])
        for i in range(len(out)):
            await ctx.send(out[i])

    @commands.group(invoke_without_command=True)
    async def casal(self, ctx):
        """Displays the Casal List."""
        with open(CASAL_FILE, 'r') as file:
            casal_list = file.readlines()
        await ctx.send(format_casal(casal_list))

    @casal.command(name='help')
    async def _help(self, ctx):
        """Explains what the Casal List is."""
        msg = ("```The Casal List is the list of people who have been outdpsed by Coizioc, a known shit pvmer. "
               "If a person is on this list, then logically, that person must be worse than her in every way "
               "possible. To get onto this list, she must have outdpsed you at least once. The reason as to why "
               "this occurs is irrelevant. It is called the Casal list because Casal is the first person she "
               "ever outdpsed.```")
        await ctx.send(msg)

    @casal.command(name='add', hidden=True)
    async def _add(self, ctx, name):
        """Adds a name to the Casal List."""
        if ctx.author.id == MARKOV_MODULE_CREATORS_ID:
            with open(CASAL_FILE, 'a+') as file:
                file.write(name.rstrip() + '\n')
            await ctx.send(f"{name} successfully added to the Casal List.")
        else:
            await ctx.send(f"Error: You do not have permission to use this command.")

    @casal.command(name='remove', hidden=True)
    async def _remove(self, ctx, removed_name):
        """Removes a name from the Casal List."""
        if ctx.author.id == MARKOV_MODULE_CREATORS_ID:
            with open(CASAL_FILE, 'r+') as infile:
                casal_list = infile.read().splitlines()
            if removed_name in casal_list:
                try:
                    casal_list.remove(removed_name)
                    out = ''
                    for name in casal_list:
                        out += name + '\n'
                    with open(CASAL_FILE, 'w') as outfile:
                        outfile.write(out)
                    await ctx.send(f"{removed_name} successfully removed from the Casal List.")
                except Exception:
                    await ctx.send(f"Error: Unknown error.")
            else:
                await ctx.send(f"Error: {removed_name} not found.")
        else:
            await ctx.send(f"Error: You do not have permission to use this command.")

    @commands.command(aliases=['um'], hidden=True)
    async def updatemarkov(self, ctx):
        """Updates the corpus for the Markov module."""
        if ctx.author.id == MARKOV_MODULE_CREATORS_ID:
            print("Beginning update...")
            new_messages = []
            authors = []
            last_timestamp = load_timestamp()
            print("Fetching history...")
            history = await ctx.channel.history(after=last_timestamp, limit=None).flatten()
            print("Filtering messages...")
            for message in history:
                if not message.content.startswith(FILTERED_PREFIXES) and not message.author.bot:
                    new_messages.append(message)
                    authors.append(message.author)
                    creation_time = message.created_at
                    if creation_time > last_timestamp:
                        last_timestamp = creation_time
            await ctx.send(update_markov_people(new_messages, set(authors)))
            save_timestamp(last_timestamp)
        else:
            await ctx.send(f"Error: You do not have permission to use this command.")

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
