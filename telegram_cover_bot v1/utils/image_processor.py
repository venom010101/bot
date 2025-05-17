"""
Utility module for image processing in the Telegram Cover Bot.
"""
import requests
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image


class ImageProcessor:
    """Utility class for processing and validating cover images."""
    
    @staticmethod
    def download_image(url: str) -> Optional[BytesIO]:
        """
        Download an image from a URL.
        
        Args:
            url: The URL of the image to download
            
        Returns:
            BytesIO object containing the image data or None if download failed
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return BytesIO(response.content)
        except (requests.RequestException, IOError) as e:
            print(f"Error downloading image: {e}")
            return None
    
    @staticmethod
    def validate_image(image_data: BytesIO) -> Tuple[bool, Optional[Image.Image], Optional[str]]:
        """
        Validate an image and check its quality.
        
        Args:
            image_data: BytesIO object containing the image data
            
        Returns:
            Tuple of (is_valid, image_object, error_message)
        """
        try:
            image = Image.open(image_data)
            
            # Check if image is valid
            image.verify()
            
            # Reopen the image after verify (which closes it)
            image_data.seek(0)
            image = Image.open(image_data)
            
            # Check image dimensions
            width, height = image.size
            if width < 300 or height < 300:
                return False, None, "Image resolution too low"
                
            return True, image, None
        except Exception as e:
            return False, None, f"Invalid image: {str(e)}"
    
    @staticmethod
    def get_image_info(image: Image.Image) -> dict:
        """
        Get information about an image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with image information
        """
        width, height = image.size
        format_name = image.format
        mode = image.mode
        
        return {
            "width": width,
            "height": height,
            "format": format_name,
            "mode": mode,
            "aspect_ratio": width / height if height > 0 else 0
        }
    
    @staticmethod
    def prepare_for_telegram(image_data: BytesIO) -> BytesIO:
        """
        Prepare an image for sending via Telegram.
        
        Args:
            image_data: BytesIO object containing the image data
            
        Returns:
            BytesIO object with the processed image
        """
        # Reset the pointer to the beginning of the file
        image_data.seek(0)
        
        # Telegram supports JPEG, PNG, and other formats
        # We'll keep the original format but ensure it's not too large
        try:
            image = Image.open(image_data)
            
            # If image is very large, resize it to a reasonable size
            # Telegram has a 10MB limit for photos
            max_dimension = 1600
            width, height = image.size
            
            if width > max_dimension or height > max_dimension:
                # Calculate new dimensions while preserving aspect ratio
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))
                
                image = image.resize((new_width, new_height), Image.LANCZOS)
            
            # Save to BytesIO
            output = BytesIO()
            
            # Save in original format if possible
            format_name = image.format if image.format else "JPEG"
            
            # For JPEG, use quality parameter
            if format_name == "JPEG":
                image.save(output, format=format_name, quality=95)
            else:
                image.save(output, format=format_name)
                
            output.seek(0)
            return output
        except Exception as e:
            print(f"Error preparing image for Telegram: {e}")
            # Return original if processing fails
            image_data.seek(0)
            return image_data
