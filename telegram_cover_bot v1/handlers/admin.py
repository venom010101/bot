"""
Admin command handlers for the Telegram Cover Bot.
This module provides admin-only commands for broadcasting messages, viewing user statistics,
and accessing the interaction database.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

from utils.admin import AdminManager
from utils.translation import TranslationManager
from utils.database import InteractionDatabase


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           admin_manager: AdminManager,
                           translation_manager: Optional[TranslationManager] = None,
                           database: Optional[InteractionDatabase] = None) -> None:
    """
    Handle the /broadcast command (admin only).
    
    Args:
        update: The update object from Telegram
        context: The context object from Telegram
        admin_manager: Admin manager instance
        translation_manager: Translation manager instance (optional)
        database: Interaction database instance (optional)
    """
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Check if user is admin
    if not admin_manager.is_admin(user_id):
        await update.message.reply_text("⛔ هذا الأمر متاح للمطور فقط.")
        return
    
    # Log command if database is available
    if database:
        user_data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        database.log_command("broadcast", context.args, user_id, user_data)
    
    # Get broadcast message
    message_text = " ".join(context.args).strip() if context.args else ""
    
    if not message_text:
        # Show broadcast help
        await update.message.reply_text(
            "📢 *أمر الإذاعة الجماعية*\n\n"
            "يتيح هذا الأمر إرسال رسالة لجميع مستخدمي البوت.\n\n"
            "*الاستخدام:*\n"
            "`/broadcast نص الرسالة`\n\n"
            "يمكنك استخدام تنسيق Markdown في الرسالة.\n"
            "مثال: `/broadcast مرحباً بالجميع! 👋 تم إضافة ميزة جديدة للبوت.`",
            parse_mode="HTML"
        )
        return
    
    # Confirm broadcast
    keyboard = [
        [
            InlineKeyboardButton("✅ تأكيد الإرسال", callback_data="broadcast_confirm"),
            InlineKeyboardButton("❌ إلغاء", callback_data="broadcast_cancel")
        ]
    ]
    
    # Store message in user data for later use
    context.user_data['broadcast_message'] = message_text
    
    # Get user stats for confirmation message
    user_stats = admin_manager.get_user_stats()
    
    await update.message.reply_text(
        f"📢 *تأكيد الإذاعة الجماعية*\n\n"
        f"سيتم إرسال الرسالة التالية إلى {user_stats['total_users']} مستخدم:\n\n"
        f"```\n{message_text}\n```\n\n"
        f"هل أنت متأكد من إرسال هذه الرسالة؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                       admin_manager: AdminManager,
                       translation_manager: Optional[TranslationManager] = None,
                       database: Optional[InteractionDatabase] = None) -> None:
    """
    Handle the /users command (admin only).
    
    Args:
        update: The update object from Telegram
        context: The context object from Telegram
        admin_manager: Admin manager instance
        translation_manager: Translation manager instance (optional)
        database: Interaction database instance (optional)
    """
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Check if user is admin
    if not admin_manager.is_admin(user_id):
        await update.message.reply_text("⛔ هذا الأمر متاح للمطور فقط.")
        return
    
    # Log command if database is available
    if database:
        user_data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        database.log_command("users", context.args, user_id, user_data)
    
    # Get user statistics
    user_stats = admin_manager.get_user_stats()
    
    # Create statistics message
    stats_message = (
        f"📊 *إحصائيات المستخدمين*\n\n"
        f"👥 إجمالي المستخدمين: {user_stats['total_users']}\n"
        f"🟢 نشط اليوم: {user_stats['active_today']}\n"
        f"📅 نشط هذا الأسبوع: {user_stats['active_week']}\n"
        f"📆 نشط هذا الشهر: {user_stats['active_month']}\n\n"
    )
    
    # Create keyboard with options
    keyboard = [
        [
            InlineKeyboardButton("👥 عرض المستخدمين النشطين", callback_data="users_active"),
            InlineKeyboardButton("📋 عرض جميع المستخدمين", callback_data="users_all")
        ],
        [
            InlineKeyboardButton("📊 تصدير البيانات", callback_data="users_export")
        ]
    ]
    
    await update.message.reply_text(
        stats_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def database_command(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                          admin_manager: AdminManager,
                          database: InteractionDatabase) -> None:
    """
    Handle the /database command (admin only).
    
    Args:
        update: The update object from Telegram
        context: The context object from Telegram
        admin_manager: Admin manager instance
        database: Interaction database instance
    """
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Check if user is admin
    if not admin_manager.is_admin(user_id):
        await update.message.reply_text("⛔ هذا الأمر متاح للمطور فقط.")
        return
    
    # Log command
    user_data = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name
    }
    database.log_command("database", context.args, user_id, user_data)
    
    # Get database statistics
    stats = database.get_stats()
    
    # Format top commands
    top_commands = ""
    for cmd, count in stats.get("top_commands", {}).items():
        top_commands += f"/{cmd}: {count} مرة\n"
    
    if not top_commands:
        top_commands = "لا توجد بيانات بعد"
    
    # Format top searches
    top_searches = ""
    for search, count in stats.get("top_searches", {}).items():
        top_searches += f"{search}: {count} مرة\n"
    
    if not top_searches:
        top_searches = "لا توجد بيانات بعد"
    
    # Create statistics message
    stats_message = (
        f"📊 *إحصائيات قاعدة البيانات*\n\n"
        f"👥 عدد المستخدمين: {stats.get('users_count', 0)}\n"
        f"👥 عدد المجموعات: {stats.get('groups_count', 0)}\n"
        f"🔢 إجمالي التفاعلات: {stats.get('total_interactions', 0)}\n\n"
        f"📈 *الأوامر الأكثر استخداماً:*\n{top_commands}\n\n"
        f"🔍 *عمليات البحث الأكثر شيوعاً:*\n{top_searches}\n\n"
    )
    
    # Create keyboard with options
    keyboard = [
        [
            InlineKeyboardButton("👤 تفاعلات المستخدمين", callback_data="db_users"),
            InlineKeyboardButton("👥 تفاعلات المجموعات", callback_data="db_groups")
        ],
        [
            InlineKeyboardButton("📊 تصدير البيانات", callback_data="db_export"),
            InlineKeyboardButton("🗑️ تنظيف البيانات القديمة", callback_data="db_clean")
        ]
    ]
    
    await update.message.reply_text(
        stats_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               admin_manager: AdminManager,
                               database: Optional[InteractionDatabase] = None) -> bool:
    """
    Handle admin-related callback queries.
    
    Args:
        update: The update object from Telegram
        context: The context object from Telegram
        admin_manager: Admin manager instance
        database: Interaction database instance (optional)
        
    Returns:
        True if the callback was handled, False otherwise
    """
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Check if user is admin
    if not admin_manager.is_admin(user_id):
        await query.answer("⛔ هذا الإجراء متاح للمطور فقط.")
        return False
    
    # Check if this is an admin-related callback
    if not (data.startswith('broadcast_') or data.startswith('users_') or data.startswith('db_')):
        return False
    
    # Log callback if database is available
    if database:
        user_data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        database.log_interaction("callback", {
            "callback_data": data,
            "user": user_data
        }, user_id)
    
    # Handle broadcast callbacks
    if data == 'broadcast_confirm':
        # Get the message from user data
        message = context.user_data.get('broadcast_message', '')
        
        if not message:
            await query.answer("❌ لم يتم العثور على رسالة للإذاعة.")
            await query.edit_message_text("❌ فشلت عملية الإذاعة: لم يتم العثور على رسالة.")
            return True
        
        # Show broadcasting status
        await query.answer("🔄 جاري بدء الإذاعة...")
        await query.edit_message_text(
            "🔄 *جاري إرسال الإذاعة الجماعية*\n\n"
            "يرجى الانتظار، قد تستغرق هذه العملية بعض الوقت...",
            parse_mode="HTML"
        )
        
        # Broadcast the message
        result = await admin_manager.broadcast_message(message, context.bot)
        
        # Show results
        if result['success']:
            success_rate = (result['sent'] / result['total']) * 100 if result['total'] > 0 else 0
            await query.edit_message_text(
                f"✅ *تمت الإذاعة بنجاح*\n\n"
                f"📊 الإحصائيات:\n"
                f"👥 إجمالي المستخدمين: {result['total']}\n"
                f"✅ تم الإرسال بنجاح: {result['sent']}\n"
                f"❌ فشل الإرسال: {result['failed']}\n"
                f"📈 نسبة النجاح: {success_rate:.1f}%\n"
                f"⏱ المدة: {result['duration']:.2f} ثانية",
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text(
                f"❌ *فشلت عملية الإذاعة*\n\n"
                f"السبب: {result.get('error', 'خطأ غير معروف')}",
                parse_mode="HTML"
            )
        
        # Clear the message from user data
        if 'broadcast_message' in context.user_data:
            del context.user_data['broadcast_message']
            
        return True
        
    elif data == 'broadcast_cancel':
        await query.answer("تم إلغاء الإذاعة.")
        await query.edit_message_text("❌ تم إلغاء الإذاعة الجماعية.")
        
        # Clear the message from user data
        if 'broadcast_message' in context.user_data:
            del context.user_data['broadcast_message']
            
        return True
    
    # Handle users callbacks
    elif data == 'users_active':
        # Get active users (last 7 days)
        active_users = admin_manager.get_active_users(days=7)
        
        if not active_users:
            await query.answer("لا يوجد مستخدمين نشطين في آخر 7 أيام.")
            return True
        
        # Format user list
        users_message = f"👥 *المستخدمين النشطين (آخر 7 أيام): {len(active_users)}*\n\n"
        
        for i, user in enumerate(active_users[:20], 1):  # Limit to 20 users to avoid message too long
            username = f"@{user['username']}" if user['username'] else "بدون معرف"
            name = f"{user['first_name']} {user['last_name']}".strip()
            last_active = datetime.fromtimestamp(user['last_active']).strftime('%Y-%m-%d %H:%M')
            users_message += f"{i}. {name} ({username}) - آخر نشاط: {last_active}\n"
        
        if len(active_users) > 20:
            users_message += f"\n... و{len(active_users) - 20} مستخدم آخر"
        
        # Create back button
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="users_back")]]
        
        await query.edit_message_text(
            users_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        await query.answer()
        return True
        
    elif data == 'users_all':
        # Get all users
        all_users = admin_manager.get_all_users()
        
        if not all_users:
            await query.answer("لا يوجد مستخدمين مسجلين.")
            return True
        
        # Format user list
        users_message = f"👥 *جميع المستخدمين: {len(all_users)}*\n\n"
        
        for i, user in enumerate(all_users[:20], 1):  # Limit to 20 users to avoid message too long
            username = f"@{user['username']}" if user['username'] else "بدون معرف"
            name = f"{user['first_name']} {user['last_name']}".strip()
            first_seen = datetime.fromtimestamp(user['first_seen']).strftime('%Y-%m-%d')
            users_message += f"{i}. {name} ({username}) - أول استخدام: {first_seen}\n"
        
        if len(all_users) > 20:
            users_message += f"\n... و{len(all_users) - 20} مستخدم آخر"
        
        # Create back button
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="users_back")]]
        
        await query.edit_message_text(
            users_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        await query.answer()
        return True
        
    elif data == 'users_export':
        # Get all users
        all_users = admin_manager.get_all_users()
        
        if not all_users:
            await query.answer("لا يوجد مستخدمين مسجلين.")
            return True
        
        # Format user list as CSV
        csv_content = "user_id,username,first_name,last_name,first_seen,last_active\n"
        
        for user in all_users:
            username = user['username'] or ""
            first_name = user['first_name'] or ""
            last_name = user['last_name'] or ""
            first_seen = datetime.fromtimestamp(user['first_seen']).strftime('%Y-%m-%d %H:%M:%S')
            last_active = datetime.fromtimestamp(user['last_active']).strftime('%Y-%m-%d %H:%M:%S')
            
            csv_content += f"{user['user_id']},{username},{first_name},{last_name},{first_seen},{last_active}\n"
        
        # Send CSV file
        from io import BytesIO
        
        csv_bytes = BytesIO(csv_content.encode('utf-8'))
        csv_bytes.name = 'users_export.csv'
        
        await context.bot.send_document(
            chat_id=user_id,
            document=csv_bytes,
            filename='users_export.csv',
            caption="📊 تصدير بيانات المستخدمين"
        )
        
        await query.answer("تم إرسال ملف التصدير.")
        return True
        
    elif data == 'users_back':
        # Get user statistics
        user_stats = admin_manager.get_user_stats()
        
        # Create statistics message
        stats_message = (
            f"📊 *إحصائيات المستخدمين*\n\n"
            f"👥 إجمالي المستخدمين: {user_stats['total_users']}\n"
            f"🟢 نشط اليوم: {user_stats['active_today']}\n"
            f"📅 نشط هذا الأسبوع: {user_stats['active_week']}\n"
            f"📆 نشط هذا الشهر: {user_stats['active_month']}\n\n"
        )
        
        # Create keyboard with options
        keyboard = [
            [
                InlineKeyboardButton("👥 عرض المستخدمين النشطين", callback_data="users_active"),
                InlineKeyboardButton("📋 عرض جميع المستخدمين", callback_data="users_all")
            ],
            [
                InlineKeyboardButton("📊 تصدير البيانات", callback_data="users_export")
            ]
        ]
        
        await query.edit_message_text(
            stats_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        await query.answer()
        return True
    
    # Handle database callbacks
    elif data == 'db_users' and database:
        # Ask for user ID
        await query.edit_message_text(
            "👤 *تفاعلات المستخدمين*\n\n"
            "الرجاء إرسال معرف المستخدم (User ID) للاطلاع على تفاعلاته.\n"
            "يمكنك الحصول على معرف المستخدم من قائمة المستخدمين النشطين.",
            parse_mode="HTML"
        )
        
        # Set user state to wait for user ID
        context.user_data['admin_state'] = 'waiting_for_user_id'
        
        await query.answer()
        return True
        
    elif data == 'db_groups' and database:
        # Ask for group ID
        await query.edit_message_text(
            "👥 *تفاعلات المجموعات*\n\n"
            "الرجاء إرسال معرف المجموعة (Group ID) للاطلاع على تفاعلاتها.",
            parse_mode="HTML"
        )
        
        # Set user state to wait for group ID
        context.user_data['admin_state'] = 'waiting_for_group_id'
        
        await query.answer()
        return True
        
    elif data == 'db_export' and database:
        # Create export directory
        export_dir = os.path.join(database.base_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        # Get database statistics
        stats = database.get_stats()
        
        # Create statistics file
        stats_file = os.path.join(export_dir, "stats_export.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        # Send statistics file
        await context.bot.send_document(
            chat_id=user_id,
            document=open(stats_file, 'rb'),
            filename='stats_export.json',
            caption="📊 تصدير إحصائيات قاعدة البيانات"
        )
        
        await query.answer("تم إرسال ملف الإحصائيات.")
        return True
        
    elif data == 'db_clean' and database:
        # Confirm cleaning
        keyboard = [
            [
                InlineKeyboardButton("✅ تأكيد التنظيف (30 يوم)", callback_data="db_clean_confirm_30"),
                InlineKeyboardButton("❌ إلغاء", callback_data="db_clean_cancel")
            ],
            [
                InlineKeyboardButton("تنظيف البيانات الأقدم من 60 يوم", callback_data="db_clean_confirm_60"),
                InlineKeyboardButton("تنظيف البيانات الأقدم من 90 يوم", callback_data="db_clean_confirm_90")
            ]
        ]
        
        await query.edit_message_text(
            "🗑️ *تنظيف البيانات القديمة*\n\n"
            "هل أنت متأكد من رغبتك في تنظيف البيانات القديمة؟\n"
            "سيتم حذف جميع التفاعلات الأقدم من المدة المحددة.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        await query.answer()
        return True
        
    elif data.startswith('db_clean_confirm_') and database:
        # Get days from callback data
        days = int(data.split('_')[-1])
        
        # Clean old data
        deleted_count = database.clear_old_data(days=days)
        
        await query.edit_message_text(
            f"✅ *تم تنظيف البيانات القديمة*\n\n"
            f"تم حذف {deleted_count} ملف من البيانات الأقدم من {days} يوم.",
            parse_mode="HTML"
        )
        
        await query.answer(f"تم حذف {deleted_count} ملف.")
        return True
        
    elif data == 'db_clean_cancel':
        # Get database statistics
        stats = database.get_stats()
        
        # Format top commands
        top_commands = ""
        for cmd, count in stats.get("top_commands", {}).items():
            top_commands += f"/{cmd}: {count} مرة\n"
        
        if not top_commands:
            top_commands = "لا توجد بيانات بعد"
        
        # Format top searches
        top_searches = ""
        for search, count in stats.get("top_searches", {}).items():
            top_searches += f"{search}: {count} مرة\n"
        
        if not top_searches:
            top_searches = "لا توجد بيانات بعد"
        
        # Create statistics message
        stats_message = (
            f"📊 *إحصائيات قاعدة البيانات*\n\n"
            f"👥 عدد المستخدمين: {stats.get('users_count', 0)}\n"
            f"👥 عدد المجموعات: {stats.get('groups_count', 0)}\n"
            f"🔢 إجمالي التفاعلات: {stats.get('total_interactions', 0)}\n\n"
            f"📈 *الأوامر الأكثر استخداماً:*\n{top_commands}\n\n"
            f"🔍 *عمليات البحث الأكثر شيوعاً:*\n{top_searches}\n\n"
        )
        
        # Create keyboard with options
        keyboard = [
            [
                InlineKeyboardButton("👤 تفاعلات المستخدمين", callback_data="db_users"),
                InlineKeyboardButton("👥 تفاعلات المجموعات", callback_data="db_groups")
            ],
            [
                InlineKeyboardButton("📊 تصدير البيانات", callback_data="db_export"),
                InlineKeyboardButton("🗑️ تنظيف البيانات القديمة", callback_data="db_clean")
            ]
        ]
        
        await query.edit_message_text(
            stats_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        await query.answer("تم إلغاء عملية التنظيف.")
        return True
    
    return False


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              admin_manager: AdminManager,
                              database: InteractionDatabase) -> bool:
    """
    Handle admin-related messages (e.g., responses to admin prompts).
    
    Args:
        update: The update object from Telegram
        context: The context object from Telegram
        admin_manager: Admin manager instance
        database: Interaction database instance
        
    Returns:
        True if the message was handled, False otherwise
    """
    user_id = update.effective_user.id
    user = update.effective_user
    message_text = update.message.text
    
    # Check if user is admin
    if not admin_manager.is_admin(user_id):
        return False
    
    # Check if we're waiting for admin input
    admin_state = context.user_data.get('admin_state')
    
    if not admin_state:
        return False
    
    # Log interaction
    user_data = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name
    }
    
    # Handle different admin states
    if admin_state == 'waiting_for_user_id':
        # Try to parse user ID
        try:
            target_user_id = int(message_text.strip())
            
            # Get user interactions
            interactions = database.get_user_interactions(target_user_id, limit=10)
            
            if not interactions:
                await update.message.reply_text(
                    f"❌ لا توجد تفاعلات مسجلة للمستخدم {target_user_id}."
                )
                context.user_data.pop('admin_state', None)
                return True
            
            # Get user stats
            user_stats = database.get_user_stats(target_user_id)
            
            # Format interactions
            interactions_message = f"👤 *تفاعلات المستخدم {target_user_id}*\n\n"
            interactions_message += f"إجمالي التفاعلات: {user_stats.get('interactions', 0)}\n\n"
            
            interactions_message += "*آخر 10 تفاعلات:*\n"
            for i, interaction in enumerate(interactions, 1):
                time_str = interaction.get("formatted_time", "")
                type_str = interaction.get("type", "")
                
                details = ""
                if type_str == "command":
                    cmd = interaction.get("command", "")
                    details = f"الأمر: /{cmd}"
                elif type_str == "search":
                    query = interaction.get("query", "")
                    search_type = interaction.get("search_type", "")
                    details = f"بحث عن {search_type}: {query}"
                elif type_str == "result":
                    query = interaction.get("query", "")
                    selected = interaction.get("selected_result", {})
                    if selected:
                        title = selected.get("title", "")
                        artist = selected.get("artist", "")
                        details = f"نتيجة: {title} - {artist}"
                    else:
                        details = f"نتيجة لـ: {query}"
                
                interactions_message += f"{i}. {time_str} - {type_str} - {details}\n"
            
            # Create export button
            keyboard = [
                [
                    InlineKeyboardButton(f"📊 تصدير تفاعلات المستخدم {target_user_id}", 
                                        callback_data=f"db_export_user_{target_user_id}")
                ]
            ]
            
            await update.message.reply_text(
                interactions_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            
            # Clear admin state
            context.user_data.pop('admin_state', None)
            
        except ValueError:
            await update.message.reply_text(
                "❌ معرف المستخدم غير صالح. الرجاء إدخال رقم صحيح."
            )
        
        return True
        
    elif admin_state == 'waiting_for_group_id':
        # Try to parse group ID
        try:
            target_group_id = int(message_text.strip())
            
            # Get group interactions
            interactions = database.get_group_interactions(target_group_id, limit=10)
            
            if not interactions:
                await update.message.reply_text(
                    f"❌ لا توجد تفاعلات مسجلة للمجموعة {target_group_id}."
                )
                context.user_data.pop('admin_state', None)
                return True
            
            # Get group stats
            group_stats = database.get_group_stats(target_group_id)
            
            # Format interactions
            interactions_message = f"👥 *تفاعلات المجموعة {target_group_id}*\n\n"
            interactions_message += f"إجمالي التفاعلات: {group_stats.get('interactions', 0)}\n\n"
            
            interactions_message += "*آخر 10 تفاعلات:*\n"
            for i, interaction in enumerate(interactions, 1):
                time_str = interaction.get("formatted_time", "")
                type_str = interaction.get("type", "")
                
                details = ""
                if type_str == "command":
                    cmd = interaction.get("command", "")
                    user_info = interaction.get("user", {})
                    username = user_info.get("username", "")
                    username_str = f"@{username}" if username else "بدون معرف"
                    details = f"الأمر: /{cmd} من {username_str}"
                elif type_str == "search":
                    query = interaction.get("query", "")
                    search_type = interaction.get("search_type", "")
                    user_info = interaction.get("user", {})
                    username = user_info.get("username", "")
                    username_str = f"@{username}" if username else "بدون معرف"
                    details = f"بحث عن {search_type}: {query} من {username_str}"
                
                interactions_message += f"{i}. {time_str} - {type_str} - {details}\n"
            
            # Create export button
            keyboard = [
                [
                    InlineKeyboardButton(f"📊 تصدير تفاعلات المجموعة {target_group_id}", 
                                        callback_data=f"db_export_group_{target_group_id}")
                ]
            ]
            
            await update.message.reply_text(
                interactions_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            
            # Clear admin state
            context.user_data.pop('admin_state', None)
            
        except ValueError:
            await update.message.reply_text(
                "❌ معرف المجموعة غير صالح. الرجاء إدخال رقم صحيح."
            )
        
        return True
    
    return False
