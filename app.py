from flask import Flask, request, Response, redirect, render_template
import requests, json
import random, os
import sys
import argparse
import urllib
import functions
#from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.triggers.cron import CronTrigger
from flask_apscheduler import APScheduler

app = Flask(__name__)
scheduler = APScheduler()
#trigger = CronTrigger(day_of_week='fri', hour=15, minute=10)
#scheduler.add_job(func=functions.auto_weekly_playlist, trigger=trigger, args=[DATABASE_URL,CLIENT_ID,CLIENT_SECRET,SPOTIFY_TOKEN_URL,ACCESS_TOKEN])
scheduler.init_app(app)
scheduler.start()

#Database
DATABASE_URL = os.getenv('DATABASE_URL')

# Facebook env_variables
# token to verify that this bot is legit
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
# token to send messages through facebook messenger
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

# Client Keys
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

#Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = SPOTIFY_API_BASE_URL + "/" + API_VERSION

#Server-side Parameters
REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')
SCOPE = os.getenv('SPOTIPY_SCOPE')

#TO-DO static page to explain the app and redirect to github repo
@app.route("/")
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['GET'])
def webhook_verify():
    if request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge')
    return "Wrong verify token"


#Receive message from messenger & return message depends on what the user choose
@app.route('/webhook', methods=['POST'])
def webhook_action():
    #Set returned variable
    returned_message = 'Something went wrong sorry :('

    data = json.loads(request.data.decode('utf-8'))

    for entry in data['entry']:
        user_id = entry['messaging'][0]['sender']['id']
        #The user sent normal message
        """ try:
            #User message in lower case
            user_message = entry['messaging'][0]['message']['text'].lower()
            #Search for this user_id in DB
            search_returned = functions.search_user_db(DATABASE_URL, user_id)
            #If user_id is not in the DB
            if not search_returned:
                #Return authorize endpoint the user needs to log in
                returned_message = "Hello :-) First of all I need to access your Spotify data so you have to authorize me here :\n" + functions.app_authorization(CLIENT_ID, REDIRECT_URI, SCOPE, user_id, SPOTIFY_AUTH_URL)
            #Send functions menu to the user
            elif 'menu' in user_message:
                returned_message = "start : Enabled auto weekly playlist mode, you will receive a new playlist with fresh tracks every monday directly on your Spotify!\nstop : Disabled auto weekly playlist mode\n\ntop artist [short | medium | long] : get your current top artists for time range selected\ntop track [short | medium | long] : get your current top tracks for time range selected"
            #If user_id is in the DB
            else:
                #Different cases
                if 'update' in user_message:
                    #Asking for a new access_token, search_returned == refresh_token
                    #authorization_header = functions.get_refreshed_token(search_returned, CLIENT_ID, CLIENT_SECRET, SPOTIFY_TOKEN_URL)
                    #Get followed artists list back
                    #list_artist = functions.followed_list(authorization_header)
                    #Return new release list as a string
                    #returned_message = functions.new_release(authorization_header, list_artist)
                    functions.auto_weekly_playlist(DATABASE_URL,CLIENT_ID,CLIENT_SECRET,SPOTIFY_TOKEN_URL,ACCESS_TOKEN)

                #Top artist               
                elif 'top artist' in user_message:
                    choice = ['short', 'medium', 'long']
                    #If user do not send any choice we set by default for medium
                    timing = 'medium_term'

                    #Define choice for top time range
                    for c in choice:
                        if c in user_message:
                            timing = c + '_term'

                    #Asking for a new access_token, search_returned == refresh_token
                    authorization_header = functions.get_refreshed_token(search_returned, CLIENT_ID, CLIENT_SECRET, SPOTIFY_TOKEN_URL)
                    #Return top user artist
                    returned_message = functions.top_artist(authorization_header, timing)
                
                #Top track
                elif 'top track' in user_message:
                    choice = ['short', 'medium', 'long']
                    #If user do not send any choice we set by default for medium
                    timing = 'medium_term'

                    #Define choice for top time range
                    for c in choice:
                        if c in user_message:
                            timing = c + '_term'

                    #Asking for a new access_token, search_returned == refresh_token
                    authorization_header = functions.get_refreshed_token(search_returned, CLIENT_ID, CLIENT_SECRET, SPOTIFY_TOKEN_URL)
                    #Return top user artist
                    returned_message = functions.top_track(authorization_header, timing)
                
                #Enabled auto weekly playlist
                elif 'start' in user_message:

                    functions.change_autoplaylist_attribute(DATABASE_URL, user_id, "true")

                    returned_message = "Auto weekly playlist mode has been enabled.\nYou will receive a new playlist with fresh tracks every monday !\n(Send 'stop' to disabled)"

                #Disabled auto weekly playlist
                elif 'stop' in user_message:

                    functions.change_autoplaylist_attribute(DATABASE_URL, user_id, "false")

                    returned_message = "Auto weekly playlist mode has been disabled.\nYou will NOT receive any new playlist from us ! This will not delete any playlists created previously.\n(Send 'start' to enabled)"
                else:
                    returned_message = "Hello! Welcome on Check this out App :)\nIt's a multifunction Spotify bot\nSend 'menu' to view all functions you can use"

        #The user sent an other type of content than a message
        except:
            returned_message = 'I do not understand what you sent me :( Please send me a normal message' """
        #User message in lower case
        user_message = entry['messaging'][0]['message']['text'].lower()
        #Search for this user_id in DB
        search_returned = functions.search_user_db(DATABASE_URL, user_id)
        #If user_id is not in the DB
        if not search_returned:
            #Return authorize endpoint the user needs to log in
            returned_message = "Hello :-) First of all I need to access your Spotify data so you have to authorize me here :\n" + functions.app_authorization(CLIENT_ID, REDIRECT_URI, SCOPE, user_id, SPOTIFY_AUTH_URL)
        #Send functions menu to the user
        elif 'menu' in user_message:
            returned_message = "start : Enabled auto weekly playlist mode, you will receive a new playlist with fresh tracks every monday directly on your Spotify!\nstop : Disabled auto weekly playlist mode\n\ntop artist [short | medium | long] : get your current top artists for time range selected\ntop track [short | medium | long] : get your current top tracks for time range selected"
        #If user_id is in the DB
        else:
            #Different cases
            if 'update' in user_message:
                #Asking for a new access_token, search_returned == refresh_token
                authorization_header = functions.get_refreshed_token(search_returned, CLIENT_ID, CLIENT_SECRET, SPOTIFY_TOKEN_URL)
                #Get followed artists list back
                list_artist = functions.followed_list(authorization_header)
                #Return new release list as a string
                returned_message = functions.new_release(authorization_header, list_artist)

            #Top artist               
            elif 'top artist' in user_message:
                choice = ['short', 'medium', 'long']
                #If user do not send any choice we set by default for medium
                timing = 'medium_term'

                #Define choice for top time range
                for c in choice:
                    if c in user_message:
                        timing = c + '_term'

                #Asking for a new access_token, search_returned == refresh_token
                authorization_header = functions.get_refreshed_token(search_returned, CLIENT_ID, CLIENT_SECRET, SPOTIFY_TOKEN_URL)
                #Return top user artist
                returned_message = functions.top_artist(authorization_header, timing)
            
            #Top track
            elif 'top track' in user_message:
                choice = ['short', 'medium', 'long']
                #If user do not send any choice we set by default for medium
                timing = 'medium_term'

                #Define choice for top time range
                for c in choice:
                    if c in user_message:
                        timing = c + '_term'

                #Asking for a new access_token, search_returned == refresh_token
                authorization_header = functions.get_refreshed_token(search_returned, CLIENT_ID, CLIENT_SECRET, SPOTIFY_TOKEN_URL)
                #Return top user artist
                returned_message = functions.top_track(authorization_header, timing)
            
            #Enabled auto weekly playlist
            elif 'start' in user_message:

                functions.change_autoplaylist_attribute(DATABASE_URL, user_id, "true")

                returned_message = "Auto weekly playlist mode has been enabled.\nYou will receive a new playlist with fresh tracks every monday !\n(Send 'stop' to disabled)"

            #Disabled auto weekly playlist
            elif 'stop' in user_message:

                functions.change_autoplaylist_attribute(DATABASE_URL, user_id, "false")

                returned_message = "Auto weekly playlist mode has been disabled.\nYou will NOT receive any new playlist from us ! This will not delete any playlists created previously.\n(Send 'start' to enabled)"
            else:
                returned_message = "Hello! Welcome on Check this out App :)\nIt's a multifunction Spotify bot\nSend 'menu' to view all functions you can use"
            
        functions.send_messenger_message(returned_message, ACCESS_TOKEN, user_id)

    return Response(response="EVENT RECEIVED",status=200)

