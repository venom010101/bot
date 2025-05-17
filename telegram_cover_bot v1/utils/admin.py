"""
Admin module for the Telegram Cover Bot.
This module provides admin-only features like broadcasting messages and viewing user statistics.
"""
from typing import Dict, Any, List, Optional, Set
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio

class AdminManager:
    """Manager for admin-only features."""
    
    def __init__(self, admin_ids: List[int] = None):
        """
        Initialize the admin manager.
        
        Args:
            admin_ids: List of Telegram user IDs that have admin privileges
        """
        self.admin_ids = set(admin_ids) if admin_ids else set()
        self.users_data = {}  # Store user data: {user_id: {'username': str, 'first_name': str, 'last_name': str, 'last_active': timestamp}}
        self.broadcast_in_progress = False
        self.broadcast_status = {
            'total': 0,
            'sent': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None,
            'message': None
        }
    
    def is_admin(self, user_id: int) -> bool:
        """
        Check if a user is an admin.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if the user is an admin, False otherwise
        """
        return user_id in self.admin_ids
    
    def add_admin(self, user_id: int) -> bool:
        """
        Add a user to the admin list.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if the user was added, False if already an admin
        """
        if user_id in self.admin_ids:
            return False
        
        self.admin_ids.add(user_id)
        return True
    
    def remove_admin(self, user_id: int) -> bool:
        """
        Remove a user from the admin list.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if the user was removed, False if not an admin
        """
        if user_id not in self.admin_ids:
            return False
        
        self.admin_ids.remove(user_id)
        return True
    
    def track_user_activity(self, user_id: int, user_data: Dict[str, Any]) -> None:
        """
        Track user activity by updating their last active timestamp and user data.
        
        Args:
            user_id: Telegram user ID
            user_data: Dictionary with user data (username, first_name, last_name)
        """
        if user_id not in self.users_data:
            self.users_data[user_id] = {
                'username': user_data.get('username', None),
                'first_name': user_data.get('first_name', 'Unknown'),
                'last_name': user_data.get('last_name', ''),
                'last_active': time.time(),
                'first_seen': time.time()
            }
        else:
            # Update existing user data
            self.users_data[user_id]['last_active'] = time.time()
            
            # Update user info if provided
            if 'username' in user_data and user_data['username']:
                self.users_data[user_id]['username'] = user_data['username']
            if 'first_name' in user_data and user_data['first_name']:
                self.users_data[user_id]['first_name'] = user_data['first_name']
            if 'last_name' in user_data and user_data['last_name']:
                self.users_data[user_id]['last_name'] = user_data['last_name']
    
    def get_active_users(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get a list of active users within the specified time period.
        
        Args:
            days: Number of days to consider for activity
            
        Returns:
            List of dictionaries with user data
        """
        now = time.time()
        active_period = days * 24 * 60 * 60  # Convert days to seconds
        
        active_users = []
        for user_id, data in self.users_data.items():
            if now - data['last_active'] <= active_period:
                user_info = data.copy()
                user_info['user_id'] = user_id
                active_users.append(user_info)
        
        # Sort by last active time (most recent first)
        active_users.sort(key=lambda x: x['last_active'], reverse=True)
        
        return active_users
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get a list of all users.
        
        Returns:
            List of dictionaries with user data
        """
        all_users = []
        for user_id, data in self.users_data.items():
            user_info = data.copy()
            user_info['user_id'] = user_id
            all_users.append(user_info)
        
        # Sort by first seen time (oldest first)
        all_users.sort(key=lambda x: x['first_seen'])
        
        return all_users
    
    def get_user_ids(self) -> List[int]:
        """
        Get a list of all user IDs.
        
        Returns:
            List of user IDs
        """
        return list(self.users_data.keys())
    
    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Returns:
            Dictionary with user statistics
        """
        now = time.time()
        
        # Time periods in seconds
        day = 24 * 60 * 60
        week = 7 * day
        month = 30 * day
        
        # Count users active in different time periods
        active_today = 0
        active_week = 0
        active_month = 0
        
        for user_id, data in self.users_data.items():
            last_active = data['last_active']
            if now - last_active <= day:
                active_today += 1
            if now - last_active <= week:
                active_week += 1
            if now - last_active <= month:
                active_month += 1
        
        return {
            'total_users': len(self.users_data),
            'active_today': active_today,
            'active_week': active_week,
            'active_month': active_month
        }
    
    async def broadcast_message(self, message: str, bot, exclude_ids: Set[int] = None) -> Dict[str, Any]:
        """
        Broadcast a message to all users.
        
        Args:
            message: Message to broadcast
            bot: Telegram bot instance
            exclude_ids: Set of user IDs to exclude from broadcast
            
        Returns:
            Dictionary with broadcast results
        """
        if self.broadcast_in_progress:
            return {'success': False, 'error': 'Broadcast already in progress'}
        
        self.broadcast_in_progress = True
        self.broadcast_status = {
            'total': 0,
            'sent': 0,
            'failed': 0,
            'start_time': time.time(),
            'end_time': None,
            'message': message
        }
        
        exclude_ids = exclude_ids or set()
        user_ids = [uid for uid in self.users_data.keys() if uid not in exclude_ids]
        self.broadcast_status['total'] = len(user_ids)
        
        for user_id in user_ids:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="Markdown"
                )
                self.broadcast_status['sent'] += 1
                
                # Add a small delay to avoid hitting rate limits
                await asyncio.sleep(0.05)
            except Exception as e:
                self.broadcast_status['failed'] += 1
                print(f"Failed to send broadcast to {user_id}: {str(e)}")
        
        self.broadcast_status['end_time'] = time.time()
        self.broadcast_in_progress = False
        
        return {
            'success': True,
            'total': self.broadcast_status['total'],
            'sent': self.broadcast_status['sent'],
            'failed': self.broadcast_status['failed'],
            'duration': self.broadcast_status['end_time'] - self.broadcast_status['start_time']
        }
    
    def get_broadcast_status(self) -> Dict[str, Any]:
        """
        Get the status of the current or last broadcast.
        
        Returns:
            Dictionary with broadcast status
        """
        status = self.broadcast_status.copy()
        
        if status['start_time']:
            status['start_time_formatted'] = datetime.fromtimestamp(status['start_time']).strftime('%Y-%m-%d %H:%M:%S')
        
        if status['end_time']:
            status['end_time_formatted'] = datetime.fromtimestamp(status['end_time']).strftime('%Y-%m-%d %H:%M:%S')
            status['duration'] = status['end_time'] - status['start_time']
            status['duration_formatted'] = f"{status['duration']:.2f} seconds"
        
        status['in_progress'] = self.broadcast_in_progress
        
        return status
