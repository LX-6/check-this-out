import requests, json
import spotipy
import datetime
import psycopg2
import base64

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

#Send message to a specific user named after user_id
def send_messenger_message(message, access_token, user_id):
    response = {
        'recipient': {'id': user_id},
        'message': {'text': message}
    }
    r = requests.post('https://graph.facebook.com/v7.0/me/messages/?access_token=' + access_token, json=response)

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

    access_token = response_data["access_token"] 

    #Use the access token to access Spotify API
    authorization_header = {"Authorization":"Bearer " + str(access_token)}
    return authorization_header

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
        #Set
        ret = None

    return ret

#Store refresh_token in DB
def store_db(refresh_token, messenger_id, database_url):
    #Connect with the DB
    conn = psycopg2.connect(database_url, sslmode='require')
    cur = conn.cursor()
    cur.execute("INSERT INTO checkthisout (refreshtoken, messengerid) VALUES (%s, %s);", (refresh_token, int(messenger_id)))
    #Commit changes
    conn.commit()
    cur.close()
    conn.close()