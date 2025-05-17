"""
Utility module for session management in the Telegram Cover Bot.
"""
from typing import Dict, Any, Optional
import time


class SessionManager:
    """
    Manages user sessions for the Telegram bot.
    Stores user preferences and recent searches.
    """
    
    def __init__(self):
        """Initialize the session manager."""
        self.sessions = {}
        self.session_timeout = 3600  # 1 hour timeout
    
    def get_session(self, user_id: int) -> Dict[str, Any]:
        """
        Get or create a session for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            User session dictionary
        """
        # Clean expired sessions
        self._clean_expired_sessions()
        
        # Create session if it doesn't exist
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                'last_activity': time.time(),
                'recent_searches': [],
                'preferences': {
                    'high_quality': True,
                    'max_results': 5
                }
            }
        else:
            # Update last activity time
            self.sessions[user_id]['last_activity'] = time.time()
            
        return self.sessions[user_id]
    
    def update_session(self, user_id: int, data: Dict[str, Any]) -> None:
        """
        Update a user session with new data.
        
        Args:
            user_id: Telegram user ID
            data: New data to update in the session
        """
        session = self.get_session(user_id)
        session.update(data)
        session['last_activity'] = time.time()
    
    def add_recent_search(self, user_id: int, query: str, search_type: str) -> None:
        """
        Add a recent search to a user's session.
        
        Args:
            user_id: Telegram user ID
            query: Search query
            search_type: Type of search (song, artist, album)
        """
        session = self.get_session(user_id)
        
        # Add to recent searches, limited to 10 items
        recent_searches = session.get('recent_searches', [])
        
        # Add new search at the beginning
        recent_searches.insert(0, {
            'query': query,
            'type': search_type,
            'timestamp': time.time()
        })
        
        # Limit to 10 recent searches
        session['recent_searches'] = recent_searches[:10]
    
    def get_recent_searches(self, user_id: int, limit: int = 5) -> list:
        """
        Get recent searches for a user.
        
        Args:
            user_id: Telegram user ID
            limit: Maximum number of recent searches to return
            
        Returns:
            List of recent searches
        """
        session = self.get_session(user_id)
        return session.get('recent_searches', [])[:limit]
    
    def get_preference(self, user_id: int, key: str) -> Optional[Any]:
        """
        Get a user preference.
        
        Args:
            user_id: Telegram user ID
            key: Preference key
            
        Returns:
            Preference value or None if not found
        """
        session = self.get_session(user_id)
        return session.get('preferences', {}).get(key)
    
    def set_preference(self, user_id: int, key: str, value: Any) -> None:
        """
        Set a user preference.
        
        Args:
            user_id: Telegram user ID
            key: Preference key
            value: Preference value
        """
        session = self.get_session(user_id)
        
        if 'preferences' not in session:
            session['preferences'] = {}
            
        session['preferences'][key] = value
    
    def _clean_expired_sessions(self) -> None:
        """Clean expired sessions."""
        current_time = time.time()
        expired_users = []
        
        for user_id, session in self.sessions.items():
            if current_time - session['last_activity'] > self.session_timeout:
                expired_users.append(user_id)
                
        for user_id in expired_users:
            del self.sessions[user_id]
