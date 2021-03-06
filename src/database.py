# Helpful resources: https://stackoverflow.com/questions/12223335/sqlalchemy-creating-vs-reusing-a-session

from datetime import datetime
import os
import time
from typing import Optional

import sqlalchemy as db
from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Boolean
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Database file path
FILE_PATH = os.path.abspath(os.path.join("data", "appdata.db"))

# Creating the database engine and a base class for table creation
engine = db.create_engine(f"sqlite:///{FILE_PATH}")
Base = declarative_base()

# A table to store playlist-track relationships (many-to-many)
playlist_track = Table(
    "playlist_track",
    Base.metadata,
    Column("playlist_id", Integer, ForeignKey("playlist.id")),
    Column("track_id", Integer, ForeignKey("track.id")),
)

class Playlist(Base):
    __tablename__ = "playlist"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    date_created = Column(DateTime)
    downloaded = Column(Boolean)
    tracks = relationship(
        "Track", secondary=playlist_track, back_populates="playlists"
    )

    def __init__(self, title: str, date_created: datetime, downloaded: bool=False, description: Optional[str]=None) -> None:
        """
        Parameters
        ----------
        title : str
            The title of the playlist
        date_created : datetime
            The date and time the playlist was created
        downloaded : bool
            Whether the contents of the playlist should be downloaded
        description : str, optional
            A description of the playlist

        Returns
        -------
        None
        """
        self.title = title
        self.date_created = date_created
        self.downloaded = downloaded

        if not description:
            description = ""
        self.description = description

    def get_length(self) -> int:
        """
        Returns the number of tracks in the playlist

        Returns
        -------
        int
            The number of tracks in the playlist
        """
        return len(self.tracks)

    def get_total_duration(self) -> int:
        """
        Get the total duration of all the tracks in the playlist.

        Returns
        -------
        int
            the total duration duration of all the tracks in the playlist
        """
        return sum([t.duration for t in self.tracks])

class Track(Base):
    __tablename__ = "track"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    artist = Column(String)
    album = Column(String)
    duration = Column(Integer)
    path = Column(String)
    stream_id = Column(Integer, ForeignKey("stream.id"))
    stream = relationship("Stream", backref="track")
    liked = Column(Boolean)
    cover_art_url = Column(String)
    playlists = relationship(
        "Playlist", secondary=playlist_track, back_populates="tracks"
    )

    def __init__(self, title: str, artist: str, album: str, duration: int, playlists: list[Playlist], liked: bool=False,
        path: Optional[str]=None, stream_url: Optional[str]=None, cover_art_url: Optional[str]=None) -> None:
        """
        Parameters
        ----------
        title : str
            The track title
        artist : str
            The track artist
        album : str
            The track album
        duration : int
            The track duration
        playlists : list[Playlist]
            A list of playlists that contain this track
        liked : bool
            Whether or not the track is liked
        path : str, optional
            The path the local version of the track is stored at
        stream_url : str, optional
            The url of the streamed track
        cover_art_url : str, optional
            The url of the cover art image

        Returns
        -------
        None
        """
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration
        self.playlists = playlists
        self.liked = liked
        self.cover_art_url = cover_art_url

        if path:
            self.path = path
        else:
            self.stream = Stream(stream_url)

class Stream(Base):
    __tablename__ = "stream"

    id = Column(Integer, primary_key=True)
    url = Column(String)

    def __init__(self, url: str) -> None:
        """
        Parameters
        ----------
        url : str
            The stream url for the corresponding track

        Returns
        -------
        None
        """
        self.url = url

