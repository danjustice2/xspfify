#!/usr/bin/python
# -*- coding: utf-8 -*-
import codecs
import requests
from xml.sax.saxutils import escape
import re
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SPOTIFY_BASE_URL = 'https://api.spotify.com'
OAUTH_TOKEN = 'BQAEPRXttVZ9JMlAhVdjApVUWrLdgJWdIiywDxQAH37l2Zreowt5uJOi6wBJVVfdyaBulhrk4JA9zOiNWgSZ35ytUPOEyRsG4xhr9T_PCR3vIonRV9Y' # obtain this at https://developer.spotify.com/console/get-playlist-tracks/
SPOTIFY_USERNAME = '12170631829' # set your username
PLAYLIST_LIMIT = 50
SONG_LIMIT = 100
OUTPUT_PATH = '/home/dan/playlists' # set this to your desired path
SANITIZER = re.compile('[a-zA-Z ()0-9]+')

def get_auth_header():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + OAUTH_TOKEN
    }

def get_playlists(user_id='me', limit=PLAYLIST_LIMIT, offset=0):
    url = SPOTIFY_BASE_URL + f'/v1/users/{user_id}/playlists?limit={limit}&offset={offset}'
    headers = get_auth_header()
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Unable to fetch playlists. Status code: {response.status_code}, Message: {response.json()['error']['message']}")
        return []
    logging.info(f"Fetched playlists for user {user_id}.")
    return response.json()

def get_my_playlists(user_id='me', username=SPOTIFY_USERNAME):
    offset = 0
    playlists_data = get_playlists(user_id)
    if not playlists_data:
        return []
    total = playlists_data['total']
    limit = PLAYLIST_LIMIT
    my_lists = []
    while offset < total:
        playlists = get_playlists(user_id, offset=offset, limit=limit)
        for p in playlists['items']:
            owner = p['owner']['id']
            if owner == username:
                my_lists.append({
                    'name': p['name'],
                    'id': p['id'],
                    'length': p['tracks']['total']
                })
        offset += limit
    logging.info(f"Collected {len(my_lists)} playlists owned by {username}.")
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
    path = OUTPUT_PATH + "/" + filename + ".xspf"
    with codecs.open(path, "w", "utf-8") as f:
        f.write(xspf)
    logging.info(f"Wrote playlist {playlist_id} to file {path}.")

def make_filename(text):
    return ''.join(SANITIZER.findall(text))

def backup_playlists_to_xspf(user_id='me', username=SPOTIFY_USERNAME):
    playlists = get_my_playlists(user_id, username)
    if not playlists:
        logging.info("No playlists found to back up.")
    for playlist in playlists:
        if playlist['length'] <= SONG_LIMIT:
            write_playlist_to_xspf_file(playlist['id'], make_filename(playlist['name']))
            logging.info(f"Backed up playlist: {playlist['name']}")

# Main script execution
if __name__ == "__main__":
    backup_playlists_to_xspf()
    logging.info("Backup process completed.")