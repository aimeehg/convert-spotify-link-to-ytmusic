import telebot
import re
from os import environ as env
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy import Spotify
from ytmusicapi import YTMusic
from thefuzz import fuzz
import json
from requests.exceptions import HTTPError
from spotipy.exceptions import SpotifyException

# Load environment variables
load_dotenv()

# Initialize Spotify and YouTube Music APIs
sp = Spotify(auth_manager=SpotifyClientCredentials())
ytmusic = YTMusic()

# Initialize Telegram bot
bot_token = env.get("BOT_TOKEN") 
bot = telebot.TeleBot(bot_token)

# Function to calculate similarity between two strings
def calculate_similarity(str1, str2):
    return fuzz.token_set_ratio(str1.lower(), str2.lower())

# Create a custom keyboard for the track results
markup = telebot.types.InlineKeyboardMarkup()

# Handle for Spotify links
@bot.message_handler(func=lambda message: "spotify.com" in message.text)
def handle_spotify_link(message):
    chat_id = message.chat.id
    spotify_link = message.text

    # Use regex to extract the track ID from the Spotify URL
    match = re.search(r'/track/([a-zA-Z0-9]+)', spotify_link)
    if match:
        track_id = match.group(1)
    else:
        bot.send_message(chat_id, "Invalid Spotify URL.")
        return

    try:
        # Get track information from Spotify
        track_info = sp.track(track_id)
        track_name_spotify = track_info['name']
        artist_name_spotify = track_info['artists'][0]['name']
    except (HTTPError, SpotifyException) as e:
        # Handle exceptions and send an error message to the user
        bot.send_message(chat_id, "Error: Track not found on Spotify.")
        return

    # Search for the track on YouTube Music
    search_results = ytmusic.search(f"{track_name_spotify} {artist_name_spotify}", filter="songs")


    if search_results:
        # Check similarity between Spotify info and the first result on YT
        first_result = search_results[0]
        track_name_ytmusic = first_result['title']
        artist_name_ytmusic = first_result['artists'][0]['name']

        similarity = calculate_similarity(f"{track_name_spotify} {artist_name_spotify}", f"{track_name_ytmusic} {artist_name_ytmusic}")
        # If the first track is mostly similar, send it to the user
        if similarity >= 80:  # threshold 80
            video_id = first_result['videoId']
            youtube_music_url = f"https://music.youtube.com/watch?v={video_id}"
            bot.send_message(chat_id, f"YouTube Music URL: {youtube_music_url}")
        # Else, send a menu where the user can choose between the first three results
        else:
            # Clear the existing keyboard
            markup.keyboard = []

            # Maximum length for the button text
            max_length = 40
            # Gets the first three results and creates buttons for the menu
            for index, result in enumerate(search_results[:3], start=1):
                if result['resultType'] == 'song':
                    title = result['title']
                    artist = result['artists'][0]['name']
                    album = result['album']['name']
                    video_id = result['videoId']
                    youtube_music_url = f"https://music.youtube.com/watch?v={video_id}"

                    # Create a button text
                    song_info = f"{title} - {artist} - {album}"
                    # If the text it's too long, truncate it
                    song_info = song_info[:max_length] + '...' if len(song_info) > max_length else song_info

                    # Create a custom keyboard button for each result
                    callback_data = f"result_{index}_{youtube_music_url}"
                    button_text = f"{song_info}"
                    button = telebot.types.InlineKeyboardButton(
                        text=button_text,
                        callback_data=callback_data
                    )

                    markup.add(button)

            # Send a single message with all buttons
            if len(markup.keyboard) > 0:
                bot.send_message(chat_id, "Select a song:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "No results found on YouTube Music.")
# Callback when the user chooses a song, it returns the selected YTMusic link for that track
@bot.callback_query_handler(func=lambda call: call.data.startswith('result_'))
def handle_callback_query(call):
    chat_id = call.message.chat.id
    callback_data = call.data.split('_')
    if len(callback_data) == 3:
        youtube_music_url = callback_data[2]
        bot.send_message(chat_id, f"YouTube Music URL: {youtube_music_url}")

bot.polling()
