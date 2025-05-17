"""
Image quality validation module for the Telegram Cover Bot.
This module provides functionality for validating and ensuring high quality cover art.
"""
import os
import io
import logging
from typing import Dict, Any, Optional, Tuple
import requests
from PIL import Image, ImageFilter, ImageEnhance

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class ImageQualityValidator:
    """Image quality validator for ensuring high quality cover art."""
    
    def __init__(self, min_width: int = 500, min_height: int = 500, 
                 preferred_width: int = 1000, preferred_height: int = 1000):
        """
        Initialize the image quality validator.
        
        Args:
            min_width: Minimum acceptable width for cover art
            min_height: Minimum acceptable height for cover art
            preferred_width: Preferred width for high quality cover art
            preferred_height: Preferred height for high quality cover art
        """
        self.min_width = min_width
        self.min_height = min_height
        self.preferred_width = preferred_width
        self.preferred_height = preferred_height
    
    def validate_image_url(self, url: str) -> Dict[str, Any]:
        """
        Validate an image from a URL.
        
        Args:
            url: URL of the image to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "url": url,
            "is_valid": False,
            "quality": "unknown",
            "width": 0,
            "height": 0,
            "aspect_ratio": 0,
            "format": "unknown",
            "file_size": 0,
            "error": None
        }
        
        try:
            # Download image
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Get file size
            result["file_size"] = len(response.content)
            
            # Open image
            img = Image.open(io.BytesIO(response.content))
            
            # Get image properties
            result["width"], result["height"] = img.size
            result["aspect_ratio"] = result["width"] / result["height"] if result["height"] > 0 else 0
            result["format"] = img.format
            
            # Validate image
            result["is_valid"] = (
                result["width"] >= self.min_width and 
                result["height"] >= self.min_height and
                0.9 <= result["aspect_ratio"] <= 1.1  # Close to square aspect ratio
            )
            
            # Determine quality
            if result["width"] >= self.preferred_width and result["height"] >= self.preferred_height:
                result["quality"] = "high"
            elif result["width"] >= self.min_width and result["height"] >= self.min_height:
                result["quality"] = "medium"
            else:
                result["quality"] = "low"
            
        except Exception as e:
            logger.error(f"Error validating image URL: {e}")
            result["error"] = str(e)
        
        return result
    
    def validate_image_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate an image from a file.
        
        Args:
            file_path: Path to the image file to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "file_path": file_path,
            "is_valid": False,
            "quality": "unknown",
            "width": 0,
            "height": 0,
            "aspect_ratio": 0,
            "format": "unknown",
            "file_size": 0,
            "error": None
        }
        
        try:
            # Get file size
            result["file_size"] = os.path.getsize(file_path)
            
            # Open image
            img = Image.open(file_path)
            
            # Get image properties
            result["width"], result["height"] = img.size
            result["aspect_ratio"] = result["width"] / result["height"] if result["height"] > 0 else 0
            result["format"] = img.format
            
            # Validate image
            result["is_valid"] = (
                result["width"] >= self.min_width and 
                result["height"] >= self.min_height and
                0.9 <= result["aspect_ratio"] <= 1.1  # Close to square aspect ratio
            )
            
            # Determine quality
            if result["width"] >= self.preferred_width and result["height"] >= self.preferred_height:
                result["quality"] = "high"
            elif result["width"] >= self.min_width and result["height"] >= self.min_height:
                result["quality"] = "medium"
            else:
                result["quality"] = "low"
            
        except Exception as e:
            logger.error(f"Error validating image file: {e}")
            result["error"] = str(e)
        
        return result
    
    def enhance_image(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Enhance an image to improve its quality.
        
        Args:
            input_path: Path to the input image file
            output_path: Path to save the enhanced image
            
        Returns:
            Dictionary with enhancement results
        """
        result = {
            "input_path": input_path,
            "output_path": output_path,
            "success": False,
            "original_quality": "unknown",
            "enhanced_quality": "unknown",
            "error": None
        }
        
        try:
            # Validate original image
            original_validation = self.validate_image_file(input_path)
            result["original_quality"] = original_validation["quality"]
            
            # Open image
            img = Image.open(input_path)
            
            # Apply enhancements
            # 1. Sharpen the image
            img = img.filter(ImageFilter.SHARPEN)
            
            # 2. Enhance contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)  # Increase contrast by 20%
            
            # 3. Enhance color
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)  # Increase color saturation by 10%
            
            # 4. Enhance brightness
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.05)  # Increase brightness by 5%
            
            # Save enhanced image
            img.save(output_path, quality=95)  # High JPEG quality
            
            # Validate enhanced image
            enhanced_validation = self.validate_image_file(output_path)
            result["enhanced_quality"] = enhanced_validation["quality"]
            
            result["success"] = True
            
        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            result["error"] = str(e)
        
        return result
    
    def get_quality_report(self, url_or_path: str, is_url: bool = True) -> str:
        """
        Generate a quality report for an image.
        
        Args:
            url_or_path: URL or file path of the image
            is_url: Whether the input is a URL or file path
            
        Returns:
            Quality report as a string
        """
        try:
            # Validate image
            if is_url:
                validation = self.validate_image_url(url_or_path)
            else:
                validation = self.validate_image_file(url_or_path)
            
            # Generate report
            report = "# تقرير جودة الصورة\n\n"
            
            if validation["error"]:
                report += f"❌ **خطأ**: {validation['error']}\n\n"
                return report
            
            # Basic information
            report += "## معلومات أساسية\n\n"
            report += f"- **المصدر**: {'رابط URL' if is_url else 'ملف محلي'}\n"
            report += f"- **الصيغة**: {validation['format']}\n"
            report += f"- **الأبعاد**: {validation['width']}×{validation['height']} بكسل\n"
            report += f"- **نسبة العرض إلى الارتفاع**: {validation['aspect_ratio']:.2f}\n"
            report += f"- **حجم الملف**: {validation['file_size'] / 1024:.1f} كيلوبايت\n\n"
            
            # Quality assessment
            report += "## تقييم الجودة\n\n"
            
            quality_emoji = "🔴" if validation["quality"] == "low" else "🟡" if validation["quality"] == "medium" else "🟢"
            report += f"- **الجودة الإجمالية**: {quality_emoji} {validation['quality'].upper()}\n"
            
            # Resolution assessment
            resolution_emoji = "🔴" if validation["width"] < self.min_width or validation["height"] < self.min_height else "🟡" if validation["width"] < self.preferred_width or validation["height"] < self.preferred_height else "🟢"
            report += f"- **الدقة**: {resolution_emoji} {validation['width']}×{validation['height']} بكسل\n"
            
            # Aspect ratio assessment
            aspect_emoji = "🔴" if validation["aspect_ratio"] < 0.9 or validation["aspect_ratio"] > 1.1 else "🟡" if validation["aspect_ratio"] < 0.95 or validation["aspect_ratio"] > 1.05 else "🟢"
            report += f"- **نسبة العرض إلى الارتفاع**: {aspect_emoji} {validation['aspect_ratio']:.2f}\n\n"
            
            # Recommendations
            report += "## التوصيات\n\n"
            
            if validation["quality"] == "high":
                report += "✅ **الصورة ذات جودة عالية ومناسبة للاستخدام.**\n"
            elif validation["quality"] == "medium":
                report += "⚠️ **الصورة ذات جودة متوسطة. يمكن تحسينها عن طريق البحث عن نسخة بدقة أعلى.**\n"
            else:
                report += "❌ **الصورة ذات جودة منخفضة. يوصى بالبحث عن نسخة بدقة أعلى.**\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return f"# تقرير جودة الصورة\n\n❌ **خطأ**: {e}\n"
