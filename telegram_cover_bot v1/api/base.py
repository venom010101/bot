"""
Base API interface for music services.
This module defines the abstract base class for all API implementations.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class MusicAPI(ABC):
    """Abstract base class for music API implementations."""
    
    @abstractmethod
    def search_song(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for songs by name.
        
        Args:
            query: The song name to search for
            
        Returns:
            A list of song dictionaries containing at least:
            - title: Song title
            - artist: Artist name
            - album: Album name
            - cover_url: URL to the album cover image
            - cover_url_hq: URL to high quality album cover (if available)
        """
        pass
    
    @abstractmethod
    def search_artist(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for songs by artist.
        
        Args:
            query: The artist name to search for
            
        Returns:
            A list of song dictionaries (same format as search_song)
        """
        pass
    
    @abstractmethod
    def search_album(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for albums.
        
        Args:
            query: The album name to search for
            
        Returns:
            A list of album dictionaries containing at least:
            - title: Album title
            - artist: Artist name
            - cover_url: URL to the album cover image
            - cover_url_hq: URL to high quality album cover (if available)
        """
        pass
    
    @abstractmethod
    def get_cover_url(self, item: Dict[str, Any], high_quality: bool = True) -> Optional[str]:
        """
        Extract cover URL from an item (song or album).
        
        Args:
            item: The song or album dictionary
            high_quality: Whether to return high quality image if available
            
        Returns:
            URL to the cover image or None if not available
        """
        pass
