"""
Group support module for the Telegram Cover Bot.
This module enhances the bot's functionality in group chats.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes
from typing import Optional, List, Dict, Any, Tuple

from utils.session import SessionManager


class GroupSupportHandler:
    """Handler for group-specific functionality."""
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize the group support handler.
        
        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
        self.group_sessions = {}  # Store group-specific data
    
    async def handle_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle commands in group chats.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
        """
        # Check if this is a group chat
        if not update.effective_chat.type in ['group', 'supergroup']:
            return
            
        # Get the command and arguments
        message = update.message
        command = message.text.split()[0].lower()
        
        if command == '/groupsearch':
            await self._handle_group_search(update, context)
        elif command == '/vote':
            await self._handle_vote(update, context)
        elif command == '/results':
            await self._handle_results(update, context)
    
    async def _handle_group_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle group search command.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
        """
        message = update.message
        args = message.text.split(' ', 1)
        
        if len(args) < 2:
            await message.reply_text(
                "الرجاء إدخال اسم الأغنية بعد الأمر.\n"
                "مثال: /groupsearch Bohemian Rhapsody"
            )
            return
            
        query = args[1].strip()
        group_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # Initialize group session if needed
        if group_id not in self.group_sessions:
            self.group_sessions[group_id] = {
                'current_poll': None,
                'votes': {},
                'results': []
            }
            
        # Create a new poll
        poll_message = await message.reply_text(
            f"🔍 بحث جماعي: \"{query}\"\n\n"
            f"تم بدء البحث بواسطة {update.effective_user.mention_html()}.\n"
            f"استخدم الأزرار أدناه للتصويت على نوع البحث:",
            reply_markup=self._create_search_type_keyboard(),
            parse_mode="HTML"
        )
        
        # Store poll information
        self.group_sessions[group_id]['current_poll'] = {
            'query': query,
            'message_id': poll_message.message_id,
            'initiator_id': user_id,
            'votes': {
                'song': [],
                'artist': [],
                'album': []
            },
            'status': 'voting'  # voting, searching, completed
        }
    
    async def _handle_vote(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle vote command in group chats.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
        """
        message = update.message
        group_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # Check if there's an active poll
        if group_id not in self.group_sessions or not self.group_sessions[group_id]['current_poll']:
            await message.reply_text("لا يوجد تصويت نشط حالياً. استخدم /groupsearch لبدء بحث جديد.")
            return
            
        # Get poll information
        poll = self.group_sessions[group_id]['current_poll']
        
        if poll['status'] != 'voting':
            await message.reply_text("التصويت مغلق. البحث قيد التنفيذ أو مكتمل.")
            return
            
        # Parse vote
        args = message.text.split(' ', 1)
        if len(args) < 2:
            await message.reply_text(
                "الرجاء تحديد نوع البحث.\n"
                "مثال: /vote song أو /vote artist أو /vote album"
            )
            return
            
        vote_type = args[1].strip().lower()
        
        if vote_type not in ['song', 'artist', 'album']:
            await message.reply_text("خيار غير صالح. الخيارات المتاحة: song, artist, album")
            return
            
        # Record vote
        for vote_category in poll['votes']:
            # Remove user from other categories if they voted before
            if user_id in poll['votes'][vote_category]:
                poll['votes'][vote_category].remove(user_id)
                
        # Add user vote to selected category
        poll['votes'][vote_type].append(user_id)
        
        # Update poll message
        await self._update_poll_message(context, group_id)
        
        # Delete the vote command message to keep the chat clean
        await message.delete()
    
    async def _handle_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle results command in group chats.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
        """
        message = update.message
        group_id = update.effective_chat.id
        
        # Check if there are any results
        if group_id not in self.group_sessions or not self.group_sessions[group_id]['results']:
            await message.reply_text("لا توجد نتائج بحث سابقة لهذه المجموعة.")
            return
            
        # Get the latest results
        results = self.group_sessions[group_id]['results'][-1]
        
        await message.reply_text(
            f"📊 نتائج آخر بحث:\n\n"
            f"🔍 استعلام: \"{results['query']}\"\n"
            f"🔎 نوع البحث: {results['search_type']}\n"
            f"📈 عدد النتائج: {results['count']}\n\n"
            f"استخدم /groupsearch للبدء في بحث جديد."
        )
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Handle callback queries from inline keyboards in group chats.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
            
        Returns:
            True if the callback was handled, False otherwise
        """
        query = update.callback_query
        data = query.data
        
        # Check if this is a group-related callback
        if not data.startswith('group_'):
            return False
            
        # Extract the action
        action = data.split('_')[1]
        
        if action == 'vote':
            # Format: group_vote_TYPE
            vote_type = data.split('_')[2]
            await self._handle_vote_callback(update, context, vote_type)
        elif action == 'finalize':
            # Format: group_finalize
            await self._handle_finalize_callback(update, context)
        elif action == 'select':
            # Format: group_select_INDEX
            index = int(data.split('_')[2])
            await self._handle_select_callback(update, context, index)
            
        return True
    
    async def _handle_vote_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, vote_type: str) -> None:
        """
        Handle vote callback in group chats.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
            vote_type: Type of vote (song, artist, album)
        """
        query = update.callback_query
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Check if there's an active poll
        if chat_id not in self.group_sessions or not self.group_sessions[chat_id]['current_poll']:
            await query.answer("لا يوجد تصويت نشط حالياً.")
            return
            
        # Get poll information
        poll = self.group_sessions[chat_id]['current_poll']
        
        if poll['status'] != 'voting':
            await query.answer("التصويت مغلق.")
            return
            
        # Record vote
        for vote_category in poll['votes']:
            # Remove user from other categories if they voted before
            if user_id in poll['votes'][vote_category]:
                poll['votes'][vote_category].remove(user_id)
                
        # Add user vote to selected category
        poll['votes'][vote_type].append(user_id)
        
        # Update poll message
        await self._update_poll_message(context, chat_id)
        
        await query.answer(f"تم التصويت لـ: {vote_type}")
    
    async def _handle_finalize_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle finalize callback in group chats.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
        """
        query = update.callback_query
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Check if there's an active poll
        if chat_id not in self.group_sessions or not self.group_sessions[chat_id]['current_poll']:
            await query.answer("لا يوجد تصويت نشط حالياً.")
            return
            
        # Get poll information
        poll = self.group_sessions[chat_id]['current_poll']
        
        # Only the initiator can finalize the poll
        if poll['initiator_id'] != user_id:
            await query.answer("فقط منشئ البحث يمكنه إنهاء التصويت.")
            return
            
        if poll['status'] != 'voting':
            await query.answer("التصويت مغلق بالفعل.")
            return
            
        # Determine the winning search type
        search_type, vote_count = self._get_winning_vote(poll['votes'])
        
        # Update poll status
        poll['status'] = 'searching'
        poll['search_type'] = search_type
        
        # Update poll message
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=poll['message_id'],
            text=f"🔍 بحث جماعي: \"{poll['query']}\"\n\n"
                f"تم إغلاق التصويت. النتيجة: البحث كـ {search_type} (عدد الأصوات: {vote_count}).\n"
                f"جاري البحث...",
            reply_markup=None
        )
        
        await query.answer("تم إنهاء التصويت وبدء البحث.")
        
        # Trigger the search
        # This would typically call your existing search functionality
        # For now, we'll just simulate it
        await self._simulate_search_results(context, chat_id)
    
    async def _handle_select_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, index: int) -> None:
        """
        Handle selection callback in group chats.
        
        Args:
            update: The update object from Telegram
            context: The context object from Telegram
            index: Index of the selected result
        """
        query = update.callback_query
        chat_id = update.effective_chat.id
        
        # Check if there's an active poll with results
        if chat_id not in self.group_sessions or not self.group_sessions[chat_id]['current_poll']:
            await query.answer("لا يوجد بحث نشط حالياً.")
            return
            
        # Get poll information
        poll = self.group_sessions[chat_id]['current_poll']
        
        if poll['status'] != 'completed' or 'results' not in poll:
            await query.answer("لم يتم العثور على نتائج بعد.")
            return
            
        # Check if the index is valid
        if index < 0 or index >= len(poll['results']):
            await query.answer("خيار غير صالح.")
            return
            
        # Get the selected result
        selected_result = poll['results'][index]
        
        await query.answer("جاري تحميل الغلاف...")
        
        # This would typically call your existing cover sending functionality
        # For now, we'll just simulate it
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎵 تم اختيار: {selected_result['title']} - {selected_result['artist']}\n\n"
                f"هنا سيتم إرسال صورة الغلاف بأعلى جودة."
        )
        
        # Store the result in the group's history
        if 'history' not in self.group_sessions[chat_id]:
            self.group_sessions[chat_id]['history'] = []
            
        self.group_sessions[chat_id]['history'].append({
            'query': poll['query'],
            'search_type': poll['search_type'],
            'selected': selected_result
        })
    
    def _create_search_type_keyboard(self) -> InlineKeyboardMarkup:
        """
        Create an inline keyboard for voting on search type.
        
        Returns:
            InlineKeyboardMarkup object
        """
        keyboard = [
            [
                InlineKeyboardButton("🎵 أغنية", callback_data="group_vote_song"),
                InlineKeyboardButton("👤 فنان", callback_data="group_vote_artist"),
                InlineKeyboardButton("💿 ألبوم", callback_data="group_vote_album")
            ],
            [
                InlineKeyboardButton("✅ إنهاء التصويت وبدء البحث", callback_data="group_finalize")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _update_poll_message(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
        """
        Update the poll message with current votes.
        
        Args:
            context: The context object from Telegram
            chat_id: Chat ID
        """
        # Get poll information
        poll = self.group_sessions[chat_id]['current_poll']
        
        # Count votes
        song_votes = len(poll['votes']['song'])
        artist_votes = len(poll['votes']['artist'])
        album_votes = len(poll['votes']['album'])
        
        # Update message
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=poll['message_id'],
            text=f"🔍 بحث جماعي: \"{poll['query']}\"\n\n"
                f"التصويت الحالي:\n"
                f"🎵 أغنية: {song_votes} صوت\n"
                f"👤 فنان: {artist_votes} صوت\n"
                f"💿 ألبوم: {album_votes} صوت\n\n"
                f"استخدم الأزرار أدناه للتصويت، أو أرسل /vote [نوع البحث]",
            reply_markup=self._create_search_type_keyboard()
        )
    
    def _get_winning_vote(self, votes: Dict[str, List[int]]) -> Tuple[str, int]:
        """
        Determine the winning search type based on votes.
        
        Args:
            votes: Dictionary of votes by category
            
        Returns:
            Tuple of (winning_type, vote_count)
        """
        vote_counts = {
            category: len(voters) for category, voters in votes.items()
        }
        
        # Find the category with the most votes
        winning_type = max(vote_counts, key=vote_counts.get)
        winning_count = vote_counts[winning_type]
        
        # If there's a tie, default to 'song'
        if list(vote_counts.values()).count(winning_count) > 1:
            # Check if 'song' is among the tied categories
            if vote_counts['song'] == winning_count:
                winning_type = 'song'
            # Otherwise, prioritize in order: artist, album
            elif vote_counts['artist'] == winning_count:
                winning_type = 'artist'
            else:
                winning_type = 'album'
        
        return winning_type, winning_count
    
    async def _simulate_search_results(self, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
        """
        Simulate search results for demonstration purposes.
        
        Args:
            context: The context object from Telegram
            chat_id: Chat ID
        """
        # Get poll information
        poll = self.group_sessions[chat_id]['current_poll']
        
        # Simulate some results
        results = [
            {
                'title': f"نتيجة 1 لـ {poll['query']}",
                'artist': 'فنان 1',
                'album': 'ألبوم 1',
                'cover_url': 'https://example.com/cover1.jpg'
            },
            {
                'title': f"نتيجة 2 لـ {poll['query']}",
                'artist': 'فنان 2',
                'album': 'ألبوم 2',
                'cover_url': 'https://example.com/cover2.jpg'
            },
            {
                'title': f"نتيجة 3 لـ {poll['query']}",
                'artist': 'فنان 3',
                'album': 'ألبوم 3',
                'cover_url': 'https://example.com/cover3.jpg'
            }
        ]
        
        # Update poll with results
        poll['status'] = 'completed'
        poll['results'] = results
        
        # Store in group results history
        self.group_sessions[chat_id]['results'].append({
            'query': poll['query'],
            'search_type': poll['search_type'],
            'count': len(results),
            'timestamp': context.bot.get_updates()[-1].message.date.timestamp() if context.bot.get_updates() else 0
        })
        
        # Create results keyboard
        keyboard = []
        for i, result in enumerate(results):
            keyboard.append([
                InlineKeyboardButton(
                    f"{result['title']} - {result['artist']}",
                    callback_data=f"group_select_{i}"
                )
            ])
        
        # Update message with results
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=poll['message_id'],
            text=f"🔍 نتائج البحث لـ \"{poll['query']}\" (كـ {poll['search_type']}):\n\n"
                f"تم العثور على {len(results)} نتيجة. اختر من القائمة أدناه:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
