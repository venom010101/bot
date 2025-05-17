"""
iTunes Search API implementation for fetching music covers.
"""
import requests
from typing import Dict, List, Optional, Any
from api.base import MusicAPI


class iTunesAPI(MusicAPI):
    """Implementation of the iTunes Search API for fetching music covers."""
    
    BASE_URL = "https://itunes.apple.com/search"
    
    def __init__(self):
        """Initialize the iTunes API client."""
        self.session = requests.Session()
    
    def _search(self, query: str, media: str = "music", entity: str = None, limit: int = 10) -> Dict[str, Any]:
        """
        Perform a search using the iTunes Search API.
        
        Args:
            query: The search query
            media: The media type to search for (music, podcast, etc.)
            entity: The entity type to search for (song, album, artist)
            limit: Maximum number of results to return
            
        Returns:
            The JSON response from the API
        """
        params = {
            "term": query,
            "media": media,
            "limit": limit,
            "country": "US"  # Default to US store for wider content availability
        }
        
        if entity:
            params["entity"] = entity
            
        response = self.session.get(self.BASE_URL, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        return response.json()
    
    def search_song(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for songs by name.
        
        Args:
            query: The song name to search for
            
        Returns:
            A list of song dictionaries
        """
        results = self._search(query, entity="song")
        return self._parse_song_results(results)
    
    def search_artist(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for songs by artist.
        
        Args:
            query: The artist name to search for
            
        Returns:
            A list of song dictionaries
        """
        # First search for the artist
        artist_results = self._search(query, entity="musicArtist", limit=1)
        
        if not artist_results.get("resultCount", 0):
            # If no exact artist match, just search for songs with this artist name
            results = self._search(query, entity="song")
            return self._parse_song_results(results)
        
        # If we found an artist, get their artist ID and search for their songs
        artist_id = artist_results["results"][0]["artistId"]
        results = self._search(f"artistId:{artist_id}", entity="song", limit=20)
        return self._parse_song_results(results)
    
    def search_album(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for albums.
        
        Args:
            query: The album name to search for
            
        Returns:
            A list of album dictionaries
        """
        results = self._search(query, entity="album")
        return self._parse_album_results(results)
    
    def get_cover_url(self, item: Dict[str, Any], high_quality: bool = True) -> Optional[str]:
        """
        Extract cover URL from an item (song or album).
        
        Args:
            item: The song or album dictionary
            high_quality: Whether to return high quality image if available
            
        Returns:
            URL to the cover image or None if not available
        """
        if high_quality and "cover_url_hq" in item:
            return item["cover_url_hq"]
        return item.get("cover_url")
    
    def _parse_song_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse song results from iTunes API response.
        
        Args:
            results: The iTunes API response
            
        Returns:
            A list of parsed song dictionaries
        """
        parsed_results = []
        
        for item in results.get("results", []):
            if item.get("wrapperType") != "track" or item.get("kind") != "song":
                continue
                
            # Get the artwork URL and upgrade to highest quality
            artwork_url = item.get("artworkUrl100")
            if not artwork_url:
                continue
                
            # iTunes artwork URLs can be upgraded by changing the size in the URL
            # Default is 100x100, we can get higher resolutions by replacing this
            # Common sizes: 100x100, 600x600, 1200x1200, 1400x1400, 1600x1600
            # The highest quality is usually 1600x1600 or 3000x3000 depending on the album
            
            # Try to get the highest quality by replacing the size
            # Format: https://is1-ssl.mzstatic.com/image/thumb/Music/v4/path/artworkUrl100.jpg
            high_quality_url = artwork_url.replace("100x100", "1600x1600")
            
            parsed_results.append({
                "title": item.get("trackName", "Unknown Title"),
                "artist": item.get("artistName", "Unknown Artist"),
                "album": item.get("collectionName", "Unknown Album"),
                "cover_url": artwork_url,
                "cover_url_hq": high_quality_url,
                "preview_url": item.get("previewUrl"),
                "track_id": item.get("trackId"),
                "collection_id": item.get("collectionId"),
                "artist_id": item.get("artistId"),
                "release_date": item.get("releaseDate")
            })
            
        return parsed_results
    
    def _parse_album_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse album results from iTunes API response.
        
        Args:
            results: The iTunes API response
            
        Returns:
            A list of parsed album dictionaries
        """
        parsed_results = []
        
        for item in results.get("results", []):
            if item.get("wrapperType") != "collection" or item.get("collectionType") != "Album":
                continue
                
            # Get the artwork URL and upgrade to highest quality
            artwork_url = item.get("artworkUrl100")
            if not artwork_url:
                continue
                
            # Upgrade to high quality as with songs
            high_quality_url = artwork_url.replace("100x100", "1600x1600")
            
            parsed_results.append({
                "title": item.get("collectionName", "Unknown Album"),
                "artist": item.get("artistName", "Unknown Artist"),
                "cover_url": artwork_url,
                "cover_url_hq": high_quality_url,
                "collection_id": item.get("collectionId"),
                "artist_id": item.get("artistId"),
                "track_count": item.get("trackCount"),
                "release_date": item.get("releaseDate"),
                "genre": item.get("primaryGenreName")
            })
            
        return parsed_results
