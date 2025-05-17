"""
Social sharing module for the Telegram Cover Bot.
This module provides functionality for sharing the bot and content on social media.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, Any, Optional

from utils.translation import TranslationManager


class SocialSharingManager:
    """Manager for social sharing functionality."""
    
    def __init__(self, bot_username: str, translation_manager: TranslationManager):
        """
        Initialize the social sharing manager.
        
        Args:
            bot_username: The bot's username
            translation_manager: Translation manager instance
        """
        self.bot_username = bot_username
        self.translation_manager = translation_manager
    
    async def share_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the /share command.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
        """
        user_id = update.effective_user.id
        user_lang = self.translation_manager.get_user_language(user_id)
        
        # Create share message
        share_message = self.translation_manager.get_text('share_message', user_lang)
        
        # Create share text
        share_text = self.translation_manager.get_text('share_text', user_lang, bot_username=self.bot_username)
        
        # Create keyboard with sharing options
        keyboard = [
            [
                InlineKeyboardButton(
                    self.translation_manager.get_text('btn_share_telegram', user_lang),
                    url=f"https://t.me/share/url?url=https://t.me/{self.bot_username}&text={share_text}"
                )
            ],
            [
                InlineKeyboardButton(
                    self.translation_manager.get_text('btn_share_twitter', user_lang),
                    url=f"https://twitter.com/intent/tweet?text={share_text}"
                )
            ],
            [
                InlineKeyboardButton(
                    self.translation_manager.get_text('btn_share_facebook', user_lang),
                    url=f"https://www.facebook.com/sharer/sharer.php?u=https://t.me/{self.bot_username}"
                )
            ],
            [
                InlineKeyboardButton(
                    self.translation_manager.get_text('btn_share_whatsapp', user_lang),
                    url=f"https://wa.me/?text={share_text}"
                )
            ]
        ]
        
        await update.message.reply_text(
            share_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def create_share_buttons_for_cover(self, cover_url: str, song_info: Dict[str, str], user_lang: str) -> InlineKeyboardMarkup:
        """
        Create share buttons for a specific cover image.
        
        Args:
            cover_url: URL of the cover image
            song_info: Dictionary with song information (title, artist, album)
            user_lang: User's language code
            
        Returns:
            InlineKeyboardMarkup with share buttons
        """
        # Create share text
        title = song_info.get('title', 'Unknown')
        artist = song_info.get('artist', 'Unknown Artist')
        
        share_text = self.translation_manager.get_text('cover_share_text', user_lang, 
                                                     title=title, artist=artist, 
                                                     bot_username=self.bot_username)
        
        # Create keyboard with sharing options
        keyboard = [
            [
                InlineKeyboardButton(
                    self.translation_manager.get_text('btn_share_telegram', user_lang),
                    url=f"https://t.me/share/url?url={cover_url}&text={share_text}"
                ),
                InlineKeyboardButton(
                    self.translation_manager.get_text('btn_share_twitter', user_lang),
                    url=f"https://twitter.com/intent/tweet?text={share_text}&url={cover_url}"
                )
            ],
            [
                InlineKeyboardButton(
                    self.translation_manager.get_text('btn_share_facebook', user_lang),
                    url=f"https://www.facebook.com/sharer/sharer.php?u={cover_url}"
                ),
                InlineKeyboardButton(
                    self.translation_manager.get_text('btn_share_whatsapp', user_lang),
                    url=f"https://wa.me/?text={share_text} {cover_url}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
