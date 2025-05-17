"""
Main entry point for the Telegram Cover Bot.
"""
import logging
import os
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import telegram

from config import TELEGRAM_TOKEN, ADMIN_IDS
from utils.session import SessionManager
from utils.translation import TranslationManager
from utils.analytics import AnalyticsManager
from utils.social_sharing import SocialSharingManager
from utils.admin import AdminManager
from utils.database import InteractionDatabase
from handlers.commands import start_command, help_command
from handlers.search import SearchHandler
from handlers.group_support import GroupSupportHandler
from handlers.language import language_command, handle_language_callback
from handlers.analytics import stats_command, handle_stats_callback
from handlers.admin import broadcast_command, users_command, database_command, handle_admin_callback, handle_admin_message
from handlers.audio import AudioHandler


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def setup_commands(application):
    """Set up bot commands in the menu."""
    commands = [
        BotCommand("start", "بدء استخدام البوت"),
        BotCommand("help", "عرض المساعدة"),
        BotCommand("search", "البحث عن أغنية"),
        BotCommand("artist", "البحث عن فنان"),
        BotCommand("album", "البحث عن ألبوم"),
        BotCommand("language", "تغيير اللغة"),
        BotCommand("stats", "عرض إحصائيات الاستخدام"),
        BotCommand("share", "مشاركة البوت"),
        BotCommand("groupsearch", "بدء بحث جماعي في المجموعة"),
        BotCommand("vote", "التصويت على نوع البحث"),
        BotCommand("results", "عرض نتائج آخر بحث جماعي"),
    ]
    
    # Add admin commands for admin users
    admin_commands = commands + [
        BotCommand("broadcast", "إرسال رسالة إذاعة لجميع المستخدمين"),
        BotCommand("users", "عرض إحصائيات المستخدمين"),
        BotCommand("database", "إدارة قاعدة بيانات التفاعلات"),
    ]
    
    # Set regular commands for all users
    await application.bot.set_my_commands(commands)
    
    # Set admin commands for admin users
    for admin_id in ADMIN_IDS:
        try:
            await application.bot.set_my_commands(
                admin_commands,
                scope=telegram.BotCommandScopeChat(chat_id=admin_id)
            )
        except Exception as e:
            logger.error(f"Failed to set admin commands for {admin_id}: {e}")


async def track_user(update: Update, context: ContextTypes.DEFAULT_TYPE, admin_manager: AdminManager) -> None:
    """Track user activity."""
    user = update.effective_user
    if user:
        user_data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        admin_manager.track_user_activity(user.id, user_data)


