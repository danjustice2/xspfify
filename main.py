# -*- coding: utf-8 -*-

import codecs
import requests
from xml.sax.saxutils import escape
import re
import logging
import os
import json
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import argparse

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REDIRECT_URI = 'https://example.org/callback' # Set your redirect URI
SPOTIFY_BASE_URL = "https://api.spotify.com"

# Maximum 50. This is how many playlists the script will request from Spotify at a time. All your playlists will be saved by looping through the requests untill all playlists have been received.
PLAYLIST_LIMIT = 50

# This is a soft limit for how long exported playlists should be. They will still be exported, but a warning will be displayed in the console. I'm not sure what the reason for including this in the original project was.
SONG_LIMIT = 100

# The output path for the playlists.
OUTPUT_PATH = os.path.expanduser('~/Playlists')

# For making sure the file names of the playlists don't cause issues.
SANITIZER = re.compile('[a-zA-Z ()0-9]+')

# Function to set up environment variables for Spotify credentials
def setup_environment():
    print("You can create your app and get your client ID and secret at: https://developer.spotify.com/dashboard")
    client_id = input("Enter your Spotify Client ID: ")
    client_secret = input("Enter your Spotify Client Secret: ")
    global CLIENT_ID, CLIENT_SECRET
    CLIENT_ID = client_id
    CLIENT_SECRET = client_secret

# Authenticate and get token
def authenticate_spotify():
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope="playlist-read-private,user-library-read")
    token_info = sp_oauth.get_access_token()
    return token_info['access_token']

def get_auth_header():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + access_token
    }

def get_playlists(limit=PLAYLIST_LIMIT, offset=0):
    url = SPOTIFY_BASE_URL + f'/v1/me/playlists?limit={limit}&offset={offset}'
    headers = get_auth_header()
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Unable to fetch playlists. Status code: {response.status_code}, Message: {response.json()['error']['message']}")
        return []
    logging.info("Fetched playlist data.")
    return response.json()

def get_my_playlists():
    offset = 0
    playlists_data = get_playlists()
    if not playlists_data:
        return []
    total = playlists_data['total']
    limit = PLAYLIST_LIMIT
    my_lists = []
    while offset < total:
        playlists = get_playlists(offset=offset, limit=limit)
        for p in playlists['items']:
            my_lists.append({
                'name': p['name'],
                'id': p['id'],
                'length': p['tracks']['total']
            })
        offset += limit
    logging.info(f"Collected {len(my_lists)} playlists.")
    return my_lists

def get_playlist_tracks(playlist_id):
    url = SPOTIFY_BASE_URL + f'/v1/playlists/{playlist_id}/tracks'
    headers = get_auth_header()
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Unable to fetch tracks for playlist {playlist_id}. Status code: {response.status_code}, Message: {response.json()['error']['message']}")
        return []
    logging.info(f"Fetched tracks for playlist {playlist_id}.")
    tracks_full = response.json()
    tracks = []
    for t in tracks_full['items']:
        tr = t['track']
        tracks.append({
            'title': tr['name'],
            'artist': tr['artists'][0]['name'],
            'album': tr['album']['name']
        })
    return tracks

def get_saved_tracks(limit=50, offset=0):
    url = SPOTIFY_BASE_URL + f'/v1/me/tracks?limit={limit}&offset={offset}'
    headers = get_auth_header()
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Unable to fetch saved tracks. Status code: {response.status_code}, Message: {response.json()['error']['message']}")
        return []
    logging.info(f"Fetched saved tracks.")
    return response.json()

def get_saved_tracks_list():
    offset = 0
    saved_tracks_data = get_saved_tracks()
    if not saved_tracks_data:
        return []
    total = saved_tracks_data['total']
    limit = 50
    saved_tracks = []
    while offset < total:
        tracks_data = get_saved_tracks(offset=offset, limit=limit)
        for t in tracks_data['items']:
            tr = t['track']
            saved_tracks.append({
                'title': tr['name'],
                'artist': tr['artists'][0]['name'],
                'album': tr['album']['name']
            })
        offset += limit
    logging.info(f"Collected {len(saved_tracks)} saved tracks.")
    return saved_tracks

