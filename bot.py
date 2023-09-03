import os
from dotenv import load_dotenv
import telebot
from pydub import AudioSegment
import cv2
import requests
import numpy as np
import traceback

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')

# In this development it's been chosen to save the files in to disk by user ID
AUDIO_STORAGE_PATH = "./audio_messages/"
PHOTO_STORAGE_PATH = "./photos/"

bot = telebot.TeleBot(BOT_TOKEN)

# Bot start greeting
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Hello!, I'm Michael-bot for Telegram. I've been developed by Pablo Sotos made exclusively to save your audio messages and detect which photos have faces in them.")

# Audio message handler
@bot.message_handler(content_types=['voice'])
def handle_audio_message(message):
    try:
        # This is to retrieve the user id and the audio file
        user_id = message.from_user.id
        audio_file = bot.download_file(bot.get_file(message.voice.file_id).file_path)
        audio_path = os.path.join(AUDIO_STORAGE_PATH, str(user_id))

        # IF the user directory does not exist, we create one
        if not os.path.exists(audio_path):
            os.makedirs(audio_path)

        # Download the audio file
        audio_filename = os.path.join(audio_path, f"audio_message.ogg")
        with open(audio_filename, "wb") as f:
            f.write(audio_file)

        # Convert the file to WAV with a samlpling freq of 16kHz
        audio = AudioSegment.from_file(audio_filename, format="ogg")
        audio_wav_filename = os.path.join(audio_path, f"audio_message_{len(os.listdir(audio_path))-1}.wav")
        audio.export(audio_wav_filename, format="wav", parameters=["-ar", "16000"])
        # Delete the original .ogg audio
        os.remove(audio_filename)

        # Answer to the user that the audio file was successfully saved
        bot.reply_to(message, "Voice message saved successfully to WAV.")
    except Exception as e:
        traceback.print_exc()
        bot.reply_to(message, "An error ocurred processing the voice note.")

# Photo message handler
@bot.message_handler(content_types=['photo'])
def handle_photo_message(message):
    try:
        user_id = message.from_user.id
        photo_file = bot.get_file(message.photo[-1].file_id)
        photo_path = os.path.join(PHOTO_STORAGE_PATH, str(user_id))

        if not os.path.exists(photo_path):
            os.makedirs(photo_path)

        photo_filename = os.path.join(photo_path, f"{message.photo[-1].file_id}.jpg")
        photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{photo_file.file_path}"

        #Download de picture
        response = requests.get(photo_url)
        if response.status_code == 200:
            with open(photo_filename, "wb") as f:
                f.write(response.content)


        # Detect faces in pictures using opencv

        # Read the image
        image = cv2.imread(photo_filename)
        # Load the Classifier
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # Convert the picture to grayscale to improve computationa efficiency
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Perform the face detection
        faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # If it finds at least one face, we save the picture
        if len(faces) > 0:
            # Create a green bounding box around the faces
            for(x, y, w, h) in faces:
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 4)

            # Answer to the user with a message and the processed image
            bot.reply_to(message, "Picture with detected faces saved successfully.")
        else:
            # If the picture doesn't have face, is removed from the directory
            os.remove(photo_filename)
            bot.reply_to(message, "No faces detected in this picture.")
    except Exception as e:
            traceback.print_exc()
            bot.reply_to(message, "An error ocurred processing the picture.")


bot.polling()