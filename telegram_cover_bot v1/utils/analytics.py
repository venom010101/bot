"""
Analytics module for the Telegram Cover Bot.
This module provides advanced user analytics and statistics.
"""
from typing import Dict, Any, List, Optional, Tuple
import time
from collections import Counter
from datetime import datetime


class AnalyticsManager:
    """Manager for user analytics and statistics."""
    
    def __init__(self):
        """Initialize the analytics manager."""
        self.user_stats = {}  # User-specific statistics
        self.global_stats = {
            'total_searches': 0,
            'song_searches': 0,
            'artist_searches': 0,
            'album_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'search_queries': [],
            'start_time': time.time()
        }
        self.search_history = []  # List of all searches
    
    def record_search(self, user_id: int, query: str, search_type: str, successful: bool) -> None:
        """
        Record a search event.
        
        Args:
            user_id: Telegram user ID
            query: Search query
            search_type: Type of search (song, artist, album)
            successful: Whether the search was successful
        """
        # Initialize user stats if not exists
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'total_searches': 0,
                'song_searches': 0,
                'artist_searches': 0,
                'album_searches': 0,
                'successful_searches': 0,
                'failed_searches': 0,
                'search_queries': [],
                'first_search_time': time.time(),
                'last_search_time': time.time()
            }
        
        # Update user stats
        self.user_stats[user_id]['total_searches'] += 1
        self.user_stats[user_id]['last_search_time'] = time.time()
        
        if search_type == 'song':
            self.user_stats[user_id]['song_searches'] += 1
        elif search_type == 'artist':
            self.user_stats[user_id]['artist_searches'] += 1
        elif search_type == 'album':
            self.user_stats[user_id]['album_searches'] += 1
        
        if successful:
            self.user_stats[user_id]['successful_searches'] += 1
        else:
            self.user_stats[user_id]['failed_searches'] += 1
            
        self.user_stats[user_id]['search_queries'].append(query)
        
        # Update global stats
        self.global_stats['total_searches'] += 1
        
        if search_type == 'song':
            self.global_stats['song_searches'] += 1
        elif search_type == 'artist':
            self.global_stats['artist_searches'] += 1
        elif search_type == 'album':
            self.global_stats['album_searches'] += 1
        
        if successful:
            self.global_stats['successful_searches'] += 1
        else:
            self.global_stats['failed_searches'] += 1
            
        self.global_stats['search_queries'].append(query)
        
        # Add to search history
        self.search_history.append({
            'user_id': user_id,
            'query': query,
            'search_type': search_type,
            'successful': successful,
            'timestamp': time.time()
        })
    
    def get_user_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dictionary with user statistics or None if user not found
        """
        if user_id not in self.user_stats:
            return None
            
        stats = self.user_stats[user_id].copy()
        
        # Calculate success rate
        total = stats['successful_searches'] + stats['failed_searches']
        stats['success_rate'] = (stats['successful_searches'] / total * 100) if total > 0 else 0
        
        # Get most searched query
        if stats['search_queries']:
            counter = Counter(stats['search_queries'])
            stats['most_searched'] = counter.most_common(1)[0][0]
        else:
            stats['most_searched'] = None
            
        # Format timestamps
        stats['first_search'] = datetime.fromtimestamp(stats['first_search_time']).strftime('%Y-%m-%d %H:%M:%S')
        stats['last_search'] = datetime.fromtimestamp(stats['last_search_time']).strftime('%Y-%m-%d %H:%M:%S')
        
        return stats
    
    def get_global_stats(self) -> Dict[str, Any]:
        """
        Get global statistics.
        
        Returns:
            Dictionary with global statistics
        """
        stats = self.global_stats.copy()
        
        # Calculate success rate
        total = stats['successful_searches'] + stats['failed_searches']
        stats['success_rate'] = (stats['successful_searches'] / total * 100) if total > 0 else 0
        
        # Get most searched query
        if stats['search_queries']:
            counter = Counter(stats['search_queries'])
            stats['most_searched'] = counter.most_common(1)[0][0]
        else:
            stats['most_searched'] = None
            
        # Calculate uptime
        stats['uptime'] = time.time() - stats['start_time']
        stats['uptime_formatted'] = self._format_duration(stats['uptime'])
        
        # Count unique users
        stats['unique_users'] = len(self.user_stats)
        
        return stats
    
    def get_user_search_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get search history for a specific user.
        
        Args:
            user_id: Telegram user ID
            limit: Maximum number of history items to return
            
        Returns:
            List of search history items
        """
        # Filter history by user ID and sort by timestamp (newest first)
        history = [item for item in self.search_history if item['user_id'] == user_id]
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Format timestamps and limit results
        for item in history:
            item['time'] = datetime.fromtimestamp(item['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            
        return history[:limit]
    
    def get_most_active_users(self, limit: int = 10) -> List[Tuple[int, int]]:
        """
        Get the most active users.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of tuples (user_id, search_count)
        """
        # Sort users by total searches
        users = [(user_id, stats['total_searches']) for user_id, stats in self.user_stats.items()]
        users.sort(key=lambda x: x[1], reverse=True)
        
        return users[:limit]
    
    def get_trending_searches(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get trending search queries.
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of tuples (query, count)
        """
        # Count queries and get the most common
        counter = Counter(self.global_stats['search_queries'])
        return counter.most_common(limit)
    
    def get_search_type_distribution(self) -> Dict[str, float]:
        """
        Get distribution of search types.
        
        Returns:
            Dictionary with search type percentages
        """
        total = self.global_stats['total_searches']
        if total == 0:
            return {'song': 0, 'artist': 0, 'album': 0}
            
        return {
            'song': (self.global_stats['song_searches'] / total * 100),
            'artist': (self.global_stats['artist_searches'] / total * 100),
            'album': (self.global_stats['album_searches'] / total * 100)
        }
    
    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in seconds to a human-readable string.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 or not parts:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
            
        return ", ".join(parts)