#Logic function sending a message with proper response to messenger user
@app.route('/callback', methods=['GET'])
def callback():
    #Set returned variable
    returned_message = ''

    #Get messenger user_id back
    #If the user accepts to log in
    try:
        user_id = request.args['state']
        try:
            auth_token = request.args['code']
            authorization_header, refresh_token = functions.get_access_token(REDIRECT_URI, CLIENT_ID, CLIENT_SECRET, SPOTIFY_TOKEN_URL, auth_token)

            #Save in DB refresh_token
            functions.store_db(refresh_token, user_id, DATABASE_URL)

            returned_message = "Everything worked fine, you can resend a message"
        except:
            returned_message = "It seems you did not accept to authorize access to the data sets defined in the scopes :(\nYou can't use the app without it.\nWe do not save or sell your personal datas!"
        functions.send_messenger_message(returned_message, ACCESS_TOKEN, user_id) 
        return "You can close this tab and resend message :)"
    except:
        return "You need to send a message to this messenger bot : https://m.me/106434560955345"
        
#Bullsh...privacy pro page :)
@app.route('/privacy', methods=['GET'])
def privacy():
    return "This facebook messenger bot's only purpose is to advertise user for each new album or song release of their favorites artists on Spotify. That's all. We don't use it in any other way."

@scheduler.task('cron', day_of_week='fri', hour=16, minute=6)
def launch_weekly_playlist():
    print("oui")
    functions.auto_weekly_playlist(DATABASE_URL,CLIENT_ID,CLIENT_SECRET,SPOTIFY_TOKEN_URL,ACCESS_TOKEN) 

if __name__ == '__main__':

    #scheduler.add_job(func=test_schedule, trigger=trigger)
    #scheduler.add_job(id ='Scheduled task', func=test_schedule, trigger='interval', seconds=10)
    #scheduler.start()
    #app.run(debug=True, host='0.0.0.0', use_reloader=False)
    app.run(host='0.0.0.0')