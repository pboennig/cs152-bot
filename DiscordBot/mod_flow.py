from enum import Enum, auto
import discord
import emoji

from report import ReportedMessage, ThreatLevel

class ModState(Enum):
    FLOW_START = auto()
    AWAITING_REACT = auto()
    NONIMMINENT_THREAT = auto()
    REPORT_COMPLETE = auto()

react_state_update: dict[(str, ModState), ModState] = {
    (':double_exclamation_mark:', ModState.AWAITING_REACT) : ModState.REPORT_COMPLETE,
    (':red_exclamation_mark:', ModState.AWAITING_REACT) : ModState.NONIMMINENT_THREAT,
    (':thumbs_down:', ModState.AWAITING_REACT) : ModState.REPORT_COMPLETE,
    (':thumbs_up:', ModState.NONIMMINENT_THREAT) : ModState.REPORT_COMPLETE,
    (':thumbs_down:', ModState.NONIMMINENT_THREAT) : ModState.REPORT_COMPLETE
}

class Incident:
    def __init__(self, client, incident_num, reporter, offending_message: ReportedMessage, threat_level: ThreatLevel):
        self.state = ModState.FLOW_START
        self.reporter = reporter
        self.incident_prefix = f"**[INCIDENT {incident_num}]**\n"
        self.client = client
        self.offending_message = offending_message
        self.threat_level = threat_level 
    
    async def handle_message(self):
        assert self.state == ModState.FLOW_START
        forward_message = self.incident_prefix

        if self.reporter is not None:
            forward_message += self.reporter.name 
        else:
            forward_message += 'The bot'

        forward_message += " this message as possibly containing violence:\n" 
        forward_message += "```" + self.offending_message.author + ": " + self.offending_message.content + "```\n"
        if self.threat_level != ThreatLevel.AUTO_REPORT:
            forward_message += "They rated the treat level as "
            forward_message += "**not imminent**\n" if self.threat_level == ThreatLevel.NON_IMMINENT else "**imminent**\n"
        forward_message += "React with :thumbsdown: if the message is not a threat, :exclamation: if it is a threat but *not* imminent, and :bangbang: if it *is* imminent"
        self.state = ModState.AWAITING_REACT
        return [forward_message]

    async def handle_emoji(self, react_emoji: discord.PartialEmoji):
        react = emoji.demojize(react_emoji.name)
        if self.state == ModState.AWAITING_REACT:
            if (react, self.state) in react_state_update:
                self.state = react_state_update[(react, self.state)]

            if react == ':red_exclamation_mark:':
                return [f"{self.incident_prefix}Are they a threat to themselves? Reply :thumbsup: if yes and :thumbsdown: if not"]
            elif react == ':double_exclamation_mark:':
                return [f'{self.incident_prefix}Please remove the content, ban the user, and contact authorities. This incident is closed.']
            elif react == ':thumbs_down:':
                return [f'{self.incident_prefix}Thank you, incident closed.']

        elif self.state == ModState.NONIMMINENT_THREAT:
            if react == ':thumbs_up:':
                return [f'{self.incident_prefix}Please reach out to @{self.offending_message.author} with supportive resources.']
            elif react == ':thumbs_down:':
                return [f'Please remove the content. Ban the user if it incites violence or the user has repeatedly glorified violence']
        

        elif self.state == ModState.REPORT_COMPLETE:
            # If the incident is already closed, don't change anything
            return [f'{self.incident_prefix}Incident is already closed.']
            
        return []
        


    

