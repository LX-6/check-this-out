import requests, json
import spotipy
import datetime
import psycopg2
import base64

######################
# CREDENTIALS FLOW  #
#####################

#Authorization of application with spotify
#Return auth url
def app_authorization(client_id, redirect_uri, scope, state, spotify_auth_url):
    url_args = "client_id=" + client_id + "&response_type=code&redirect_uri=" + redirect_uri + "&scope=" + scope + "&state=" + state
    auth_url = spotify_auth_url + "?" + url_args
    return auth_url

#Return access token and refresh token
def get_access_token(redirect_uri, client_id, client_secret, spotify_token_url, auth_token):

    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": redirect_uri
    }
    clients = client_id + ":" + client_secret
    base64encoded = base64.urlsafe_b64encode(clients.encode("utf-8"))
    base64encoded_string = base64encoded.decode("utf-8")
    headers = {"Authorization": "Basic " + base64encoded_string}
    post_request = requests.post(spotify_token_url, data=code_payload, headers=headers)
    response_data = json.loads(post_request.text)

    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]

    #Use the access token to access Spotify API
    authorization_header = {"Authorization":"Bearer " + str(access_token)}
    return authorization_header, refresh_token

#Take refresh token and return valid access token
def get_refreshed_token(refresh_token, client_id, client_secret, refresh_url):

    code_payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    clients = client_id + ":" + client_secret
    base64encoded = base64.urlsafe_b64encode(clients.encode("utf-8"))
    base64encoded_string = base64encoded.decode("utf-8")
    headers = {"Authorization": "Basic " + base64encoded_string}
    post_request = requests.post(refresh_url, data=code_payload, headers=headers)
    response_data = json.loads(post_request.text)

    print(response_data)

    access_token = response_data["access_token"] 

    #Use the access token to access Spotify API
    authorization_header = {"Authorization":"Bearer " + str(access_token)}
    return authorization_header


######################
# LOGICAL FUNCTIONS #
#####################

#Return list of followed artists id
def followed_list(token):
    list_followed_artists_name = []
    list_followed_artists_id = []
    #Auth with token
    try:
        sp = spotipy.Spotify(auth=token)
    except:
        return "Woopsie, I have an issue :s"

    #Ask for the first 50 followed artists
    results = sp.current_user_followed_artists(limit=50)
    total = results['artists']['total']
    #Count loop number needed to have all the followed artists
    loop_count = int(total / 50)
    if total % 50 != 0:
        loop_count += 1
    #Browse results to append artists name & id to the lists
    for artist in results['artists']['items']:
        list_followed_artists_name.append(artist['name'])
        list_followed_artists_id.append(artist['id'])

    #Do the trick until all the followed artists are appended to the lists
    if loop_count > 1:
        for i in range(0, loop_count-1):
            last_artist_id = list_followed_artists_id[-1]
            results = sp.current_user_followed_artists(limit=50, after=last_artist_id)
            total = results['artists']['total']
            for artist in results['artists']['items']:
                list_followed_artists_name.append(artist['name'])
                list_followed_artists_id.append(artist['id'])
    
    return list_followed_artists_id

#Return string with all the new releases per artists
def new_release(token, list_artist):
    #If the user doesn't follow any artist
    if not list_artist:
        returned_string = 'It seems you do not follow any artist on Spotify\nSee this to know how to : https://support.spotify.com/us/using_spotify/features/how-do-i-follow-unfollow-friends-and-artists-on-spotify/'
    else:
        today = datetime.date.today()
        returned_album = ''
        returned_single = ''
        returned_feat = ''
        #Auth with token
        try:
            sp = spotipy.Spotify(auth=token)
        except:
            print("Can't get token")
            return

        today_minus = today - datetime.timedelta(days=7)
        #Browse followed artists list
        for id_artist in list_artist:
            all_albums = sp.artist_albums(id_artist)
            #Browse all artist albums
            for album in all_albums['items']:
                try:
                    #Get the album release date
                    release_date = datetime.datetime.strptime(album['release_date'], "%Y-%m-%d").date()
                except:
                    #Some album have different date typo
                    release_date = datetime.datetime.strptime(album['release_date'], "%Y").date()
                if release_date > today_minus and album['album_type'] != 'compilation' and album['artists'][0]['name'] != 'Various Artists':
                    #We add the release type, the artist name & the release date
                    if album['album_group'] == 'appears_on':
                        artist = sp.artist(id_artist)
                        returned_feat += "[Feat] " + artist['name'] + " appears on " + album['name'] + " of " + album['artists'][0]['name'] + " released on " + album['release_date'] + "\n"
                    elif album['album_type'] == 'album':
                        returned_album += "[Album] " + album['artists'][0]['name'] + " released " + album['name'] + " on " + album['release_date'] + "\n"
                    else:
                        returned_single += "[Single] " + album['artists'][0]['name'] + " released " + album['name'] + " on " + album['release_date'] + "\n"
        returned_string = returned_album + returned_single + returned_feat
    if len(returned_string) > 2000:
        returned_string = 'The list is to long to send it through messenger message sorry :/'
    return returned_string