def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Initialize managers
    session_manager = SessionManager()
    translation_manager = TranslationManager()
    analytics_manager = AnalyticsManager()
    admin_manager = AdminManager(admin_ids=ADMIN_IDS)
    
    # Initialize database
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    database = InteractionDatabase(base_dir=data_dir)
    
    # Get bot username for social sharing
    bot_username = ""
    
    async def post_init(application):
        """Post-initialization tasks."""
        nonlocal bot_username
        bot_info = await application.bot.get_me()
        bot_username = bot_info.username
        
        # Set up commands
        await setup_commands(application)
    
    application.post_init = post_init
    
    # Initialize handlers
    search_handler = SearchHandler(session_manager, translation_manager, analytics_manager, database)
    group_handler = GroupSupportHandler(session_manager)
    audio_handler = AudioHandler(session_manager, translation_manager, analytics_manager, database)
    
    # Initialize social sharing manager (after getting bot username)
    social_sharing_manager = None
    
    async def handle_share_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /share command."""
        nonlocal social_sharing_manager
        if social_sharing_manager is None:
            social_sharing_manager = SocialSharingManager(bot_username, translation_manager)
        await social_sharing_manager.share_command(update, context)
        
        # Track user activity
        await track_user(update, context, admin_manager)
        
        # Log command
        user = update.effective_user
        user_data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        database.log_command("share", context.args, user.id, user_data, 
                           update.effective_chat.id if update.effective_chat.type != "private" else None)
    
    # User tracking middleware
    async def user_activity_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Track user activity for all updates."""
        await track_user(update, context, admin_manager)
        
    # Register middleware
    application.add_handler(
        MessageHandler(filters.ALL, user_activity_middleware, block=False),
        group=-1  # Make sure it runs before all other handlers
    )
    
    # Register command handlers with logging
    async def wrapped_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Wrapped start command with logging."""
        user = update.effective_user
        user_data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        database.log_command("start", context.args, user.id, user_data, 
                           update.effective_chat.id if update.effective_chat.type != "private" else None)
        await start_command(update, context, translation_manager)
    
    async def wrapped_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Wrapped help command with logging."""
        user = update.effective_user
        user_data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        database.log_command("help", context.args, user.id, user_data, 
                           update.effective_chat.id if update.effective_chat.type != "private" else None)
        await help_command(update, context, translation_manager)
    
    async def wrapped_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Wrapped language command with logging."""
        user = update.effective_user
        user_data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        database.log_command("language", context.args, user.id, user_data, 
                           update.effective_chat.id if update.effective_chat.type != "private" else None)
        await language_command(update, context, translation_manager)
    
    async def wrapped_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Wrapped stats command with logging."""
        user = update.effective_user
        user_data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        database.log_command("stats", context.args, user.id, user_data, 
                           update.effective_chat.id if update.effective_chat.type != "private" else None)
        await stats_command(update, context, analytics_manager, translation_manager)
    
    # Register command handlers
    application.add_handler(CommandHandler("start", wrapped_start_command))
    application.add_handler(CommandHandler("help", wrapped_help_command))
    application.add_handler(CommandHandler("search", search_handler.handle_song_search))
    application.add_handler(CommandHandler("artist", search_handler.handle_artist_search))
    application.add_handler(CommandHandler("album", search_handler.handle_album_search))
    application.add_handler(CommandHandler("language", wrapped_language_command))
    application.add_handler(CommandHandler("stats", wrapped_stats_command))
    application.add_handler(CommandHandler("share", handle_share_command))
    
    # Register admin command handlers
    application.add_handler(CommandHandler("broadcast", lambda update, context: 
                                         broadcast_command(update, context, admin_manager, translation_manager, database)))
    application.add_handler(CommandHandler("users", lambda update, context: 
                                         users_command(update, context, admin_manager, translation_manager, database)))
    application.add_handler(CommandHandler("database", lambda update, context: 
                                         database_command(update, context, admin_manager, database)))
    
    # Register group-specific command handlers
    application.add_handler(CommandHandler("groupsearch", group_handler.handle_group_command))
    application.add_handler(CommandHandler("vote", group_handler.handle_group_command))
    application.add_handler(CommandHandler("results", group_handler.handle_group_command))
    
    # Register callback query handler for inline keyboards
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries."""
        # Log callback
        user = update.effective_user
        user_data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        database.log_interaction("callback", {
            "callback_data": update.callback_query.data,
            "user": user_data
        }, user.id, update.effective_chat.id if update.effective_chat.type != "private" else None)
        
        # Try each handler in order until one handles the callback
        if await handle_language_callback(update, context, translation_manager):
            return
        if await handle_stats_callback(update, context, analytics_manager, translation_manager):
            return
        if await handle_admin_callback(update, context, admin_manager, database):
            return
        if await audio_handler.handle_audio_callback(update, context):
            return
        if await group_handler.handle_callback_query(update, context):
            return
        await search_handler.handle_callback_query(update, context)
        
        # Track user activity
        await track_user(update, context, admin_manager)
    
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Register message handler for admin responses
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages."""
        # Try admin message handler first
        if await handle_admin_message(update, context, admin_manager, database):
            return
        
        # If not handled by admin handler, use text search
        await search_handler.handle_text_search(update, context)
    
    # Register message handler for direct text search
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register audio file handler
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, audio_handler.handle_audio_file))

    # Start the Bot
    application.run_polling()
    
    logger.info("Bot started successfully!")


if __name__ == "__main__":
    main()
