from dataclasses import dataclass
from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    HARM_REPORTED = auto()
    REPORT_COMPLETE = auto()

class ThreatLevel(Enum):
    NOT_HARM = auto()
    NON_IMMINENT = auto()
    IMMINENT = auto()

class ReportType(Enum):
    SPAM = 'spam'
    HARASSMENT = 'harassment'
    INAPPROPIATE = 'inappropiate'
    HARM = 'harm'

@dataclass
class ReportedMessage:
    author: str
    content: str


class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
        self.threat_level = ThreatLevel.NOT_HARM
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply =  "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE
            return [reply]
        
        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED

            self.message = ReportedMessage(message.author.name, message.content)

            reply = "I found this message:" + "```" + message.author.name + ": " + message.content + "```\n"
            reply += "What do you think is wrong with this message?\n\n"
            reply += "If you think it is spam or fraud, say `" + ReportType.SPAM.value +"`\n" 
            reply += "If this message is harassing you or others, say `" + ReportType.HARASSMENT.value + "`\n"
            reply += "If you think this message is inappropiate or illegal, say `" + ReportType.INAPPROPIATE.value + "`\n"
            reply += "If you're worried the sender will do harm to themselves or others, say `" + ReportType.HARM.value + "`\n"
            return [reply]
        
        if self.state == State.MESSAGE_IDENTIFIED:
            type_keywords = [rt.value for rt in ReportType]
            content = message.content.strip() # remove whitespace
            if content not in type_keywords:
                reply = "Please make sure your response is one of "
                reply += ", ".join([f"`{rt}`" for rt in type_keywords[:-1]]) + ", " 
                reply += f"or `{type_keywords[-1]}`" 
                return [reply]
            else:
                if content != ReportType.HARM.value:
                    self.state = State.REPORT_COMPLETE
                    return ["Abuse type not covered in this project."]
                else:
                    self.state = State.HARM_REPORTED
                    reply = "Do you think they will act on their intentions soon?\n"
                    reply += "Type `yes` or `no`"
                    return [reply]

        if self.state == State.HARM_REPORTED:
            content = message.content.strip() # remove whitespace
            if content == 'yes' or content == 'no':
                self.threat_level = ThreatLevel.IMMINENT if content == 'yes' else ThreatLevel.NON_IMMINENT

                return ["Thank you for letting us know, we will look into this as soon as possible and" + \
                    " will notify the relevant authorities if necessary."]
            else: 
                return ["Please type either `yes` or `no`"]
        return []

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    


    

