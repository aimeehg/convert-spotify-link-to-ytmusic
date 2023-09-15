import telebot
import re  # Import the 're' module for regular expressions
from os import environ as env
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from ytmusicapi import YTMusic

# Load environment variables
load_dotenv()

# Initialize Spotify and YouTube Music APIs
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
ytmusic = YTMusic()

# Initialize Telegram bot
bot_token = env.get("BOT_TOKEN")  # Replace with your bot token
bot = telebot.TeleBot(bot_token)

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

    # Get track information from Spotify
    track_info = sp.track(track_id)
    track_name = track_info['name']
    artist_name = track_info['artists'][0]['name']
    album_name = track_info['album']['name']

    # Search for the track on YouTube Music
    search_results = ytmusic.search(f"{track_name} {artist_name} {album_name}", filter="songs")

    if search_results:
        first_result = search_results[0]

        if first_result['resultType'] == 'song':
            video_id = first_result['videoId']
            youtube_music_url = f"https://music.youtube.com/watch?v={video_id}"
            bot.send_message(chat_id, f"YouTube Music URL: {youtube_music_url}")
        else:
            bot.send_message(chat_id, "The first result is not a song.")
    else:
        bot.send_message(chat_id, "No results found on YouTube Music.")

bot.polling()