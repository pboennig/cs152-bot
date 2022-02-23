from enum import Enum, auto

from report import ReportedMessage, ThreatLevel

class ModState(Enum):
    FLOW_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    HARM_REPORTED = auto()
    REPORT_COMPLETE = auto()

class Incident:
    def __init__(self, client, incident_num, reporter, offending_message: ReportedMessage, threat_level: ThreatLevel):
        self.state = ModState.FLOW_START
        self.reporter = reporter
        self.incident_prefix = f"**[INCIDENT {incident_num}**]\n"
        self.client = client
        self.offending_message = offending_message
        self.threat_level = threat_level 
    
    async def handle_message(self):
        if self.state == ModState.FLOW_START:
            forward_message = self.incident_prefix
            forward_message += f"`{self.reporter.name}` reported this message as possibly containing violence:\n" 
            forward_message += "```" + self.offending_message.author + ": " + self.offending_message.content + "```\n"
            forward_message += "They rated the treat level as "
            forward_message += "**not imminent**\n" if self.threat_level == ThreatLevel.NON_IMMINENT else "**imminent**\n"
            return [forward_message]
        return []
    


    

