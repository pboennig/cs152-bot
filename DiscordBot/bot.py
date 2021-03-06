# bot.py
from typing import Dict
import discord
import os
import json
import logging
import re
import requests
from handle_image import get_text_from_attachment
from mod_flow import Incident
from report import Report, ThreatLevel 
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'token.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']
    perspective_key = tokens['perspective']


class ModBot(discord.Client):
    def __init__(self, key):
        intents = discord.Intents.default()
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports = {} # Map from user IDs to the state of their report
        self.incident_count = 0
        self.incident_map: Dict[int, Incident] = {}
        self.perspective_key = key
        #Loads the model from the folder 'best_model'
        first_model = AutoModelForSequenceClassification.from_pretrained('best_model', num_labels=2)
        tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
        # Makes the model easy to use:
        # Usage: nlp(string or strings to classify)
        # Output = [{'labels': "LABEL_1", 'score': probability} for string in input]
        # Violent Content = LABEL_1, Non-Violent = LABEL_0
        self.nlp = pipeline("sentiment-analysis",model=first_model, tokenizer=tokenizer)

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception("Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        # Ignore messages from the bot 
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

    async def on_message_edit(self, before, after):
        # Ignore messages from the bot 
        if after.author.id == self.user.id:
            return

        if after.guild:
            await self.handle_channel_message(after)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id:
            if payload.guild_id in self.mod_channels:
                channel = self.mod_channels[payload.guild_id]
                message: discord.Message = await channel.fetch_message(payload.message_id)
                if message.author.id == self.user.id:
                    # only respond to reactions on our own message in the mod channel
                    m = re.match(r"\*\*\[INCIDENT (\d*)\]\*\*", message.content)
                    if m is not None:
                        i = self.incident_map[int(m.group(1))]
                        responses = await i.handle_emoji(payload.emoji)
                        for r in responses:
                            await channel.send(r)
            # only care about reactions on messages that aren't DM

    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply =  "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)

        # Let the report class handle this message; forward all the messages it returns to uss
        responses = await self.reports[author_id].handle_message(message)
        for r in responses:
            await message.channel.send(r)

        # If the report is complete or cancelled, remove it from our map and forward it 
        # to the mod channel
        if self.reports[author_id].report_complete():
            r = self.reports[author_id]
            if r.threat_level != ThreatLevel.NOT_HARM:
                i =  Incident(self, self.incident_count, message.author, r.message, r.threat_level) 
                self.incident_map[self.incident_count] = i 
                self.incident_count += 1
                responses = await i.handle_message()
                for mod_channel in self.mod_channels.values():
                    for response in responses:
                        await mod_channel.send(response)
            self.reports.pop(author_id)

    async def handle_channel_message(self, message: discord.Message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return

        for attachment in message.attachments:
            message.content += get_text_from_attachment(attachment)

        if len(message.content) > 0:
            if self.eval_text(message):
                i = Incident(self, self.incident_count, None, message, ThreatLevel.AUTO_REPORT)
                self.incident_map[self.incident_count] = i
                self.incident_count += 1
                responses = await i.handle_message()
                for mod_channel in self.mod_channels.values():
                    for response in responses:
                        await mod_channel.send(response)


    def eval_text(self, message: discord.Message) -> bool:
        '''
        Given a message, forwards the message to our classifier and returns true if violent. 
        '''
        return self.nlp(message.content)[0]['label'] == 'LABEL_1'

    def code_format(self, text):
        return "```" + text + "```"


client = ModBot(perspective_key)
client.run(discord_token)
