"""
Audio file handler for the Telegram Cover Bot.
This module provides handlers for processing audio files sent by users.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os
import logging
from typing import Dict, Any, Optional, List
import time

from utils.session import SessionManager
from utils.translation import TranslationManager
from utils.analytics import AnalyticsManager
from utils.database import InteractionDatabase
from utils.audio_processor import AudioProcessor
from api.itunes import iTunesAPI

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class AudioHandler:
    """Handler for audio files sent by users."""
    
    def __init__(self, 
                session_manager: SessionManager, 
                translation_manager: TranslationManager,
                analytics_manager: Optional[AnalyticsManager] = None,
                database: Optional[InteractionDatabase] = None):
        """
        Initialize the audio handler.
        
        Args:
            session_manager: Session manager instance
            translation_manager: Translation manager instance
            analytics_manager: Analytics manager instance (optional)
            database: Interaction database instance (optional)
        """
        self.session_manager = session_manager
        self.translation_manager = translation_manager
        self.analytics_manager = analytics_manager
        self.database = database
        
        # Initialize audio processor
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        self.audio_processor = AudioProcessor(temp_dir=temp_dir)
        
        # Initialize iTunes API
        self.itunes_api = iTunesAPI()
    
    async def handle_audio_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle audio files sent by users.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
        """
        user = update.effective_user
        chat_id = update.effective_chat.id
        message = update.message
        
        # Get user language
        user_lang = self.session_manager.get_user_language(user.id)
        _ = self.translation_manager.get_translation(user_lang)
        
        # Log interaction if database is available
        if self.database:
            user_data = {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
            self.database.log_interaction("audio", {
                "file_id": message.audio.file_id if message.audio else (message.voice.file_id if message.voice else "unknown"),
                "user": user_data
            }, user.id, chat_id if update.effective_chat.type != "private" else None)
        
        # Send processing message
        processing_message = await message.reply_text(
            _("🔍 جاري معالجة الملف الصوتي واستخراج الغلاف... يرجى الانتظار.")
        )
        
        try:
            # Download the audio file
            audio = message.audio or message.voice
            if not audio:
                await processing_message.edit_text(
                    _("❌ لم يتم العثور على ملف صوتي. يرجى إرسال ملف صوتي صالح.")
                )
                return
            
            # Get file from Telegram
            file = await context.bot.get_file(audio.file_id)
            
            # Generate a unique filename
            timestamp = int(time.time())
            file_name = f"audio_{user.id}_{timestamp}"
            
            # Add appropriate extension
            if message.audio:
                mime_type = message.audio.mime_type
                if mime_type == "audio/mpeg":
                    file_name += ".mp3"
                elif mime_type == "audio/mp4":
                    file_name += ".m4a"
                elif mime_type == "audio/ogg":
                    file_name += ".ogg"
                elif mime_type == "audio/flac":
                    file_name += ".flac"
                else:
                    file_name += ".mp3"  # Default to mp3
            else:
                file_name += ".ogg"  # Voice messages are usually OGG
            
            # Download file
            file_path = os.path.join(self.audio_processor.temp_dir, file_name)
            await file.download_to_drive(file_path)
            
            # Process the audio file
            await processing_message.edit_text(
                _("🔍 جاري استخراج الغلاف والبيانات الوصفية...")
            )
            
            result = await self.audio_processor.process_audio_file(file_path)
            
            if not result["success"]:
                await processing_message.edit_text(
                    _("❌ فشل في معالجة الملف الصوتي: {error}").format(
                        error=result["error"] or _("خطأ غير معروف")
                    )
                )
                return
            
            # Check if cover was extracted
            if result["cover_path"]:
                # Log cover extraction if database is available
                if self.database:
                    self.database.log_interaction("cover_extracted", {
                        "file_id": audio.file_id,
                        "cover_quality": result["cover_quality"],
                        "metadata": result["metadata"],
                        "user": user_data
                    }, user.id, chat_id if update.effective_chat.type != "private" else None)
                
                # If cover quality is high, send it directly
                if result["cover_quality"] == "high":
                    await processing_message.edit_text(
                        _("✅ تم استخراج غلاف الأغنية بنجاح!")
                    )
                    
                    # Send cover image
                    with open(result["cover_path"], 'rb') as cover_file:
                        await context.bot.send_photo(
                            chat_id=chat_id,
                            photo=cover_file,
                            caption=_("🎵 غلاف الأغنية: {title}\n👤 الفنان: {artist}\n💿 الألبوم: {album}").format(
                                title=result["metadata"].get("title", _("غير معروف")),
                                artist=result["metadata"].get("artist", _("غير معروف")),
                                album=result["metadata"].get("album", _("غير معروف"))
                            )
                        )
                    
                    return
                
                # If cover quality is medium or low, offer to search for better quality
                await processing_message.edit_text(
                    _("🔍 تم استخراج غلاف الأغنية بجودة {quality}. هل تريد البحث عن غلاف بجودة أعلى؟").format(
                        quality=_("متوسطة") if result["cover_quality"] == "medium" else _("منخفضة")
                    )
                )
                
                # Send extracted cover with buttons
                with open(result["cover_path"], 'rb') as cover_file:
                    # Create keyboard with search options
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                _("🔍 بحث عن غلاف بجودة أعلى"),
                                callback_data=f"search_better_cover:{audio.file_id}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                _("✅ استخدام هذا الغلاف"),
                                callback_data=f"use_extracted_cover:{audio.file_id}"
                            )
                        ]
                    ]
                    
                    # Store metadata in user data for later use
                    context.user_data['audio_metadata'] = result["metadata"]
                    context.user_data['audio_file_id'] = audio.file_id
                    
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=cover_file,
                        caption=_("🎵 غلاف الأغنية: {title}\n👤 الفنان: {artist}\n💿 الألبوم: {album}").format(
                            title=result["metadata"].get("title", _("غير معروف")),
                            artist=result["metadata"].get("artist", _("غير معروف")),
                            album=result["metadata"].get("album", _("غير معروف"))
                        ),
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                
            else:
                # No cover found, try to search based on metadata
                metadata = result["metadata"]
                
                if not metadata or not (metadata.get("title") or metadata.get("artist") or metadata.get("album")):
                    await processing_message.edit_text(
                        _("❌ لم يتم العثور على غلاف في الملف الصوتي ولا توجد بيانات وصفية كافية للبحث.")
                    )
                    return
                
                # Ask user if they want to search based on metadata
                search_text = ""
                if metadata.get("title") and metadata.get("artist"):
                    search_text = f"{metadata['title']} {metadata['artist']}"
                elif metadata.get("title") and metadata.get("album"):
                    search_text = f"{metadata['title']} {metadata['album']}"
                elif metadata.get("title"):
                    search_text = metadata["title"]
                elif metadata.get("artist") and metadata.get("album"):
                    search_text = f"{metadata['artist']} {metadata['album']}"
                elif metadata.get("artist"):
                    search_text = metadata["artist"]
                elif metadata.get("album"):
                    search_text = metadata["album"]
                
                if search_text:
                    # Store search text in user data for later use
                    context.user_data['audio_search_text'] = search_text
                    context.user_data['audio_metadata'] = metadata
                    context.user_data['audio_file_id'] = audio.file_id
                    
                    # Create keyboard with search options
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                _("🔍 بحث عن غلاف"),
                                callback_data=f"search_cover_from_audio:{audio.file_id}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                _("❌ إلغاء"),
                                callback_data=f"cancel_audio_search:{audio.file_id}"
                            )
                        ]
                    ]
                    
                    await processing_message.edit_text(
                        _("ℹ️ لم يتم العثور على غلاف في الملف الصوتي، لكن تم استخراج البيانات الوصفية التالية:\n\n"
                          "🎵 العنوان: {title}\n"
                          "👤 الفنان: {artist}\n"
                          "💿 الألبوم: {album}\n\n"
                          "هل تريد البحث عن غلاف بناءً على هذه البيانات؟").format(
                            title=metadata.get("title", _("غير معروف")),
                            artist=metadata.get("artist", _("غير معروف")),
                            album=metadata.get("album", _("غير معروف"))
                        ),
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await processing_message.edit_text(
                        _("❌ لم يتم العثور على غلاف في الملف الصوتي ولا توجد بيانات وصفية كافية للبحث.")
                    )
            
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")
            
            # Log error if database is available
            if self.database:
                self.database.log_error(
                    str(e), "audio_processing", user.id, user_data,
                    chat_id if update.effective_chat.type != "private" else None
                )
            
            await processing_message.edit_text(
                _("❌ حدث خطأ أثناء معالجة الملف الصوتي: {error}").format(
                    error=str(e)
                )
            )
    
    async def handle_audio_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Handle callback queries related to audio files.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
            
        Returns:
            True if the callback was handled, False otherwise
        """
        query = update.callback_query
        data = query.data
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Check if this is an audio-related callback
        if not (data.startswith('search_better_cover:') or 
                data.startswith('use_extracted_cover:') or 
                data.startswith('search_cover_from_audio:') or 
                data.startswith('cancel_audio_search:')):
            return False
        
        # Get user language
        user_lang = self.session_manager.get_user_language(user.id)
        _ = self.translation_manager.get_translation(user_lang)
        
        # Log callback if database is available
        if self.database:
            user_data = {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
            self.database.log_interaction("callback", {
                "callback_data": data,
                "user": user_data
            }, user.id, chat_id if update.effective_chat.type != "private" else None)
        
        # Handle search for better cover
        if data.startswith('search_better_cover:'):
            await query.answer(_("🔍 جاري البحث عن غلاف بجودة أعلى..."))
            
            # Get metadata from user data
            metadata = context.user_data.get('audio_metadata', {})
            
            if not metadata:
                await query.edit_message_caption(
                    caption=_("❌ لم يتم العثور على بيانات وصفية للبحث.")
                )
                return True
            
            # Create search query
            search_query = ""
            if metadata.get("title") and metadata.get("artist"):
                search_query = f"{metadata['title']} {metadata['artist']}"
            elif metadata.get("title") and metadata.get("album"):
                search_query = f"{metadata['title']} {metadata['album']}"
            elif metadata.get("title"):
                search_query = metadata["title"]
            elif metadata.get("artist") and metadata.get("album"):
                search_query = f"{metadata['artist']} {metadata['album']}"
            
            if not search_query:
                await query.edit_message_caption(
                    caption=_("❌ لم يتم العثور على بيانات وصفية كافية للبحث.")
                )
                return True
            
            # Search for cover
            await self._search_and_send_cover(
                search_query, chat_id, context, user, user_data, _
            )
            
            return True
            
        # Handle use extracted cover
        elif data.startswith('use_extracted_cover:'):
            await query.answer(_("✅ تم اختيار استخدام الغلاف المستخرج."))
            
            # Update caption
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n" + _("✅ تم اختيار استخدام هذا الغلاف.")
            )
            
            return True
            
        # Handle search cover from audio
        elif data.startswith('search_cover_from_audio:'):
            await query.answer(_("🔍 جاري البحث عن غلاف..."))
            
            # Get search text from user data
            search_text = context.user_data.get('audio_search_text', "")
            
            if not search_text:
                await query.edit_message_text(
                    _("❌ لم يتم العثور على بيانات للبحث.")
                )
                return True
            
            # Search for cover
            await self._search_and_send_cover(
                search_text, chat_id, context, user, user_data, _
            )
            
            return True
            
        # Handle cancel audio search
        elif data.startswith('cancel_audio_search:'):
            await query.answer(_("❌ تم إلغاء البحث."))
            
            # Update message
            await query.edit_message_text(
                _("❌ تم إلغاء البحث عن غلاف الأغنية.")
            )
            
            return True
        
        return False
    
    async def _search_and_send_cover(self, 
                                    search_query: str, 
                                    chat_id: int, 
                                    context: ContextTypes.DEFAULT_TYPE,
                                    user: Any,
                                    user_data: Dict[str, Any],
                                    _: Any) -> None:
        """
        Search for a cover and send it to the user.
        
        Args:
            search_query: Search query
            chat_id: Chat ID to send the cover to
            context: The context object from Telegram
            user: The user object
            user_data: User data for logging
            _: Translation function
        """
        try:
            # Search for song
            results = await self.itunes_api.search_song(search_query)
            
            if not results:
                # Try artist search
                results = await self.itunes_api.search_artist(search_query)
            
            if not results:
                # Try album search
                results = await self.itunes_api.search_album(search_query)
            
            if not results or len(results) == 0:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=_("❌ لم يتم العثور على نتائج للبحث: {query}").format(
                        query=search_query
                    )
                )
                return
            
            # Get the first result
            result = results[0]
            
            # Get high quality cover
            cover_url = self.itunes_api.get_high_quality_artwork_url(result['artworkUrl100'])
            
            # Log search if database is available
            if self.database:
                self.database.log_search(
                    search_query, "audio_cover", user.id, user_data,
                    chat_id if chat_id != user.id else None
                )
                
                self.database.log_result(
                    search_query, "audio_cover", results, 0, user.id, user_data,
                    chat_id if chat_id != user.id else None
                )
            
            # Send cover
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=cover_url,
                caption=_("🎵 تم العثور على غلاف بجودة عالية:\n\n"
                         "🎵 العنوان: {title}\n"
                         "👤 الفنان: {artist}\n"
                         "💿 الألبوم: {album}").format(
                    title=result.get('trackName', result.get('collectionName', _("غير معروف"))),
                    artist=result.get('artistName', _("غير معروف")),
                    album=result.get('collectionName', _("غير معروف"))
                )
            )
            
            # Log image if database is available
            if self.database:
                self.database.log_image(
                    cover_url, {
                        "source": "itunes",
                        "quality": "high",
                        "search_query": search_query
                    }, user.id, user_data,
                    chat_id if chat_id != user.id else None
                )
            
        except Exception as e:
            logger.error(f"Error searching for cover: {e}")
            
            # Log error if database is available
            if self.database:
                self.database.log_error(
                    str(e), "cover_search", user.id, user_data,
                    chat_id if chat_id != user.id else None
                )
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=_("❌ حدث خطأ أثناء البحث عن الغلاف: {error}").format(
                    error=str(e)
                )
            )
