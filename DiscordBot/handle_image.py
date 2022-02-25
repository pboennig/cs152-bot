import discord
from PIL import Image
import requests 
import io
import pytesseract


def is_image(attachment: discord.Attachment) -> bool:
    # see https://stackoverflow.com/questions/66858220/how-do-you-get-the-image-from-message-and-display-it-in-an-embed-discord-py
    return attachment.filename.endswith(".jpg") \
        or attachment.filename.endswith(".jpeg") or attachment.filename.endswith(".png") or \
        attachment.filename.endswith(".webp") or attachment.filename.endswith(".gif")

def get_text_from_attachment(attachment: discord.Attachment) -> str:
    if is_image(attachment):
        image = Image.open(io.BytesIO(requests.get(attachment.url).content))
        return pytesseract.image_to_string(image)
    return "" 