class PlaylistManager:
    def __init__(self) -> None:
        """
        Creates the engine and a new session

        Returns
        -------
        None
        """
        Base.metadata.create_all(engine)
        self.session = None
        self.open_session()

    def get_track(self, title: Optional[str]=None, id: Optional[int]=None) -> Track:
        """
        Returns the first track with the corresponding title or id

        Parameters
        ----------
        title : str, optional
            The track object title
        id : int, optional
            The track object id

        Returns
        -------
        Track
            The first track with the corresponding title or id
        """
        track = None
        if title:
            track = self.session.query(Track).filter_by(title=title).first()
        elif id:
            track = self.session.query(Track).filter_by(id=id).first()
        return track

    def get_or_create_track(self, title: str, artist: str, album: str, duration: int, stream_url: str,
        cover_art_url: Optional[str]=None) -> Track:
        """
        Returns the first track with the corresponding title.
        If the track doesn't exist, creates a new track with the corresponding details and returns the object.

        Parameters
        ----------
        title : str
            The track title
        artist : str
            The track artist
        album : str
            The track album
        duration : int
            The track duration
        stream_url : str
            The track stream url
        cover_art_url : str, optional
            The track cover art image url

        Returns
        -------
        Track
            The first track with the corresponding title or id
        """
        track = self.get_track(title=title)
        if track == None:
            if not cover_art_url:
                cover_art_url = ""
            track = Track(title=title, artist=artist, album=album, duration=duration, playlists=[], stream_url=stream_url, cover_art_url=cover_art_url)
            self.session.add(track)
            self.session.commit()
        return track

    def add_track_cover_art(self, track: Track, cover_art_url: str) -> None:
        """
        Adds a cover art url to an existing track object

        Parameters
        ----------
        track : Track
            The track database object
        cover_art_url : str
            The track cover art image url

        Returns
        -------
        None
        """
        if not track:
            return

        track.cover_art_url = cover_art_url
        self.session.merge(track)
        self.session.commit()

    def get_playlist(self, title: str) -> Playlist:
        """
        Returns the first playlist with the specified title

        Parameters
        ----------
        title : str
            The playlist title
        Returns
        -------
        Playlist
            The first playlist with the specified title
        """
        playlist = self.session.query(Playlist).filter_by(title=title).first()
        return playlist

    def get_or_create_playlist(self, title: str="New Playlist") -> Playlist:
        """
        Returns the first playlist with the specified title.
        If the playlist doesn't exist, creates a new playlist with the specified title.

        Parameters
        ----------
        title : str
            The playlist title
        Returns
        -------
        Playlist
            The first playlist with the specified title
        """
        playlist = self.get_playlist(title)
        if playlist:
            return playlist

        playlist = Playlist(title=title, date_created=datetime.now())

        self.session.add(playlist)
        self.session.commit()
        return playlist

    def playlist_exists(self, title: str) -> bool:
        """
        Returns whether or not a playlist with the specified title already exists

        Parameters
        ----------
        title : str
            The playlist title
        Returns
        -------
        bool
            Whether or not a playlist with the specified title already exists
        """
        return self.get_playlist(title) is not None

    def rename_playlist(self, playlist: Playlist, new_title: str) -> None:
        """
        Renames an existing playlist

        Parameters
        ----------
        playlist : Playlist
            The playlist database object
        new_title : str
            The new playlist title
        Returns
        -------
        None
        """
        if not playlist:
            return

        playlist.title = new_title
        self.session.merge(playlist)
        self.session.commit()

    def edit_playlist_description(self, playlist: Playlist, new_description: str) -> None:
        """
        Edits an existing playlist's description

        Parameters
        ----------
        playlist : Playlist
            The playlist database object
        new_description : str
            The new playlist description
        Returns
        -------
        None
        """
        if not playlist:
            return

        playlist.description = new_description
        self.session.merge(playlist)
        self.session.commit()

    def delete_playlist(self, playlist: Playlist) -> None:
        """
        Deletes the specified playlist from the database

        Parameters
        ----------
        playlist : Playlist
            The playlist database object to delete
        Returns
        -------
        None
        """
        if not playlist:
            return

        self.session.delete(playlist)
        self.session.commit()

    def add_track_to_playlist(self, track: Track, playlist: Playlist) -> None:
        """
        Adds an existing track to an existing playlist

        Parameters
        ----------
        track : Track
            The track database object
        playlist : Playlist
            The playlist database object to add the track to

        Returns
        -------
        None
        """
        playlists = track.playlists
        if playlist in playlists:
            return
        playlists.append(playlist)
        track.playlists = playlists
        self.session.commit()

    def create_and_add_track_to_playlist(self, title: str, artist: str, album: str, duration: int,
        stream_url: str, playlist: Playlist, cover_art_url: Optional[str]=None) -> Track:
        """
        Creates and adds a track to an existing playlist

        Parameters
        ----------
        title : str
            The track title
        artist : str
            The track artist
        album : str
            The track album
        duration : int
            The track duration
        stream_url : str
            The track stream url
        playlist : Playlist
            The playlist to add the track to
        cover_art_url : str, optional
            The track cover art image url

        Returns
        -------
        Track
            The newly created track
        """
        track = self.get_or_create_track(title, artist, album, duration, stream_url, cover_art_url=cover_art_url)
        self.add_track_to_playlist(track, playlist)
        return track

    def add_track_to_liked_songs(self, track: Track) -> None:
        """
        Adds an existing track to the "Liked Songs" playlist

        Parameters
        ----------
        track : Track
            The track database object

        Returns
        -------
        None
        """
        liked_songs_playlist = self.get_or_create_playlist("Liked Songs")
        self.add_track_to_playlist(track, liked_songs_playlist)

    def create_and_add_track_to_liked_songs(self, title: str, artist: str, album: str, duration: int,
        stream_url: str, cover_art_url: Optional[str]=None) -> Track:
        """
        Creates and adds a track to the "Likes Songs" playlist

        Parameters
        ----------
        title : str
            The track title
        artist : str
            The track artist
        album : str
            The track album
        duration : int
            The track duration
        stream_url : str
            The track stream url
        cover_art_url : str, optional
            The track cover art image url

        Returns
        -------
        Track
            The newly created track
        """
        liked_songs_playlist = self.get_or_create_playlist("Liked Songs")
        return self.create_and_add_track_to_playlist(title, artist, album, duration, stream_url, liked_songs_playlist, cover_art_url=cover_art_url)

    def remove_track_from_playlist(self, track: Track, playlist: Playlist) -> None:
        """
        Removes a track from a playlist

        Parameters
        ----------
        track : Track
            The track database object
        playlist : Playlist
            The playlist database object (that contains the track) to remove the track from

        Returns
        -------
        None
        """
        playlists = track.playlists
        if playlist in playlists:
            playlists.remove(playlist)
            track.playlists = playlists
            self.session.commit()

    def remove_track_from_liked_songs(self, track: Track) -> None:
        """
        Removes a track from the "Liked Songs" playlist

        Parameters
        ----------
        track : Track
            The track database object

        Returns
        -------
        None
        """
        liked_songs_playlist = self.get_or_create_playlist("Liked Songs")
        self.remove_track_from_playlist(track, liked_songs_playlist)

    def track_is_liked(self, track: Track) -> bool:
        """
        Returns whether or not the "Liked Songs" playlist contains the specified track

        Parameters
        ----------
        track : Track
            The track database object

        Returns
        -------
        bool
            Whether or not the "Liked Songs" playlist contains the specified track
        """
        return self.get_or_create_playlist("Liked Songs") in track.playlists

    def open_session(self) -> None:
        """
        Opens a new SQL session

        Returns
        -------
        None
        """
        if self.session and self.session.is_active:
            return

        Session = sessionmaker()
        Session.configure(bind=engine)
        self.session = Session()

    def commit_session(self) -> None:
        """
        Commits the current session

        Returns
        -------
        None
        """
        self.session.commit()

    def close_session(self) -> None:
        """
        Closes the current session

        Returns
        -------
        None
        """
        self.session.close()

playlist_manager = PlaylistManager()

def test():
    playlist_manager = PlaylistManager()
    playlist_manager.close_session()
    playlists = playlist_manager.session.query(Playlist).all()

    for playlist in playlists:
        print(playlist.title)
        print(f"Number of Tracks: {playlist.get_length()}")
        print(f"Total duration: {time.strftime('%H:%M:%S', time.gmtime(playlist.get_total_duration()))}")
        for i, track in enumerate(playlist.tracks):
            print(f"{i+1}. Track: {track.title}")
            print(f"{i+1}. Url/Path: {track.stream.url if track.stream else track.path}")
            print()

if __name__ == "__main__":
    test()