def get_track_xspf_fragment(track_info, omit_album=True):
    ret_str = "<track>"
    if track_info['artist']:
        ret_str += "<creator>" + escape(track_info['artist']) + "</creator>"
    if track_info['album'] and not omit_album:
        ret_str += "<album>" + escape(track_info['album']) + "</album>"
    if track_info['title']:
        ret_str += "<title>" + escape(track_info['title']) + "</title>"
    ret_str += "</track>"
    return ret_str

def convert_spotify_playlist_to_xspf(playlist_id, omit_album=True):
    tracks_info = get_playlist_tracks(playlist_id)
    xspf = """<?xml version="1.0" encoding="UTF-8"?><playlist version="1" xmlns="http://xspf.org/ns/0/"><trackList>"""
    for track_info in tracks_info:
        xspf += get_track_xspf_fragment(track_info, omit_album=omit_album)
    xspf += """</trackList></playlist>"""
    logging.info(f"Converted playlist {playlist_id} to XSPF format.")
    return xspf

def convert_saved_tracks_to_xspf(omit_album=True):
    tracks_info = get_saved_tracks_list()
    xspf = """<?xml version="1.0" encoding="UTF-8"?><playlist version="1" xmlns="http://xspf.org/ns/0/"><trackList>"""
    for track_info in tracks_info:
        xspf += get_track_xspf_fragment(track_info, omit_album=omit_album)
    xspf += """</trackList></playlist>"""
    logging.info("Converted saved tracks to XSPF format.")
    return xspf

def get_track_details(track_uri):
    url = SPOTIFY_BASE_URL + f'/v1/tracks/{track_uri}'
    headers = get_auth_header()
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Unable to fetch track details for {track_uri}. Status code: {response.status_code}, Message: {response.json()['error']['message']}")
        return {}
    return response.json()

def get_basic_track_details(track_uri):
    json = get_track_details(track_uri)
    if not json:
        return {}
    return {
        'artist': json['artists'][0]['name'],
        'title': json['name'],
        'album': json['album']['name']
    }

def write_playlist_to_xspf_file(playlist_id, filename):
    xspf = convert_spotify_playlist_to_xspf(playlist_id)
    path = os.path.join(OUTPUT_PATH, filename + ".xspf")
    with codecs.open(path, "w", "utf-8") as f:
        f.write(xspf)
    logging.info(f"Wrote playlist {playlist_id} to file {path}.")

def write_saved_tracks_to_xspf_file(filename):
    xspf = convert_saved_tracks_to_xspf()
    path = os.path.join(OUTPUT_PATH, filename + ".xspf")
    with codecs.open(path, "w", "utf-8") as f:
        f.write(xspf)
    logging.info(f"Wrote saved tracks to file {path}.")

def make_filename(text):
    return ''.join(SANITIZER.findall(text))

def backup_playlists_to_xspf():
    playlists = get_my_playlists()
    if not playlists:
        logging.info("No playlists found to back up.")
        return
    for playlist in playlists:
        write_playlist_to_xspf_file(playlist['id'], make_filename(playlist['name']))
        if playlist['length'] <= SONG_LIMIT:
            logging.info(f"Backed up playlist: {playlist['name']}")
        else:
            logging.warning(f"Backed up playlist over the limit of {SONG_LIMIT} tracks: {playlist['name']}")

# Main script execution
if __name__ == "__main__":
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    setup_environment()
    try:
        access_token = authenticate_spotify()
        save_songs = input("Do you want to back up your saved songs as well? (y/N): ").strip().lower()
        if save_songs == 'y':
            write_saved_tracks_to_xspf_file("SavedTracks")
        backup_playlists_to_xspf()
        logging.info("Backup process completed.")
    except Exception as e:
        logging.error(f"Failed to authenticate with Spotify. Error: {e}")
        setup_environment()
        access_token = authenticate_spotify()
        save_songs = input("Do you want to back up your saved songs as well? (y/N): ").strip().lower()
        if save_songs == 'y':
            write_saved_tracks_to_xspf_file("SavedTracks")
        backup_playlists_to_xspf()
        logging.info("Backup process completed after re-authentication.")