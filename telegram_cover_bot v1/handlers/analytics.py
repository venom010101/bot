"""
Analytics command handlers for the Telegram Cover Bot.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, Any

from utils.analytics import AnalyticsManager
from utils.translation import TranslationManager


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                       analytics_manager: AnalyticsManager,
                       translation_manager: TranslationManager) -> None:
    """
    Handle the /stats command.
    
    Args:
        update: The update object from Telegram
        context: The context object from Telegram
        analytics_manager: Analytics manager instance
        translation_manager: Translation manager instance
    """
    user_id = update.effective_user.id
    user_lang = translation_manager.get_user_language(user_id)
    
    # Get user statistics
    user_stats = analytics_manager.get_user_stats(user_id)
    
    if not user_stats:
        await update.message.reply_text(
            translation_manager.get_text('no_stats', user_lang)
        )
        return
    
    # Format statistics message
    stats_message = f"{translation_manager.get_text('stats_title', user_lang)}\n\n"
    
    # Add user-specific statistics
    stats_message += f"{translation_manager.get_text('stats_searches', user_lang, count=user_stats['total_searches'])}\n"
    stats_message += f"{translation_manager.get_text('stats_songs', user_lang, count=user_stats['song_searches'])}\n"
    stats_message += f"{translation_manager.get_text('stats_artists', user_lang, count=user_stats['artist_searches'])}\n"
    stats_message += f"{translation_manager.get_text('stats_albums', user_lang, count=user_stats['album_searches'])}\n"
    
    # Add most searched item if available
    if user_stats['most_searched']:
        stats_message += f"{translation_manager.get_text('stats_most_searched', user_lang, item=user_stats['most_searched'])}\n"
    
    # Add success rate
    stats_message += f"{translation_manager.get_text('stats_success_rate', user_lang, rate=round(user_stats['success_rate'], 1))}\n"
    
    # Get recent search history
    search_history = analytics_manager.get_user_search_history(user_id, limit=1)
    if search_history:
        last_search = search_history[0]
        stats_message += f"{translation_manager.get_text('stats_last_search', user_lang, query=last_search['query'], time=last_search['time'])}\n"
    
    # Create keyboard for more detailed statistics
    keyboard = [
        [
            InlineKeyboardButton(
                translation_manager.get_text('btn_search_history', user_lang),
                callback_data="stats_history"
            )
        ],
        [
            InlineKeyboardButton(
                translation_manager.get_text('btn_global_stats', user_lang),
                callback_data="stats_global"
            )
        ]
    ]
    
    await update.message.reply_text(
        stats_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               analytics_manager: AnalyticsManager,
                               translation_manager: TranslationManager) -> bool:
    """
    Handle statistics-related callback queries.
    
    Args:
        update: The update object from Telegram
        context: The context object from Telegram
        analytics_manager: Analytics manager instance
        translation_manager: Translation manager instance
        
    Returns:
        True if the callback was handled, False otherwise
    """
    query = update.callback_query
    data = query.data
    
    # Check if this is a stats-related callback
    if not data.startswith('stats_'):
        return False
    
    user_id = update.effective_user.id
    user_lang = translation_manager.get_user_language(user_id)
    
    # Handle different stats callbacks
    if data == 'stats_history':
        await _show_search_history(query, analytics_manager, translation_manager, user_id, user_lang)
    elif data == 'stats_global':
        await _show_global_stats(query, analytics_manager, translation_manager, user_lang)
    
    return True


async def _show_search_history(query, analytics_manager, translation_manager, user_id, user_lang):
    """Show user's search history."""
    # Get search history
    history = analytics_manager.get_user_search_history(user_id, limit=10)
    
    if not history:
        await query.answer(translation_manager.get_text('no_search_history', user_lang))
        return
    
    # Format history message
    history_message = f"{translation_manager.get_text('search_history_title', user_lang)}\n\n"
    
    for i, item in enumerate(history, 1):
        # Format search type
        search_type = translation_manager.get_text(f"search_type_{item['search_type']}", user_lang)
        
        # Format success/failure
        result = translation_manager.get_text('search_success' if item['successful'] else 'search_failure', user_lang)
        
        history_message += f"{i}. \"{item['query']}\" ({search_type}) - {result} - {item['time']}\n"
    
    # Create back button
    keyboard = [
        [
            InlineKeyboardButton(
                translation_manager.get_text('btn_back', user_lang),
                callback_data="stats_back"
            )
        ]
    ]
    
    await query.edit_message_text(
        history_message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    await query.answer()


async def _show_global_stats(query, analytics_manager, translation_manager, user_lang):
    """Show global statistics."""
    # Get global statistics
    global_stats = analytics_manager.get_global_stats()
    
    # Format statistics message
    stats_message = f"{translation_manager.get_text('global_stats_title', user_lang)}\n\n"
    
    # Add global statistics
    stats_message += f"{translation_manager.get_text('global_total_searches', user_lang, count=global_stats['total_searches'])}\n"
    stats_message += f"{translation_manager.get_text('global_unique_users', user_lang, count=global_stats['unique_users'])}\n"
    stats_message += f"{translation_manager.get_text('global_success_rate', user_lang, rate=round(global_stats['success_rate'], 1))}\n"
    
    # Add uptime
    stats_message += f"{translation_manager.get_text('global_uptime', user_lang, uptime=global_stats['uptime_formatted'])}\n"
    
    # Add search type distribution
    distribution = analytics_manager.get_search_type_distribution()
    stats_message += f"\n{translation_manager.get_text('search_type_distribution', user_lang)}\n"
    stats_message += f"{translation_manager.get_text('search_type_song', user_lang)}: {round(distribution['song'], 1)}%\n"
    stats_message += f"{translation_manager.get_text('search_type_artist', user_lang)}: {round(distribution['artist'], 1)}%\n"
    stats_message += f"{translation_manager.get_text('search_type_album', user_lang)}: {round(distribution['album'], 1)}%\n"
    
    # Add trending searches
    trending = analytics_manager.get_trending_searches(limit=5)
    if trending:
        stats_message += f"\n{translation_manager.get_text('trending_searches', user_lang)}\n"
        for i, (query, count) in enumerate(trending, 1):
            stats_message += f"{i}. \"{query}\" ({count} {translation_manager.get_text('searches', user_lang)})\n"
    
    # Create back button
    keyboard = [
        [
            InlineKeyboardButton(
                translation_manager.get_text('btn_back', user_lang),
                callback_data="stats_back"
            )
        ]
    ]
    
    await query.edit_message_text(
        stats_message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    await query.answer()
