import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build
import os


class YoutubeToSpotify:

    def __init__(self):
        """Initiliaze the API keys and other important variables"""
        self.spotify_client_id = os.environ.get('SPOTIFY_CLIENT_ID')
        self.spotify_client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
        self.scope = 'playlist-modify-public playlist-modify-public'
        self.redirect = 'http://localhost:8000/'
        self.youtube_dev_key = os.environ.get('YOUTUBE_API_KEY')
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=self.spotify_client_id,
                                                            client_secret=self.spotify_client_secret,
                                                            redirect_uri=self.redirect,
                                                            scope=self.scope))
        self.youtube = build('youtube', 'v3', developerKey=self.youtube_dev_key)
        self.username = os.environ.get('SPOTIFY_USERNAME')

    def get_pl_songs(self, playlist_id):
        """Get all song names from a playlist"""
        # If the playlist has more than one page
        nextPageToken = None
        songs = []
        while True:
            # Loop through entire youtube playlist to get the title
            pl_request = self.youtube.playlistItems().list(part='contentDetails',
                                                           playlistId=playlist_id, maxResults=50,
                                                           pageToken=nextPageToken)
            pl_response = pl_request.execute()

            vid_ids = []

            for item in pl_response['items']:
                vid_ids.append(item['contentDetails']['videoId'])

            vid_request = self.youtube.videos().list(part='snippet', id=','.join(vid_ids))

            vid_response = vid_request.execute()

            for video in vid_response['items']:
                # Get the titles of the videos
                vid_title = video['snippet']['title']
                song_title = vid_title.split("(")[0]
                spotify_result = self.sp.search(q=song_title)
                if spotify_result['tracks']['items']:
                    # Add first spotify result for the search
                    songs.append(spotify_result['tracks']['items'][0]['uri'])

            nextPageToken = pl_response.get('nextPageToken')
            if not nextPageToken:
                break
        return songs

    def get_ind_song(self, video_id):
        """Get the song name of an individual video"""
        song = []
        vid_request = self.youtube.videos().list(part='snippet', id=video_id)
        vid_response = vid_request.execute()
        vid_title = vid_response['items'][0]['snippet']['title']
        song_title = vid_title.split("(")[0]

        spotify_result = self.sp.search(q=song_title)
        if spotify_result['tracks']['items']:
            # Add first spotify result for the search
            song.append(spotify_result['tracks']['items'][0]['uri'])
        else:
            print("Song does not exist on spotify")
        return song

    def create_playlist(self):
        """Function to create a playlist to your spotify account"""
        pl_name = input("What do you want to call your spotify playlist? ")
        pl_desc = input("Playlist description: ")
        self.sp.user_playlist_create(self.username, pl_name, public=True, collaborative=False, description=pl_desc)
        sp_playlists = self.sp.user_playlists(self.username, limit=50, offset=0)
        sp_pl_id = sp_playlists['items'][0]['id']
        return sp_pl_id

    def add_songs(self):
        """Add songs to the playlist just created"""
        sp_pl_id = YoutubeToSpotify().create_playlist()
        choice = input("Playlist or video?(P/V) ")
        if choice.lower() == "p":
            id = input("Playlist-ID: ")
            songs = YoutubeToSpotify().get_pl_songs(id)
            self.sp.playlist_add_items(sp_pl_id, songs)
        elif choice.lower() == "v":
            id = input("Video-ID: ")
            song = YoutubeToSpotify().get_ind_song(id)
            self.sp.playlist_add_items(sp_pl_id, song)


if __name__ == '__main__':
    YoutubeToSpotify().add_songs()
