from mutagen import File
from mutagen.mp3 import MP3
from datetime import datetime
import os

class Track:
    def __init__(self, path: str, title: str, album: str) -> None:
        """
        Parameters
        ----------
        path : str
            The local track file path
        title : str
            The title of the track
        album : str
            The album of the track
        """
        self.path = path
        self.title = title
        self.album = album

        self.date_added = datetime.fromtimestamp(os.path.getctime(self.path))

        mp3 = MP3(self.path)
        self.duration = int(mp3.info.length)
        self.sample_rate = mp3.info.sample_rate

        file = File(self.path, easy=True)

        try:
            self.artist = file["artist"][0]
        except Exception:
            self.artist = "Unknown Artist"