#Return top user artists
def top_artist(token, timing):
    #Auth with token
    try:
        sp = spotipy.Spotify(auth=token)
    except:
        return "Woopsie, I have an issue :s"
    
    returned_string = ''
    
    artists = sp.current_user_top_artists(limit=10, time_range=timing)
    for artist in artists['items']:
        returned_string += artist['name'] + "\n"

    return returned_string

#Return top user track
def top_track(token, timing):
    #Auth with token
    try:
        sp = spotipy.Spotify(auth=token)
    except:
        return "Woopsie, I have an issue :s"
    
    returned_string = ''
    
    tracks = sp.current_user_top_tracks(limit=10, time_range=timing)
    for track in tracks['items']:
        returned_string += track['name'] + "\n"

    return returned_string

#Create playlist & return the playlist uri
def create_weekly_playlist(token):
    
    #Auth with token
    try:
        sp = spotipy.Spotify(auth=token)
    except:
        return "Woopsie, I have an issue :s"

    #Create weekly playlist
    user_id = sp.current_user()['id']
    name = "CTO week " + str(datetime.date.today().isocalendar()[1])
    response = sp.user_playlist_create(user_id, name, public=False, description='Generate by Check this out app here : https://m.me/106434560955345')

    return response['uri']

#Return new releases list
def get_new_releases_list(token, list_artist):
    #Auth with token
    try:
        sp = spotipy.Spotify(auth=token)
    except:
        return "Woopsie, I have an issue :s"

    today = datetime.date.today()
    returned_list = list()
    triplet_appended_list = list()
    
    today_minus = today - datetime.timedelta(days=7)
    #Browse followed artists list
    for id_artist in list_artist:
        all_albums = sp.artist_albums(id_artist)
        #Browse all artist albums
        for album in all_albums['items']:
            try:
                #Get the album release date
                release_date = datetime.datetime.strptime(album['release_date'], "%Y-%m-%d").date()
            except:
                #Some album have different date typo
                release_date = datetime.datetime.strptime(album['release_date'], "%Y").date()
            #We skip compilation album because basically it's full of garbage
            if release_date > today_minus and album['album_type'] != 'compilation' and album['artists'][0]['name'] != 'Various Artists':
                #Get back all album data
                response = sp.album_tracks(album['uri'])

                #Browse each album's track
                for track in response['items']:
                    #Create a triplet with artist name, album name & track name
                    triplet = list()
                    triplet.append(album['artists'][0]['name'])
                    triplet.append(album['name'])
                    triplet.append(track['name'])

                    #Append if not already in the list
                    if track['uri'] not in returned_list and triplet not in triplet_appended_list:
                        #If it is a featuring we want to only add the tracks with the followed artist
                        if album['album_group'] == 'appears_on':
                            for name in track['artists']:
                                #If at least one followed artist is in the track artists list
                                if name['id'] in list_artist:
                                    #Track appended to returned list
                                    returned_list.append(track['uri'])
                                    #Triplet appended to list
                                    triplet_appended_list.append(triplet)
                                    #Quit the loop to avoid adding multiple times the track if several followed artists are on the track
                                    break
                        else:
                            #Track appended to returned list
                            returned_list.append(track['uri'])
                            #Triplet appended to list
                            triplet_appended_list.append(triplet)
            
    return returned_list

