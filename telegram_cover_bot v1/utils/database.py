"""
Database module for the Telegram Cover Bot.
This module provides functionality for storing user interactions in separate folders.
"""
import os
import json
import time
from datetime import datetime
import shutil
from typing import Dict, Any, List, Optional, Union
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class InteractionDatabase:
    """Database for storing user interactions."""
    
    def __init__(self, base_dir: str = "data"):
        """
        Initialize the interaction database.
        
        Args:
            base_dir: Base directory for storing data
        """
        self.base_dir = base_dir
        self.users_dir = os.path.join(base_dir, "users")
        self.groups_dir = os.path.join(base_dir, "groups")
        self.stats_file = os.path.join(base_dir, "stats.json")
        
        # Create directories if they don't exist
        os.makedirs(self.users_dir, exist_ok=True)
        os.makedirs(self.groups_dir, exist_ok=True)
        
        # Initialize stats
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict[str, Any]:
        """
        Load statistics from file.
        
        Returns:
            Dictionary with statistics
        """
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading stats: {e}")
        
        # Default stats
        return {
            "total_interactions": 0,
            "users": {},
            "groups": {},
            "commands": {},
            "searches": {},
            "last_updated": time.time()
        }
    
    def _save_stats(self) -> None:
        """Save statistics to file."""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def _get_user_dir(self, user_id: int) -> str:
        """
        Get directory for a specific user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Path to user directory
        """
        user_dir = os.path.join(self.users_dir, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    
    def _get_group_dir(self, group_id: int) -> str:
        """
        Get directory for a specific group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Path to group directory
        """
        group_dir = os.path.join(self.groups_dir, str(group_id))
        os.makedirs(group_dir, exist_ok=True)
        return group_dir
    
    def log_interaction(self, 
                       interaction_type: str, 
                       data: Dict[str, Any], 
                       user_id: Optional[int] = None, 
                       group_id: Optional[int] = None) -> None:
        """
        Log an interaction.
        
        Args:
            interaction_type: Type of interaction (e.g., 'command', 'search', 'result')
            data: Dictionary with interaction data
            user_id: Telegram user ID (optional)
            group_id: Telegram group ID (optional)
        """
        timestamp = time.time()
        formatted_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d_%H-%M-%S')
        
        # Add timestamp to data
        interaction_data = data.copy()
        interaction_data["timestamp"] = timestamp
        interaction_data["formatted_time"] = formatted_time
        interaction_data["type"] = interaction_type
        
        # Update stats
        self.stats["total_interactions"] += 1
        self.stats["last_updated"] = timestamp
        
        # Update command stats
        if interaction_type == "command":
            command = data.get("command", "unknown")
            if command not in self.stats["commands"]:
                self.stats["commands"][command] = 0
            self.stats["commands"][command] += 1
        
        # Update search stats
        if interaction_type == "search":
            query = data.get("query", "unknown")
            search_type = data.get("search_type", "unknown")
            search_key = f"{search_type}:{query}"
            if search_key not in self.stats["searches"]:
                self.stats["searches"][search_key] = 0
            self.stats["searches"][search_key] += 1
        
        # Log to user directory if user_id is provided
        if user_id:
            user_dir = self._get_user_dir(user_id)
            
            # Update user stats
            if str(user_id) not in self.stats["users"]:
                self.stats["users"][str(user_id)] = {
                    "interactions": 0,
                    "first_interaction": timestamp,
                    "last_interaction": timestamp
                }
            
            self.stats["users"][str(user_id)]["interactions"] += 1
            self.stats["users"][str(user_id)]["last_interaction"] = timestamp
            
            # Create interaction type directory
            type_dir = os.path.join(user_dir, interaction_type)
            os.makedirs(type_dir, exist_ok=True)
            
            # Save interaction data
            interaction_file = os.path.join(type_dir, f"{formatted_time}.json")
            try:
                with open(interaction_file, 'w', encoding='utf-8') as f:
                    json.dump(interaction_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error saving user interaction: {e}")
        
        # Log to group directory if group_id is provided
        if group_id:
            group_dir = self._get_group_dir(group_id)
            
            # Update group stats
            if str(group_id) not in self.stats["groups"]:
                self.stats["groups"][str(group_id)] = {
                    "interactions": 0,
                    "first_interaction": timestamp,
                    "last_interaction": timestamp
                }
            
            self.stats["groups"][str(group_id)]["interactions"] += 1
            self.stats["groups"][str(group_id)]["last_interaction"] = timestamp
            
            # Create interaction type directory
            type_dir = os.path.join(group_dir, interaction_type)
            os.makedirs(type_dir, exist_ok=True)
            
            # Save interaction data
            interaction_file = os.path.join(type_dir, f"{formatted_time}.json")
            try:
                with open(interaction_file, 'w', encoding='utf-8') as f:
                    json.dump(interaction_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error saving group interaction: {e}")
        
        # Save stats
        self._save_stats()
    
    def log_command(self, 
                   command: str, 
                   args: List[str], 
                   user_id: int, 
                   user_data: Dict[str, Any], 
                   group_id: Optional[int] = None) -> None:
        """
        Log a command interaction.
        
        Args:
            command: Command name
            args: Command arguments
            user_id: Telegram user ID
            user_data: User data (name, username, etc.)
            group_id: Telegram group ID (optional)
        """
        data = {
            "command": command,
            "args": args,
            "user": user_data
        }
        
        self.log_interaction("command", data, user_id, group_id)
    
    def log_search(self, 
                  query: str, 
                  search_type: str, 
                  user_id: int, 
                  user_data: Dict[str, Any], 
                  group_id: Optional[int] = None) -> None:
        """
        Log a search interaction.
        
        Args:
            query: Search query
            search_type: Type of search (song, artist, album)
            user_id: Telegram user ID
            user_data: User data (name, username, etc.)
            group_id: Telegram group ID (optional)
        """
        data = {
            "query": query,
            "search_type": search_type,
            "user": user_data
        }
        
        self.log_interaction("search", data, user_id, group_id)
    
    def log_result(self, 
                  query: str, 
                  search_type: str, 
                  results: List[Dict[str, Any]], 
                  selected_index: Optional[int], 
                  user_id: int, 
                  user_data: Dict[str, Any], 
                  group_id: Optional[int] = None) -> None:
        """
        Log a search result interaction.
        
        Args:
            query: Search query
            search_type: Type of search (song, artist, album)
            results: List of search results
            selected_index: Index of selected result (optional)
            user_id: Telegram user ID
            user_data: User data (name, username, etc.)
            group_id: Telegram group ID (optional)
        """
        data = {
            "query": query,
            "search_type": search_type,
            "results_count": len(results),
            "selected_index": selected_index,
            "user": user_data
        }
        
        # Add selected result if available
        if selected_index is not None and 0 <= selected_index < len(results):
            data["selected_result"] = results[selected_index]
        
        self.log_interaction("result", data, user_id, group_id)
    
    def log_image(self, 
                 image_url: str, 
                 image_data: Dict[str, Any], 
                 user_id: int, 
                 user_data: Dict[str, Any], 
                 group_id: Optional[int] = None) -> None:
        """
        Log an image interaction.
        
        Args:
            image_url: URL of the image
            image_data: Image metadata (dimensions, quality, etc.)
            user_id: Telegram user ID
            user_data: User data (name, username, etc.)
            group_id: Telegram group ID (optional)
        """
        data = {
            "image_url": image_url,
            "image_data": image_data,
            "user": user_data
        }
        
        self.log_interaction("image", data, user_id, group_id)
    
    def log_error(self, 
                 error_message: str, 
                 error_type: str, 
                 user_id: Optional[int] = None, 
                 user_data: Optional[Dict[str, Any]] = None, 
                 group_id: Optional[int] = None) -> None:
        """
        Log an error interaction.
        
        Args:
            error_message: Error message
            error_type: Type of error
            user_id: Telegram user ID (optional)
            user_data: User data (name, username, etc.) (optional)
            group_id: Telegram group ID (optional)
        """
        data = {
            "error_message": error_message,
            "error_type": error_type
        }
        
        if user_data:
            data["user"] = user_data
        
        self.log_interaction("error", data, user_id, group_id)
    
    def get_user_interactions(self, 
                             user_id: int, 
                             interaction_type: Optional[str] = None, 
                             limit: int = 100, 
                             offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get interactions for a specific user.
        
        Args:
            user_id: Telegram user ID
            interaction_type: Type of interaction to filter by (optional)
            limit: Maximum number of interactions to return
            offset: Offset for pagination
            
        Returns:
            List of interaction data dictionaries
        """
        user_dir = self._get_user_dir(user_id)
        interactions = []
        
        if interaction_type:
            # Get interactions of a specific type
            type_dir = os.path.join(user_dir, interaction_type)
            if os.path.exists(type_dir):
                interactions.extend(self._load_interactions_from_dir(type_dir))
        else:
            # Get all interactions
            for type_name in os.listdir(user_dir):
                type_dir = os.path.join(user_dir, type_name)
                if os.path.isdir(type_dir):
                    interactions.extend(self._load_interactions_from_dir(type_dir))
        
        # Sort by timestamp (newest first)
        interactions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Apply pagination
        return interactions[offset:offset+limit]
    
    def get_group_interactions(self, 
                              group_id: int, 
                              interaction_type: Optional[str] = None, 
                              limit: int = 100, 
                              offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get interactions for a specific group.
        
        Args:
            group_id: Telegram group ID
            interaction_type: Type of interaction to filter by (optional)
            limit: Maximum number of interactions to return
            offset: Offset for pagination
            
        Returns:
            List of interaction data dictionaries
        """
        group_dir = self._get_group_dir(group_id)
        interactions = []
        
        if interaction_type:
            # Get interactions of a specific type
            type_dir = os.path.join(group_dir, interaction_type)
            if os.path.exists(type_dir):
                interactions.extend(self._load_interactions_from_dir(type_dir))
        else:
            # Get all interactions
            for type_name in os.listdir(group_dir):
                type_dir = os.path.join(group_dir, type_name)
                if os.path.isdir(type_dir):
                    interactions.extend(self._load_interactions_from_dir(type_dir))
        
        # Sort by timestamp (newest first)
        interactions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Apply pagination
        return interactions[offset:offset+limit]
    
    def _load_interactions_from_dir(self, directory: str) -> List[Dict[str, Any]]:
        """
        Load all interaction files from a directory.
        
        Args:
            directory: Directory path
            
        Returns:
            List of interaction data dictionaries
        """
        interactions = []
        
        if not os.path.exists(directory):
            return interactions
        
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                file_path = os.path.join(directory, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        interaction = json.load(f)
                        interactions.append(interaction)
                except Exception as e:
                    logger.error(f"Error loading interaction file {file_path}: {e}")
        
        return interactions
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        # Update some stats before returning
        self.stats["users_count"] = len(self.stats["users"])
        self.stats["groups_count"] = len(self.stats["groups"])
        
        # Get top commands
        commands = sorted(self.stats["commands"].items(), key=lambda x: x[1], reverse=True)
        self.stats["top_commands"] = dict(commands[:10])
        
        # Get top searches
        searches = sorted(self.stats["searches"].items(), key=lambda x: x[1], reverse=True)
        self.stats["top_searches"] = dict(searches[:10])
        
        return self.stats
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dictionary with user statistics
        """
        user_dir = self._get_user_dir(user_id)
        user_stats = {
            "user_id": user_id,
            "interactions": 0,
            "commands": {},
            "searches": {},
            "results": {},
            "images": {},
            "errors": {}
        }
        
        # Count interactions by type
        for type_name in os.listdir(user_dir):
            type_dir = os.path.join(user_dir, type_name)
            if os.path.isdir(type_dir):
                interactions = self._load_interactions_from_dir(type_dir)
                user_stats[type_name] = len(interactions)
                user_stats["interactions"] += len(interactions)
                
                # Collect specific stats for each type
                if type_name == "command":
                    for interaction in interactions:
                        command = interaction.get("command", "unknown")
                        if command not in user_stats["commands"]:
                            user_stats["commands"][command] = 0
                        user_stats["commands"][command] += 1
                
                elif type_name == "search":
                    for interaction in interactions:
                        query = interaction.get("query", "unknown")
                        search_type = interaction.get("search_type", "unknown")
                        search_key = f"{search_type}:{query}"
                        if search_key not in user_stats["searches"]:
                            user_stats["searches"][search_key] = 0
                        user_stats["searches"][search_key] += 1
        
        return user_stats
    
    def get_group_stats(self, group_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Dictionary with group statistics
        """
        group_dir = self._get_group_dir(group_id)
        group_stats = {
            "group_id": group_id,
            "interactions": 0,
            "commands": {},
            "searches": {},
            "results": {},
            "images": {},
            "errors": {}
        }
        
        # Count interactions by type
        for type_name in os.listdir(group_dir):
            type_dir = os.path.join(group_dir, type_name)
            if os.path.isdir(type_dir):
                interactions = self._load_interactions_from_dir(type_dir)
                group_stats[type_name] = len(interactions)
                group_stats["interactions"] += len(interactions)
                
                # Collect specific stats for each type
                if type_name == "command":
                    for interaction in interactions:
                        command = interaction.get("command", "unknown")
                        if command not in group_stats["commands"]:
                            group_stats["commands"][command] = 0
                        group_stats["commands"][command] += 1
                
                elif type_name == "search":
                    for interaction in interactions:
                        query = interaction.get("query", "unknown")
                        search_type = interaction.get("search_type", "unknown")
                        search_key = f"{search_type}:{query}"
                        if search_key not in group_stats["searches"]:
                            group_stats["searches"][search_key] = 0
                        group_stats["searches"][search_key] += 1
        
        return group_stats
    
    def export_user_data(self, user_id: int, format: str = "json") -> str:
        """
        Export all data for a specific user.
        
        Args:
            user_id: Telegram user ID
            format: Export format ('json' or 'csv')
            
        Returns:
            Path to the exported file
        """
        user_dir = self._get_user_dir(user_id)
        export_dir = os.path.join(self.base_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_filename = f"user_{user_id}_export_{timestamp}.{format}"
        export_path = os.path.join(export_dir, export_filename)
        
        if format == "json":
            # Export as JSON
            all_interactions = []
            for type_name in os.listdir(user_dir):
                type_dir = os.path.join(user_dir, type_name)
                if os.path.isdir(type_dir):
                    all_interactions.extend(self._load_interactions_from_dir(type_dir))
            
            # Sort by timestamp
            all_interactions.sort(key=lambda x: x.get("timestamp", 0))
            
            # Write to file
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(all_interactions, f, ensure_ascii=False, indent=2)
        
        elif format == "csv":
            # Export as CSV
            import csv
            
            with open(export_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(["Timestamp", "Type", "Details"])
                
                # Write interactions
                for type_name in os.listdir(user_dir):
                    type_dir = os.path.join(user_dir, type_name)
                    if os.path.isdir(type_dir):
                        interactions = self._load_interactions_from_dir(type_dir)
                        for interaction in interactions:
                            timestamp = interaction.get("formatted_time", "")
                            details = json.dumps(interaction, ensure_ascii=False)
                            writer.writerow([timestamp, type_name, details])
        
        return export_path
    
    def clear_old_data(self, days: int = 30) -> int:
        """
        Clear data older than the specified number of days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of files deleted
        """
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        # Process user directories
        for user_id in os.listdir(self.users_dir):
            user_dir = os.path.join(self.users_dir, user_id)
            if os.path.isdir(user_dir):
                deleted_count += self._clear_old_data_from_dir(user_dir, cutoff_time)
        
        # Process group directories
        for group_id in os.listdir(self.groups_dir):
            group_dir = os.path.join(self.groups_dir, group_id)
            if os.path.isdir(group_dir):
                deleted_count += self._clear_old_data_from_dir(group_dir, cutoff_time)
        
        return deleted_count
    
    def _clear_old_data_from_dir(self, directory: str, cutoff_time: float) -> int:
        """
        Clear old data from a directory.
        
        Args:
            directory: Directory path
            cutoff_time: Cutoff timestamp
            
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        
        for type_name in os.listdir(directory):
            type_dir = os.path.join(directory, type_name)
            if os.path.isdir(type_dir):
                for filename in os.listdir(type_dir):
                    if filename.endswith(".json"):
                        file_path = os.path.join(type_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                interaction = json.load(f)
                                timestamp = interaction.get("timestamp", 0)
                                
                                if timestamp < cutoff_time:
                                    os.remove(file_path)
                                    deleted_count += 1
                        except Exception as e:
                            logger.error(f"Error processing file {file_path}: {e}")
        
        return deleted_count
