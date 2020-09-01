import audio
import gui
import requests


class Application:
    def __init__(self):
        self.loaded_audio_file: audio.AudioFile = None
        self.gui_top_level_window = None

    def initialize_gui(self):
        self.gui_top_level_window = gui.MainWindow(self)
        self.gui_top_level_window.mainloop()

    def load_file(self, filename):
        try:
            self.loaded_audio_file = audio.AudioFile(filename)
        except ValueError as ve:
            print(ve)
            self.loaded_audio_file = None

    def trim_audio_data(self, start_time, end_time):
        self.loaded_audio_file.trim(start_time, end_time)


class SpotifyDatabaseClient:
    def __init__(self):
        self.client_id = "8b3a3c206aa842fabe7d613257d7dc7f"
        self.client_secret = "8752adcb2f7942918ef14d69a5f49e55"
        self.authorization_token = ""

    def get_authorization_token(self):
        auth_url = 'https://accounts.spotify.com/api/token'
        response = requests.post(auth_url, {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        })

        if response.status_code == 200:
            self.authorization_token = response.json()["access_token"]

    def get_spotify_id_of_track(self, artist, title):
        search_endpoint_url = "https://api.spotify.com/v1/search"
        query_term = "{} {}".format(artist, title).replace(" ", "+")

        headers = {"Authorization": "Bearer {}".format(self.authorization_token)}

        request = requests.get(search_endpoint_url, headers=headers, params={
            "q": query_term,
            "type": "track"
        })
        second_request = None

        if request.status_code == 400 or request.status_code == 401:
            # try again, get a new token
            self.get_authorization_token()
            headers = {"Authorization": "Bearer {}".format(self.authorization_token)}
            second_request = requests.get(search_endpoint_url, headers=headers, params={
                "q": query_term,
                "type": "track"
            })
            if second_request.status_code == 200:
                request = second_request

        artist_verified = False
        track_verified = False

        if request.status_code == 200 or (second_request is not None and second_request.status_code == 200):
            results = request.json()

            if "tracks" in results:
                for artist_object in results["tracks"]["items"][0]["artists"]:
                    artist_verified = artist.lower() in artist_object["name"].lower()
                    if artist_verified:
                        break
                track_verified = title.lower() in results["tracks"]["items"][0]["name"].lower()

            if artist_verified and track_verified:
                print("Track found, id: {}".format(results["tracks"]["items"][0]["id"]))

    def get_audio_analysis_of_track(self, track_id):
        aa_endpoint_url = "https://api.spotify.com/v1/audio-analysis/{}".format(track_id)


if __name__ == "__main__":
    # spoti = SpotifyDatabaseClient()
    # spoti.get_spotify_id_of_track("The Beatles", "Martha My Dear")
    app = Application()
    app.initialize_gui()