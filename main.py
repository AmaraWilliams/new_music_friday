import os
from bottle import run, route, request
from dotenv import load_dotenv
from pynput import keyboard
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import datetime
from datetime import timedelta
from Track import Track
import logging

logging.basicConfig(filename="logs.log", filemode="w", level=logging.INFO)

load_dotenv()
SPOTIFY_CREATE_PLAYLIST_URL = os.getenv('SPOTIFY_PLAYLIST_URI')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
REDIRECT_URL = 'http://localhost:3000'
PLAYLIST_ID = os.getenv('PLAYLIST_ID')
CACHE = '.spotipyoauthcache'
PORT = 8080
USERNAME = os.getenv('SPOTIFY_USERNAME')
SCOPE = "user-library-read playlist-modify-private playlist-modify-public playlist-read-private"
spotify = spotipy.Spotify (
    auth_manager=SpotifyOAuth (
        scope=SCOPE,
        redirect_uri=REDIRECT_URL,
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        username=USERNAME,
        #token = spotipy.util.prompt_for_user_token(USERNAME, SCOPE)
    )
    
)

@route('/')
def index():
    access_token = ''
    token_info = spotify.get_cached_token()
    if token_info:
        print("Found cached token!")
        # Check if token is expired (this can be done by checking token_info['expires_at'])
        if token_info['expires_at'] < time.time():
            print("Token expired! Refreshing...")
            token_info = spotify.refresh_access_token(token_info['refresh_token'])
        access_token = token_info['access_token']
    else:
        print("No cached token found. Initiating authentication flow.")
        url = request.url
        code = spotify.parse_response_code(url)
        if code:
            print("Found Spotify auth code in Request URL! Trying to get valid access token...")
            token_info = spotify.get_access_token(code)
            access_token = token_info['access_token']

    # token_info = spotify.get_cached_token()
    # if token_info:
    #     print ("Found cached token!")
    #     access_token = token_info['access_token']
    # else:
    #     url = request.url
    #     code = spotify.parse_response_code(url)
    #     if code:
    #         print ("Found Spotify auth code in Request URL! Trying to get valid access token...")
    #         token_info = spotify.get_access_token(code)
    #         access_token = token_info['access_token']

    if not access_token:
        return htmlForLoginButton()
    print("Access token avaliable! Trying to get user info...")
    sp = spotipy.Spotify(access_token)
    results = spotify.current_user()
    return results
    
def htmlForLoginButton():
    auth_url = getSPOauthURI()
    htmlLoginButton = f"<a href='{auth_url}'>Login to Spotify</a>"
    return htmlLoginButton

    # auth_url = getSPOauthURI()
    # htmlLoginButton = "<a href='" + auth_url + ">Login to Spotify</a>"
    # return htmlForLoginButton

def getSPOauthURI():
    auth_url = spotify.get_authorize_url()
    return auth_url

quit_program = False
ready = False

def on_release(key):
        if key == keyboard.Key.esc:
            listener.stop()
            return False

    #sets global variables for "hot keys" ESC and ENTER
def on_press(key):
    if key == keyboard.Key.esc:
        global quit_program
        quit_program = True
        print("\nQuitting Program. Press ENTER...")
    
    if key == keyboard.Key.enter:
        global ready
        ready = True

listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release)
listener.start()


def create_nmf_playlist(nmf_list):
    if PLAYLIST_ID == None:
        print("This playlist does not exist!")
        return None
    if nmf_list != None:
        logging.info("replacing tracks")
        spotify.playlist_replace_items(PLAYLIST_ID, nmf_list)
        spotify.playlist_change_details(PLAYLIST_ID, description=description)
    
def create_nmf_list():
    nmf_list= []
    tracks = spotify.current_user_saved_tracks(limit=50)["items"]
    for track in tracks:
        add_date = track['added_at']
        track_id = track['track']['id']
        uri = track['track']['uri']
        artists = track['track']['artists']
        artist_list = []
        for artist in artists:
            artist_list.append(artist['uri'])
        track = Track(track_id, uri, add_date, artists)
        if within_week(add_date) == -1:
            continue
        if not within_week(add_date):
            break
        nmf_list.append(track.uri)
        break
    return nmf_list

def get_friday(date):
    """Gets the date of previous Friday"""
    # Subtract the calculated number of days
    friday = date - datetime.timedelta(days=7)
    return friday

def parse_add_date(datetimeAdd):
    date = datetimeAdd.split("T")[0].split("-")
    date = datetime.date(int(date[0]), int(date[1]), int(date[2]))
    return date

def within_week(date):
    date = parse_add_date(date)
    num_days = friday_of_last_week - date
    num_days = abs(num_days.days)
    if num_days == 0:#added before the week started
        return False
    if num_days > 7: #added after the week ended
        return -1
    return True

run(host='', port=8080)   

print("New Music Friday made easy")


while not quit_program:
    description = input("What's the description?: ")
    print("Creating your NMF...")
    today = datetime.date.today()
    friday_of_last_week = get_friday(today)
    nmf_list = create_nmf_list()
    create_nmf_playlist(nmf_list)
    print("--Successfully created your NMF! Go jam out!--")
    break
        