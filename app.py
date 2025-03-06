import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import time

class PlaylistAgent:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="user-modify-playback-state user-read-playback-state user-top-read playlist-modify-public"
        ))
        self.user_id = self.sp.current_user()["id"]
    
    def search_artist(self, query):
        results = self.sp.search(q=query, type="artist", limit=5)
        return [(artist["name"], artist["id"]) for artist in results["artists"]["items"]]
    
    def get_top_artists(self):
        results = self.sp.current_user_top_artists(limit=5)
        return [(artist["name"], artist["id"]) for artist in results["items"]]
    
    def get_similar_artists(self, artist_id):
        results = self.sp.artist_related_artists(artist_id)
        return [(artist["name"], artist["id"]) for artist in results["artists"][:5]]
    
    def get_artist_tracks(self, artist_id, filters):
        results = self.sp.artist_top_tracks(artist_id)
        tracks = results["tracks"]
        
        if "popularity" in filters:
            tracks = sorted(tracks, key=lambda x: x["popularity"], reverse=True)
        
        if "release_date" in filters:
            tracks = sorted(tracks, key=lambda x: x["album"]["release_date"], reverse=True)
        
        return [(track["name"], track["id"]) for track in tracks]
    
    def create_playlist(self, name):
        playlist = self.sp.user_playlist_create(self.user_id, name, public=True)
        return playlist["id"]
    
    def add_tracks_to_playlist(self, playlist_id, track_ids):
        self.sp.playlist_add_items(playlist_id, track_ids)
    
    def generate_playlist(self, artist_ids, filters, playlist_name):
        track_list = []
        
        while len(track_list) < 20:  # Limit playlist length
            for artist_id in artist_ids:
                tracks = self.get_artist_tracks(artist_id, filters)
                if tracks:
                    track_list.append(tracks[0][1])  # Pick the first available track
            if len(track_list) >= 20:
                break
        
        playlist_id = self.create_playlist(playlist_name)
        self.add_tracks_to_playlist(playlist_id, track_list)
        print(f"Playlist '{playlist_name}' created successfully!")
    
    def start_live_stream(self, artist_ids, filters):
        print("Starting live stream...")
        track_queue = []
        
        while True:
            for artist_id in artist_ids:
                tracks = self.get_artist_tracks(artist_id, filters)
                if tracks:
                    track_queue.append(tracks[0][1])
                    self.sp.start_playback(uris=[f"spotify:track:{tracks[0][1]}"])
                    print(f"Now playing: {tracks[0][0]}")
                    
                    while True:
                        command = input("Commands: [s]kip, [p]ause, [r]eplay, [q]uit: ")
                        if command == "s":
                            break
                        elif command == "p":
                            self.sp.pause_playback()
                            print("Paused.")
                        elif command == "r":
                            self.sp.start_playback(uris=[f"spotify:track:{track_queue[-1]}"])
                            print(f"Replaying: {tracks[0][0]}")
                        elif command == "q":
                            print("Stopping live stream.")
                            return
                    
                    time.sleep(2)  # Small delay to avoid rapid API calls

# Example Usage
if __name__ == "__main__":
    client_id = "your_spotify_client_id"
    client_secret = "your_spotify_client_secret"
    redirect_uri = "your_redirect_uri"
    
    agent = PlaylistAgent(client_id, client_secret, redirect_uri)
    
    # Example flow
    top_artists = agent.get_top_artists()
    print("Your Top Artists:", top_artists)
    
    artist_choices = [top_artists[0][1], top_artists[1][1]]  # Select top 2 artists
    filters = ["popularity"]  # Example filter
    
    mode = input("Choose mode: [p]laylist or [l]ive stream: ")
    if mode == "p":
        agent.generate_playlist(artist_choices, filters, "My Alternating Playlist")
    elif mode == "l":
        agent.start_live_stream(artist_choices, filters)
