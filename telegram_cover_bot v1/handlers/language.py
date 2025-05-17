"""
Language command handlers for the Telegram Cover Bot.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, Any

from utils.translation import TranslationManager


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE, translation_manager: TranslationManager) -> None:
    """
    Handle the /language command.
    
    Args:
        update: The update object from Telegram
        context: The context object from Telegram
        translation_manager: Translation manager instance
    """
    user_id = update.effective_user.id
    user_lang = translation_manager.get_user_language(user_id)
    
    # Create keyboard with language options
    keyboard = []
    row = []
    
    # Get available languages
    languages = translation_manager.get_available_languages()
    
    # Create buttons for each language
    for i, lang in enumerate(languages):
        # Add checkmark to current language
        button_text = f"{lang['name']} ✓" if lang['code'] == user_lang else lang['name']
        
        # Add button to current row
        row.append(InlineKeyboardButton(button_text, callback_data=f"lang_{lang['code']}"))
        
        # Create a new row every 2 buttons
        if (i + 1) % 2 == 0 or i == len(languages) - 1:
            keyboard.append(row)
            row = []
    
    # Send message with language selection keyboard
    await update.message.reply_text(
        translation_manager.get_text('select_language', user_lang),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, translation_manager: TranslationManager) -> bool:
    """
    Handle language selection callback.
    
    Args:
        update: The update object from Telegram
        context: The context object from Telegram
        translation_manager: Translation manager instance
        
    Returns:
        True if the callback was handled, False otherwise
    """
    query = update.callback_query
    data = query.data
    
    # Check if this is a language callback
    if not data.startswith('lang_'):
        return False
        
    # Extract the language code
    lang_code = data.split('_')[1]
    user_id = update.effective_user.id
    
    # Set the user's language
    if translation_manager.set_user_language(user_id, lang_code):
        # Get the language name
        languages = translation_manager.get_available_languages()
        lang_name = next((lang['name'] for lang in languages if lang['code'] == lang_code), lang_code)
        
        # Notify the user
        await query.answer(f"Language changed to {lang_name}")
        
        # Update the message
        await query.edit_message_text(
            translation_manager.get_text('language_changed', lang_code)
        )
    else:
        await query.answer("Language not supported")
        
    return True
