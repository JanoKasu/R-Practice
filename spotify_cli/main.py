import os
import time
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, redirect, request, session, url_for

load_dotenv()

app = Flask(__name__)
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = os.urandom(24)


@app.route('/')
def login():
	auth_url = create_spotify_oauth().get_authorize_url()
	return redirect(auth_url)


@app.route("/redirect")
def redirect_page():
	session.clear()
	code = request.args.get('code')
	token_info = create_spotify_oauth().get_access_token(code)
	session['token_info'] = token_info
	return redirect(url_for('save_discover_weekly', _external = True))


@app.route("/saveDiscoverWeekly")
def save_discover_weekly():
	try:
		token_info = get_token()
	except():
		print('User not logged in.')
		return redirect('/')
	
	sp = spotipy.Spotify(auth = token_info['access_token'])
	user_id = sp.current_user()['id']
	current_playlists =  sp.current_user_playlists()['items']
	discover_weekly_id = None
	saved_weekly_id = None

	for playlist in current_playlists:
		print(playlist['name'])
		if playlist['name'] == 'Discover Weekly':
			discover_weekly_id = playlist['id']
		if playlist['name'] == 'Saved Weekly':
			saved_weekly_id = playlist['id']

	if not discover_weekly_id:
		return 'Discover Weekly not found'
	
	if not saved_weekly_id:
		new_playlist = sp.user_playlist_create(user_id, 'Saved Weekly', True)
		saved_weekly_id = new_playlist['id']
	
	discover_weekly_playlist = sp.playlist_items(discover_weekly_id)
	song_uris = []
	for song in discover_weekly_playlist['items']:
		song_uri = song['track']['uri']
		song_uris.append(song_uri)
		
	sp.user_playlist_add_tracks(user_id, saved_weekly_id, song_uris)

	return 'Discover Weekly songs added successfully'


def get_token():
	token_info = session.get('token_info', None)
	if not token_info:
		redirect(url_for('/', _external = False))

	now = int(time.time())

	is_expired = token_info['expires_at'] - now < 60
	if is_expired:
		spotify_oauth = create_spotify_oauth()
		token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

	return token_info


def create_spotify_oauth():
	return SpotifyOAuth(
		client_id = os.getenv('SPOTIPY_CLIENT_ID'),
		client_secret = os.getenv('SPOTIPY_CLIENT_SECRET'),
		redirect_uri = url_for('redirect_page', _external = True),
		scope = "user-library-read playlist-read-private playlist-modify-private playlist-modify-public"
	)


app.run(debug = True)