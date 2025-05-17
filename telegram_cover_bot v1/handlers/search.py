"""
Updated search handler with multilanguage support, analytics, and social sharing.
"""
from telegram import Update, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from io import BytesIO
from typing import List, Dict, Any, Optional

from api.itunes import iTunesAPI
from utils.image_processor import ImageProcessor
from utils.session import SessionManager
from utils.translation import TranslationManager
from utils.analytics import AnalyticsManager
from utils.social_sharing import SocialSharingManager
from .commands import create_results_keyboard


class SearchHandler:
    """Handler for search-related functionality."""
    
    def __init__(self, session_manager: SessionManager, 
                translation_manager: TranslationManager = None,
                analytics_manager: AnalyticsManager = None,
                social_sharing_manager: SocialSharingManager = None):
        """
        Initialize the search handler.
        
        Args:
            session_manager: Session manager instance
            translation_manager: Translation manager instance (optional)
            analytics_manager: Analytics manager instance (optional)
            social_sharing_manager: Social sharing manager instance (optional)
        """
        self.api = iTunesAPI()
        self.image_processor = ImageProcessor()
        self.session_manager = session_manager
        self.translation_manager = translation_manager
        self.analytics_manager = analytics_manager
        self.social_sharing_manager = social_sharing_manager
        self.page_size = 5  # Number of results per page
    
    async def handle_text_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle direct text search (when user sends text without commands).
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
        """
        query = update.message.text.strip()
        user_id = update.effective_user.id
        
        # Get user language if translation manager is available
        user_lang = None
        if self.translation_manager:
            user_lang = self.translation_manager.get_user_language(user_id)
        
        if not query:
            # Use translation if available
            if self.translation_manager and user_lang:
                message = self.translation_manager.get_text('enter_query', user_lang)
            else:
                message = "الرجاء إدخال اسم أغنية، فنان، أو ألبوم للبحث."
                
            await update.message.reply_text(message)
            return
            
        # Default to song search for direct text
        await self._perform_search(update, context, query, "song")
    
    async def handle_song_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /search command.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
        """
        query = " ".join(context.args).strip() if context.args else ""
        user_id = update.effective_user.id
        
        # Get user language if translation manager is available
        user_lang = None
        if self.translation_manager:
            user_lang = self.translation_manager.get_user_language(user_id)
        
        if not query:
            # Use translation if available
            if self.translation_manager and user_lang:
                message = self.translation_manager.get_text('enter_song', user_lang)
            else:
                message = "الرجاء إدخال اسم الأغنية بعد الأمر.\nمثال: /search Bohemian Rhapsody"
                
            await update.message.reply_text(message)
            return
            
        await self._perform_search(update, context, query, "song")
    
    async def handle_artist_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /artist command.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
        """
        query = " ".join(context.args).strip() if context.args else ""
        user_id = update.effective_user.id
        
        # Get user language if translation manager is available
        user_lang = None
        if self.translation_manager:
            user_lang = self.translation_manager.get_user_language(user_id)
        
        if not query:
            # Use translation if available
            if self.translation_manager and user_lang:
                message = self.translation_manager.get_text('enter_artist', user_lang)
            else:
                message = "الرجاء إدخال اسم الفنان بعد الأمر.\nمثال: /artist Queen"
                
            await update.message.reply_text(message)
            return
            
        await self._perform_search(update, context, query, "artist")
    
    async def handle_album_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /album command.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
        """
        query = " ".join(context.args).strip() if context.args else ""
        user_id = update.effective_user.id
        
        # Get user language if translation manager is available
        user_lang = None
        if self.translation_manager:
            user_lang = self.translation_manager.get_user_language(user_id)
        
        if not query:
            # Use translation if available
            if self.translation_manager and user_lang:
                message = self.translation_manager.get_text('enter_album', user_lang)
            else:
                message = "الرجاء إدخال اسم الألبوم بعد الأمر.\nمثال: /album A Night at the Opera"
                
            await update.message.reply_text(message)
            return
            
        await self._perform_search(update, context, query, "album")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle callback queries from inline keyboards.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
        """
        query = update.callback_query
        data = query.data
        user_id = update.effective_user.id
        
        # Get user language if translation manager is available
        user_lang = None
        if self.translation_manager:
            user_lang = self.translation_manager.get_user_language(user_id)
        
        # Get user session
        session = self.session_manager.get_session(user_id)
        results = session.get('current_results', [])
        
        if not results:
            # Use translation if available
            if self.translation_manager and user_lang:
                message = self.translation_manager.get_text('no_results_available', user_lang)
            else:
                message = "لا توجد نتائج متاحة. الرجاء إجراء بحث جديد."
                
            await query.answer(message)
            return
            
        # Handle navigation
        if data.startswith("prev_") or data.startswith("next_"):
            index = int(data.split("_")[1])
            keyboard = create_results_keyboard(
                results, index, self.page_size, 
                self.translation_manager, user_lang
            )
            
            # Use translation if available
            if self.translation_manager and user_lang:
                message = self.translation_manager.get_text('choose_results', user_lang)
            else:
                message = "اختر من النتائج التالية:"
                
            await query.edit_message_text(
                message,
                reply_markup=keyboard
            )
            await query.answer()
            return
            
        # Handle selection
        if data.startswith("select_"):
            index = int(data.split("_")[1])
            
            if 0 <= index < len(results):
                selected_item = results[index]
                
                # Use translation if available
                if self.translation_manager and user_lang:
                    message = self.translation_manager.get_text('loading_cover', user_lang)
                else:
                    message = "جاري تحميل الغلاف..."
                    
                await query.answer(message)
                
                # Send the cover image
                await self._send_cover_image(
                    update.effective_chat.id,
                    selected_item,
                    context,
                    user_lang
                )
                
                # Record successful search in analytics
                if self.analytics_manager:
                    search_type = session.get('last_search_type', 'song')
                    self.analytics_manager.record_search(
                        user_id, 
                        session.get('last_query', ''), 
                        search_type, 
                        True
                    )
                
                # Delete the selection message to clean up
                await query.delete_message()
            else:
                # Use translation if available
                if self.translation_manager and user_lang:
                    message = self.translation_manager.get_text('result_error', user_lang)
                else:
                    message = "خطأ في اختيار النتيجة. الرجاء المحاولة مرة أخرى."
                    
                await query.answer(message)
    
    async def _perform_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                             query: str, search_type: str) -> None:
        """
        Perform a search and display results.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
            query: Search query
            search_type: Type of search (song, artist, album)
        """
        # Send typing action
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Get user ID and language
        user_id = update.effective_user.id
        user_lang = None
        if self.translation_manager:
            user_lang = self.translation_manager.get_user_language(user_id)
        
        # Store search in session
        self.session_manager.add_recent_search(user_id, query, search_type)
        
        # Store for analytics
        session = self.session_manager.get_session(user_id)
        session['last_query'] = query
        session['last_search_type'] = search_type
        
        # Perform search based on type
        results = []
        if search_type == "song":
            results = self.api.search_song(query)
        elif search_type == "artist":
            results = self.api.search_artist(query)
        elif search_type == "album":
            results = self.api.search_album(query)
        
        # Store results in session
        session['current_results'] = results
        
        # Record search in analytics
        if self.analytics_manager:
            self.analytics_manager.record_search(
                user_id, 
                query, 
                search_type, 
                len(results) > 0
            )
        
        if not results:
            # Use translation if available
            if self.translation_manager and user_lang:
                message = self.translation_manager.get_text('no_results', user_lang, query=query)
            else:
                message = f"لم يتم العثور على نتائج لـ '{query}'.\nالرجاء المحاولة بكلمات مفتاحية مختلفة."
                
            await update.message.reply_text(message)
            return
            
        # If only one result, send it directly
        if len(results) == 1:
            await self._send_cover_image(
                update.effective_chat.id,
                results[0],
                context,
                user_lang
            )
            return
            
        # Otherwise, show selection keyboard
        keyboard = create_results_keyboard(
            results, 0, self.page_size,
            self.translation_manager, user_lang
        )
        
        # Use translation if available
        if self.translation_manager and user_lang:
            message = self.translation_manager.get_text('results_found', user_lang, count=len(results), query=query)
        else:
            message = f"تم العثور على {len(results)} نتيجة لـ '{query}'.\nاختر من النتائج التالية:"
            
        await update.message.reply_text(
            message,
            reply_markup=keyboard
        )
    
    async def _send_cover_image(self, chat_id: int, item: Dict[str, Any], 
                               context: ContextTypes.DEFAULT_TYPE,
                               user_lang: str = None) -> None:
        """
        Send a cover image to the user.
        
        Args:
            chat_id: Telegram chat ID
            item: Item containing cover URL
            context: The context object from Telegram
            user_lang: User language code (optional)
        """
        # Get high quality cover URL
        cover_url = self.api.get_cover_url(item, high_quality=True)
        
        if not cover_url:
            # Use translation if available
            if self.translation_manager and user_lang:
                message = self.translation_manager.get_text('no_cover_found', user_lang)
            else:
                message = "عذراً، لا يمكن العثور على غلاف لهذه الأغنية."
                
            await context.bot.send_message(
                chat_id=chat_id,
                text=message
            )
            return
            
        # Download the image
        image_data = self.image_processor.download_image(cover_url)
        
        if not image_data:
            # Use translation if available
            if self.translation_manager and user_lang:
                message = self.translation_manager.get_text('error_loading', user_lang)
            else:
                message = "عذراً، حدث خطأ أثناء تحميل الغلاف."
                
            await context.bot.send_message(
                chat_id=chat_id,
                text=message
            )
            return
            
        # Validate the image
        is_valid, image_obj, error = self.image_processor.validate_image(image_data)
        
        if not is_valid:
            # Try with standard quality URL as fallback
            cover_url = self.api.get_cover_url(item, high_quality=False)
            image_data = self.image_processor.download_image(cover_url)
            
            if not image_data:
                # Use translation if available
                if self.translation_manager and user_lang:
                    message = self.translation_manager.get_text('error_loading', user_lang)
                else:
                    message = "عذراً، حدث خطأ أثناء تحميل الغلاف."
                    
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message
                )
                return
                
            is_valid, image_obj, error = self.image_processor.validate_image(image_data)
            
            if not is_valid:
                # Use translation if available
                if self.translation_manager and user_lang:
                    message = self.translation_manager.get_text('invalid_image', user_lang, error=error)
                else:
                    message = f"عذراً، الصورة غير صالحة: {error}"
                    
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message
                )
                return
        
        # Prepare image for Telegram
        telegram_image = self.image_processor.prepare_for_telegram(image_data)
        
        # Get image info for caption
        image_info = self.image_processor.get_image_info(image_obj)
        
        # Create caption
        if self.translation_manager and user_lang:
            caption = f"🎵 *{item.get('title', 'Unknown')}*\n"
            caption += f"👤 {item.get('artist', 'Unknown Artist')}\n"
            
            if 'album' in item:
                caption += f"💿 {item.get('album', 'Unknown Album')}\n"
                
            caption += f"\n{self.translation_manager.get_text('image_quality', user_lang, width=image_info['width'], height=image_info['height'])}"
        else:
            caption = f"🎵 *{item.get('title', 'Unknown')}*\n"
            caption += f"👤 {item.get('artist', 'Unknown Artist')}\n"
            
            if 'album' in item:
                caption += f"💿 {item.get('album', 'Unknown Album')}\n"
                
            caption += f"\n📊 جودة الصورة: {image_info['width']}×{image_info['height']} بكسل"
        
        # Create share buttons if social sharing manager is available
        reply_markup = None
        if self.social_sharing_manager:
            song_info = {
                'title': item.get('title', 'Unknown'),
                'artist': item.get('artist', 'Unknown Artist'),
                'album': item.get('album', 'Unknown Album') if 'album' in item else None
            }
            reply_markup = self.social_sharing_manager.create_share_buttons_for_cover(
                cover_url, song_info, user_lang
            )
        
        # Send the image
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=telegram_image,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
