"""
Command handlers for the Telegram Cover Bot.
This module provides handlers for basic commands like /start and /help.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from typing import Optional
from config import ADMIN_IDS

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, translation_manager) -> None:
    """
    Handle the /start command.
    
    Args:
        update: The update object from Telegram
        context: The context object from Telegram
        translation_manager: Translation manager instance
    """
    user = update.effective_user
    user_lang = "ar"  # Default to Arabic
    
    # Get translation function
    def _(text):
        return translation_manager.get_text(text, user_lang) if translation_manager else text
    
    # Welcome message with developer username
    welcome_text = _(
        "👋 مرحباً بك في بوت جلب أغلفة الأغاني!\n\n"
        "🎵 يمكنك البحث عن أغلفة الأغاني بجودة عالية من خلال:\n"
        "• إرسال اسم الأغنية مباشرة\n"
        "• استخدام الأمر /search متبوعاً باسم الأغنية\n"
        "• استخدام الأمر /artist للبحث عن فنان\n"
        "• استخدام الأمر /album للبحث عن ألبوم\n"
        "• إرسال ملف صوتي لاستخراج الغلاف منه\n\n"
        "ℹ️ استخدم الأمر /help للحصول على قائمة كاملة بالأوامر المتاحة\n\n"
        "🧑‍💻 تم تطوير البوت بواسطة @T8_WY"
    )
    
    # Create language selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data="lang:ar"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang:en"),
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang:es")
        ]
    ]
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, translation_manager) -> None:
    """
    Handle the /help command.
    
    Args:
        update: The update object from Telegram
        context: The context object from Telegram
        translation_manager: Translation manager instance
    """
    user = update.effective_user
    user_lang = "ar"  # Default to Arabic
    
    # Get translation function
    def _(text):
        return translation_manager.get_text(text, user_lang) if translation_manager else text
    
    # Check if user is admin
    is_admin = user.id in ADMIN_IDS
    
    # Help message introduction
    help_text = _(
        "📋 قائمة الأوامر المتاحة في البوت\n\n"
        "عند استخدام أمر /help ستظهر لك قائمة بجميع الأوامر المتاحة مع شرح بسيط لكل أمر.\n\n"
        "🔍 أوامر البحث:\n"
    )
    
    # Search commands
    help_text += _(
        "• /search [اسم الأغنية] - البحث عن أغنية\n"
        "• /artist [اسم الفنان] - البحث عن فنان\n"
        "• /album [اسم الألبوم] - البحث عن ألبوم\n\n"
    )
    
    # General commands
    help_text += _(
        "🛠️ أوامر عامة:\n"
        "• /start - بدء استخدام البوت\n"
        "• /help - عرض هذه القائمة\n"
        "• /language - تغيير لغة البوت\n"
        "• /stats - عرض إحصائيات الاستخدام\n"
        "• /share - مشاركة البوت مع الآخرين\n\n"
    )
    
    # Group commands
    help_text += _(
        "👥 أوامر المجموعات:\n"
        "• /groupsearch - بدء بحث جماعي في المجموعة\n"
        "• /vote - التصويت على نوع البحث\n"
        "• /results - عرض نتائج آخر بحث جماعي\n\n"
    )
    
    # Audio feature
    help_text += _(
        "🎵 ميزة الملفات الصوتية:\n"
        "• أرسل أي ملف صوتي للبوت وسيقوم باستخراج الغلاف منه\n"
        "• إذا كان الغلاف منخفض الجودة، سيبحث البوت عن غلاف بجودة أعلى\n\n"
    )
    
    # Admin commands (only shown to admins)
    if is_admin:
        help_text += _(
            "⚙️ أوامر المطور (خاصة بك فقط):\n"
            "• /broadcast [نص الرسالة] - إرسال رسالة إذاعة لجميع المستخدمين\n"
            "• /users - عرض إحصائيات المستخدمين النشطين\n"
            "• /database - إدارة قاعدة بيانات التفاعلات\n\n"
        )
    
    # Tips
    help_text += _(
        "💡 نصائح:\n"
        "• يمكنك إرسال اسم الأغنية أو الفنان أو الألبوم مباشرة بدون أوامر\n"
        "• للحصول على أفضل النتائج، استخدم اسم الأغنية مع اسم الفنان\n"
        "• يمكنك تغيير اللغة في أي وقت باستخدام الأمر /language\n"
    )
    
    await update.message.reply_text(help_text)

def create_results_keyboard(results, current_index, page_size, translation_manager=None, user_lang=None):
    """
    Create an inline keyboard for navigating search results.
    Args:
        results: List of search results
        current_index: Current index in the results list
        page_size: Number of results per page
        translation_manager: Translation manager instance (optional)
        user_lang: User language code (optional)
    Returns:
        InlineKeyboardMarkup object
    """
    keyboard = []
    # Add buttons for each result
    for i in range(current_index, min(current_index + page_size, len(results))):
        result = results[i]
        title = result.get("title", "Unknown")
        artist = result.get("artist", "Unknown")
        display_text = f"{title} - {artist}"
        # Truncate if too long
        if len(display_text) > 30:
            display_text = display_text[:27] + "..."
        keyboard.append([
            InlineKeyboardButton(
                text=display_text,
                callback_data=f"select_{i}"
            )
        ])
    # Add navigation buttons if needed
    nav_buttons = []
    if current_index > 0:
        prev_text = translation_manager.get_text('btn_prev', user_lang) if translation_manager and user_lang else "⬅️ السابق"
        nav_buttons.append(
            InlineKeyboardButton(
                text=prev_text,
                callback_data=f"prev_{max(0, current_index - page_size)}"
            )
        )
    if current_index + page_size < len(results):
        next_text = translation_manager.get_text('btn_next', user_lang) if translation_manager and user_lang else "التالي ➡️"
        nav_buttons.append(
            InlineKeyboardButton(
                text=next_text,
                callback_data=f"next_{current_index + page_size}"
            )
        )
    if nav_buttons:
        keyboard.append(nav_buttons)
    return InlineKeyboardMarkup(keyboard)
