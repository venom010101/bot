"""
Audio file processing module for the Telegram Cover Bot.
This module provides functionality for extracting cover art from audio files
and improving cover quality.
"""
import os
import io
import logging
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import mutagen
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class AudioProcessor:
    """Audio file processor for extracting and improving cover art."""
    
    def __init__(self, temp_dir: str = "temp"):
        """
        Initialize the audio processor.
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    
    async def process_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process an audio file to extract metadata and cover art.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary with metadata and cover art information
        """
        result = {
            "success": False,
            "metadata": {},
            "cover_path": None,
            "cover_quality": "none",
            "error": None
        }
        
        try:
            # Extract metadata and cover art
            metadata, cover_data = self._extract_metadata_and_cover(file_path)
            
            if metadata:
                result["metadata"] = metadata
                result["success"] = True
            
            if cover_data:
                # Save cover art to temporary file
                cover_path, cover_quality = self._save_cover_art(cover_data, file_path)
                
                if cover_path:
                    result["cover_path"] = cover_path
                    result["cover_quality"] = cover_quality
            
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")
            result["error"] = str(e)
        
        return result
    
    def _extract_metadata_and_cover(self, file_path: str) -> Tuple[Dict[str, Any], Optional[bytes]]:
        """
        Extract metadata and cover art from an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Tuple of (metadata dictionary, cover art bytes)
        """
        metadata = {}
        cover_data = None
        
        # Determine file type
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            # MP3 files
            if file_ext in ['.mp3']:
                audio = mutagen.File(file_path)
                
                # Extract metadata
                if audio:
                    if hasattr(audio, 'tags') and audio.tags:
                        # ID3 tags
                        tags = audio.tags
                        
                        # Title
                        if 'TIT2' in tags:
                            metadata['title'] = str(tags['TIT2'])
                        
                        # Artist
                        if 'TPE1' in tags:
                            metadata['artist'] = str(tags['TPE1'])
                        
                        # Album
                        if 'TALB' in tags:
                            metadata['album'] = str(tags['TALB'])
                        
                        # Extract cover art
                        for tag in tags.values():
                            if isinstance(tag, APIC):
                                cover_data = tag.data
                                break
            
            # MP4/M4A files
            elif file_ext in ['.m4a', '.mp4', '.aac']:
                audio = MP4(file_path)
                
                # Extract metadata
                if '\xa9nam' in audio:
                    metadata['title'] = audio['\xa9nam'][0]
                
                if '\xa9ART' in audio:
                    metadata['artist'] = audio['\xa9ART'][0]
                
                if '\xa9alb' in audio:
                    metadata['album'] = audio['\xa9alb'][0]
                
                # Extract cover art
                if 'covr' in audio:
                    cover_data = audio['covr'][0]
            
            # FLAC files
            elif file_ext in ['.flac']:
                audio = FLAC(file_path)
                
                # Extract metadata
                if 'title' in audio:
                    metadata['title'] = audio['title'][0]
                
                if 'artist' in audio:
                    metadata['artist'] = audio['artist'][0]
                
                if 'album' in audio:
                    metadata['album'] = audio['album'][0]
                
                # Extract cover art
                if audio.pictures:
                    cover_data = audio.pictures[0].data
            
            # OGG files
            elif file_ext in ['.ogg']:
                audio = OggVorbis(file_path)
                
                # Extract metadata
                if 'title' in audio:
                    metadata['title'] = audio['title'][0]
                
                if 'artist' in audio:
                    metadata['artist'] = audio['artist'][0]
                
                if 'album' in audio:
                    metadata['album'] = audio['album'][0]
                
                # OGG files don't have a standard way to store cover art
                # We would need to check for FLAC pictures or other metadata
            
            # Other file types
            else:
                # Try generic approach
                try:
                    audio = mutagen.File(file_path)
                    
                    if audio:
                        # Extract whatever metadata we can
                        for key in audio:
                            if isinstance(audio[key], list) and len(audio[key]) > 0:
                                metadata[key] = str(audio[key][0])
                except Exception as e:
                    logger.warning(f"Could not extract metadata from unknown file type: {e}")
        
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
        
        return metadata, cover_data
    
    def _save_cover_art(self, cover_data: bytes, original_file_path: str) -> Tuple[Optional[str], str]:
        """
        Save cover art to a temporary file and assess its quality.
        
        Args:
            cover_data: Cover art binary data
            original_file_path: Path to the original audio file
            
        Returns:
            Tuple of (cover path, quality assessment)
        """
        try:
            # Generate a filename based on the original file
            base_name = os.path.splitext(os.path.basename(original_file_path))[0]
            cover_path = os.path.join(self.temp_dir, f"{base_name}_cover.jpg")
            
            # Open image to check quality
            img = Image.open(io.BytesIO(cover_data))
            width, height = img.size
            
            # Assess quality
            quality = "low"
            if width >= 500 and height >= 500:
                quality = "medium"
            if width >= 1000 and height >= 1000:
                quality = "high"
            
            # Save the image
            with open(cover_path, 'wb') as f:
                f.write(cover_data)
            
            return cover_path, quality
            
        except Exception as e:
            logger.error(f"Error saving cover art: {e}")
            return None, "none"
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        try:
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")
