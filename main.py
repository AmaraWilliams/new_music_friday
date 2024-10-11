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
SCOPE = "user-library-read playlist-modify-private playlist-modify-public"
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
        print ("Found cached token!")
        access_token = token_info['access_token']
    else:
        url = request.url
        code = spotify.parse_response_code(url)
        if code:
            print ("Found Spotify auth code in Request URL! Trying to get valid access token...")
            token_info = spotify.get_access_token(code)
            access_token = token_info['access_token']

    if not access_token:
        return htmlForLoginButton()
    print("Access token avaliable! Trying to get user info...")
    sp = spotipy.Spotify(access_token)
    results = spotify.current_user()
    return results
    
def htmlForLoginButton():
    auth_url = getSPOauthURI()
    htmlLoginButton = "<a href='" + auth_url + ">Login to Spotify</a>"
    return htmlForLoginButton

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


def create_nmf_playlist(vibe, style):
    if PLAYLIST_ID == None:
        print("This playlist does not exist!")
        return None
    dict = style + "_dict"
    if dict == "key_dict":
        dict = key_dict
    elif dict == "tempo_dict":
        dict = tempo_dict
    started = False
    if vibe == "CHILL":
        for item in dict:
          add_to_playlist(dict, item, started)
          started = True
    else:
        for item in reversed(dict):
            add_to_playlist(dict, item, started)
            started = True
    
def add_to_playlist(dict, item, started):
    if dict[item] != []:
        uri_dict = {"uris":dict[item]}
        if started:
            spotify.user_playlist_add_tracks(USERNAME,PLAYLIST_ID, uri_dict["uris"]) 
        else:
            spotify.user_playlist_replace_tracks(USERNAME, PLAYLIST_ID, uri_dict["uris"])
            spotify.user_playlist_change_details(USERNAME, PLAYLIST_ID, playlist_name, description=description)

def create_nmf_list():
    nmf_list= []
    tracks = spotify.current_user_saved_tracks(limit=50)["items"]
    for track in tracks:
        add_date = track['added_at']
        track_id = track['track']['id']
        uri = track['track']['uri']
        key = spotify.audio_analysis(track_id)['track']['key']
        tempo = spotify.audio_analysis(track_id)['track']['tempo']
        track = Track(track_id, uri, add_date, key, tempo)
        if within_week(add_date) == -1:
            continue
        if not within_week(add_date):
            break
        nmf_list.append(track)
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

def sort_tempo(tempo_dict, track):
    if track.tempo <= 40:
        tempo_dict["grave"].append(track.uri)
    if track.tempo > 40 and track.tempo <= 45:
        tempo_dict["lento"].append(track.uri)
    if track.tempo > 45 and track.tempo <= 50:
        tempo_dict["largo"].append(track.uri)
    if track.tempo > 50 and track.tempo <= 65:
        tempo_dict["adagio"].append(track.uri)
    if track.tempo > 65 and track.tempo <= 69:
        tempo_dict["adagietto"].append(track.uri)
    if track.tempo > 69 and track.tempo <= 77:
        tempo_dict["andante"].append(track.uri)
    if track.tempo > 77 and track.tempo <= 97:
        tempo_dict["moderato"].append(track.uri)
    if track.tempo > 97 and track.tempo <= 109:
        tempo_dict["allegretto"].append(track.uri)
    if track.tempo > 109 and track.tempo <= 132:
        tempo_dict["lento"].append(track.uri)
    if track.tempo > 132 and track.tempo <= 140:
        tempo_dict["vivace"].append(track.uri)
    if track.tempo > 140 and track.tempo <= 177:
        tempo_dict["presto"].append(track.uri)
    if track.tempo >= 178:
        tempo_dict["prestissimo"].append(track.uri)
    return tempo_dict

def audio_analysis_algo():
    key_dict = {
        0:[],
        1:[],
        2:[],
        3:[],
        4:[],
        5:[],
        6:[],
        7:[],
        8:[],
        9:[],
        10:[],
        11:[]
    }
    tempo_dict = {
        "grave":[],
        "lento":[],
        "largo":[],
        "adagio":[],
        "adagietto":[],
        "andante":[],
        "moderato":[],
        "allegretto":[],
        "vivace":[],
        "presto":[],
        "prestissimo":[]
    }

    for track in nmf_list:
       
        key_dict[track.key].append(track.uri)
        tempo_dict = sort_tempo(tempo_dict, track)
    return key_dict, tempo_dict



run(host='', port=8080)   

print("New Music Friday made easy")


while not quit_program:
    vibe = str(input("Type 'chill' or 'hype' ")).upper()
    style = str(input("Type 'key' or 'tempo' ")).lower()
    print("Creating your NMF...")
    today = datetime.date.today()
    playlist_name = "This Week On NMF..."
    description = "Vibes = " + vibe + " in terms of " + style + " this week :^)"
    friday_of_last_week = get_friday(today)
    nmf_list = create_nmf_list()
    key_dict, tempo_dict = audio_analysis_algo()
    create_nmf_playlist(vibe, style)
    print("--Successfully created your NMF! Go jam out!--")
    break
        