#Add new releases in selected playlist
def add_song_to_playlist(token, playlist_uri, releases_list):

    #Auth with token
    try:
        sp = spotipy.Spotify(auth=token)
    except:
        return "Woopsie, I have an issue :s"

    user_id = sp.current_user()['id']
    
    releases_list_length = len(releases_list)

    #If the list contains more than 100 tracks
    if (releases_list_length/100) > 1:
        start = 0
        #We are going to add tracks in packs of 100
        while (releases_list_length/100) > 1:
            #We add 100 tracks
            sp.user_playlist_add_tracks(user_id, playlist_uri, releases_list[start:start+100], None)
            start += 100
            releases_list_length -= 100

        #Number of tracks remained to add (under 100)
        if releases_list_length % 100 != 0:
            #We add the rest of the list as it is less than 100 tracks
            sp.user_playlist_add_tracks(user_id, playlist_uri, releases_list[start:], None)
    
    else:
        sp.user_playlist_add_tracks(user_id, playlist_uri, releases_list, None)

#Create a new playlist with new releases from followed artists
def weekly_playlist_process(token):
    try:
        playlist_uri = create_weekly_playlist(token)
        releases_list = get_new_releases_list(token, better_followed_list(token))
        add_song_to_playlist(token, playlist_uri, releases_list)
        returned_string = "Your weekly playlist has been created successfully!\nHave a good week :-)"
    except:
        returned_string = "An issue occurs while creating your weekly playlist :'(\nNevermind have a good week :-)"

    return returned_string

#Create the weekly playlist for each user that enabled the mode in DB 
def auto_weekly_playlist(db_url, cli_id, cli_secret, rfresh_url, acc_token):
    #Connect with the DB
    conn = psycopg2.connect(db_url, sslmode='require')
    cur = conn.cursor()
    #Select user that enabled the auto playlist mode
    cur.execute("SELECT refreshtoken, messengerid FROM checkthisout WHERE autoplaylist = 'true';")
    #Retrieve sql request results
    sql_results = cur.fetchall()
    cur.close()
    conn.close()

    for user in sql_results:
        #Get fresh token
        token = get_refreshed_token(user[0][0], cli_id, cli_secret, rfresh_url)
        #Create playlist
        message = weekly_playlist_process(token)
        #Send message to warn the user
        #send_messenger_message(message, acc_token, user[0][1])
        print(message)

#Send message to a specific user named after user_id
def send_messenger_message(message, access_token, user_id):
    response = {
        'recipient': {'id': user_id},
        'message': {'text': message}
    }
    r = requests.post('https://graph.facebook.com/v8.0/me/messages/?access_token=' + access_token, json=response)

#######################
# DATABASE FUNCTIONS #
#####################

#Search if messenger_id exist in DB and if so, return the refresh_token associated, if not return None
def search_user_db(database_url, messenger_id):
    #Set returned variable
    ret = None

    #Connect with the DB
    conn = psycopg2.connect(database_url, sslmode='require')
    cur = conn.cursor()
    cur.execute('SELECT refreshtoken FROM checkthisout WHERE messengerid=%s;', [messenger_id])
    #Retrieve sql request results
    sql_results = cur.fetchall()
    cur.close()
    conn.close()

    #Try to get refresh_token back
    try:
        ret = sql_results[0][0]
    #If list is empty
    except:
        ret = None

    return ret

#Store refresh_token in DB
def store_db(refresh_token, messenger_id, database_url):
    #Connect with the DB
    conn = psycopg2.connect(database_url, sslmode='require')
    cur = conn.cursor()
    cur.execute("INSERT INTO checkthisout (refreshtoken, messengerid, autoplaylist) VALUES (%s, %s, 'true');", (refresh_token, int(messenger_id)))
    #Commit changes
    conn.commit()
    cur.close()
    conn.close()

#Change state of auto weekdly playlist attribute
def change_autoplaylist_attribute(database_url, messenger_id, state):
    #Connect with the DB
    conn = psycopg2.connect(database_url, sslmode='require')
    cur = conn.cursor()
    cur.execute("UPDATE checkthisout SET autoplaylist = %s WHERE messengerid = %s;", (state, int(messenger_id)))
    #Commit changes
    conn.commit()
    cur.close()
    conn.close()