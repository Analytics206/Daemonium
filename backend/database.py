"""
Database connection and management for Daemonium API
"""

import logging
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import asyncio

from .config import Settings, get_mongodb_connection_string

logger = logging.getLogger(__name__)

class DatabaseManager:
    """MongoDB database manager for async operations"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.collections: Dict[str, AsyncIOMotorCollection] = {}
        
        # Collection names based on project structure
        self.collection_names = [
            "aphorisms",
            "book_summaries", 
            "books",
            "chat_blueprints",
            "conversation_logic",
            "discussion_hooks",
            "idea_summaries",
            "modern_adaptations",
            "persona_cores",
            "philosopher_bios",
            "philosopher_bots",
            "philosopher_summaries",
            "philosophers",
            "philosophy_schools",
            "philosophy_themes",
            "top_ten_ideas"
        ]
    
    async def connect(self) -> None:
        """Connect to MongoDB"""
        try:
            connection_string = get_mongodb_connection_string(self.settings)
            logger.info(f"Connecting to MongoDB at {self.settings.mongodb_host}:{self.settings.mongodb_port}")
            
            self.client = AsyncIOMotorClient(
                connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            self.database = self.client[self.settings.mongodb_database]
            
            # Initialize collection references
            for collection_name in self.collection_names:
                self.collections[collection_name] = self.database[collection_name]
            
            logger.info("Successfully connected to MongoDB")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            if not self.client:
                return False
            
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, int]:
        """Get document counts for all collections"""
        stats = {}
        
        for collection_name in self.collection_names:
            try:
                collection = self.collections[collection_name]
                count = await collection.count_documents({})
                stats[collection_name] = count
            except Exception as e:
                logger.error(f"Failed to get stats for {collection_name}: {e}")
                stats[collection_name] = 0
        
        return stats
    
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get a collection by name"""
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")
        return self.collections[collection_name]
    
    # Philosopher-related methods
    async def get_philosophers(self, skip: int = 0, limit: int = 100, is_active_chat: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get philosophers with pagination and optional active chat filter"""
        collection = self.get_collection("philosophers")
        
        filter_query = {}
        if is_active_chat is not None:
            filter_query["is_active_chat"] = is_active_chat
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_philosopher_by_id(self, philosopher_id: str) -> Optional[Dict[str, Any]]:
        """Get philosopher by ID"""
        collection = self.get_collection("philosophers")
        return await collection.find_one({"_id": philosopher_id})
    
    # Philosophy Schools methods
    async def get_philosophy_schools(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get philosophy schools with pagination"""
        collection = self.get_collection("philosophy_schools")
        cursor = collection.find({}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_philosophy_school_by_id(self, school_id: str) -> Optional[Dict[str, Any]]:
        """Get philosophy school by ID"""
        collection = self.get_collection("philosophy_schools")
        return await collection.find_one({"_id": school_id})
    
    async def search_philosophy_schools(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search philosophy schools by name, category, or content"""
        collection = self.get_collection("philosophy_schools")
        
        # Create a text search filter
        search_filter = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"category": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}},
                {"core_principles": {"$regex": query, "$options": "i"}}
            ]
        }
        
        cursor = collection.find(search_filter).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_philosophers_by_school(self, school_id: str, skip: int = 0, limit: int = 100, is_active_chat: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get philosophers belonging to a specific school with optional active chat filter"""
        collection = self.get_collection("philosophers")
        
        filter_query = {"school_id": school_id}
        if is_active_chat is not None:
            filter_query["is_active_chat"] = is_active_chat
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_philosopher_with_school(self, philosopher_id: str) -> Optional[Dict[str, Any]]:
        """Get philosopher with their associated school information"""
        philosopher = await self.get_philosopher_by_id(philosopher_id)
        if not philosopher:
            return None
        
        result = {"philosopher": philosopher, "school": None}
        
        # Get school information if school_id exists
        if philosopher.get("school_id"):
            school = await self.get_philosophy_school_by_id(f"school_{philosopher['school_id']}")
            result["school"] = school
        
        return result
    
    async def search_philosophers(self, query: str, limit: int = 10, is_active_chat: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search philosophers by author name or content with optional active chat filter"""
        collection = self.get_collection("philosophers")
        
        # Create a text search filter - prioritize author field
        search_filter = {
            "$or": [
                {"author": {"$regex": query, "$options": "i"}},
                {"philosopher": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}}
            ]
        }
        
        # Add is_active_chat filter if specified
        if is_active_chat is not None:
            search_filter["is_active_chat"] = is_active_chat
        
        cursor = collection.find(search_filter).limit(limit)
        return await cursor.to_list(length=limit)
    
    # Methods to get data by author across collections
    async def get_aphorisms_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get aphorisms by author"""
        collection = self.get_collection("aphorisms")
        cursor = collection.find({"author": author}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_book_summaries_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get book summaries by author"""
        collection = self.get_collection("book_summaries")
        cursor = collection.find({"author": author}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_top_ideas_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get top ten ideas by author"""
        collection = self.get_collection("top_ten_ideas")
        cursor = collection.find({"author": author}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_idea_summaries_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get idea summaries by author"""
        collection = self.get_collection("idea_summaries")
        cursor = collection.find({"author": author}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_philosophy_themes_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get philosophy themes by author"""
        collection = self.get_collection("philosophy_themes")
        cursor = collection.find({"author": author}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_philosopher_summaries_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get philosopher summaries by author"""
        collection = self.get_collection("philosopher_summaries")
        cursor = collection.find({"author": author}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    # Book-related methods
    async def get_books(self, skip: int = 0, limit: int = 100, author: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get books with pagination and optional author filter"""
        collection = self.get_collection("books")
        
        filter_query = {}
        if author:
            filter_query["metadata.author"] = {"$regex": author, "$options": "i"}
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_book_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Get book by ID"""
        collection = self.get_collection("books")
        return await collection.find_one({"_id": book_id})
    
    async def get_book_summaries(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get book summaries with pagination"""
        collection = self.get_collection("book_summaries")
        cursor = collection.find({}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    # Aphorism-related methods
    async def get_aphorisms(self, skip: int = 0, limit: int = 100, philosopher: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get aphorisms with pagination and optional philosopher filter"""
        collection = self.get_collection("aphorisms")
        
        filter_query = {}
        if philosopher:
            filter_query["philosopher"] = {"$regex": philosopher, "$options": "i"}
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_random_aphorisms(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get random aphorisms"""
        collection = self.get_collection("aphorisms")
        cursor = collection.aggregate([{"$sample": {"size": count}}])
        return await cursor.to_list(length=count)
    
    # Ideas-related methods
    async def get_top_ideas(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get top ten ideas with pagination"""
        collection = self.get_collection("top_ten_ideas")
        cursor = collection.find({}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_idea_summaries(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get idea summaries with pagination"""
        collection = self.get_collection("idea_summaries")
        cursor = collection.find({}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    # Chat-related methods
    async def get_chat_blueprints(self, philosopher: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get chat blueprints, optionally filtered by philosopher"""
        collection = self.get_collection("chat_blueprints")
        
        filter_query = {}
        if philosopher:
            filter_query["philosopher"] = {"$regex": philosopher, "$options": "i"}
        
        cursor = collection.find(filter_query)
        return await cursor.to_list(length=None)
    
    async def get_philosopher_bots(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get philosopher bot configurations"""
        collection = self.get_collection("philosopher_bots")
        cursor = collection.find({}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_conversation_logic(self, philosopher: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get conversation logic, optionally filtered by philosopher"""
        collection = self.get_collection("conversation_logic")
        
        filter_query = {}
        if philosopher:
            filter_query["philosopher"] = {"$regex": philosopher, "$options": "i"}
        
        cursor = collection.find(filter_query)
        return await cursor.to_list(length=None)
    
    # Search methods
    async def global_search(self, query: str, limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """Search across multiple collections"""
        results = {}
        
        # Search in key collections
        search_collections = [
            "philosopher_summaries",
            "books", 
            "book_summaries",
            "aphorisms",
            "top_ten_ideas",
            "idea_summaries"
        ]
        
        for collection_name in search_collections:
            try:
                collection = self.get_collection(collection_name)
                
                # Create text search filter based on collection structure
                if collection_name == "philosopher_summaries":
                    search_filter = {
                        "$or": [
                            {"author": {"$regex": query, "$options": "i"}},
                            {"summary": {"$regex": query, "$options": "i"}},
                            {"content": {"$regex": query, "$options": "i"}}
                        ]
                    }
                elif collection_name in ["books", "book_summaries"]:
                    search_filter = {
                        "$or": [
                            {"metadata.title": {"$regex": query, "$options": "i"}},
                            {"metadata.author": {"$regex": query, "$options": "i"}},
                            {"content": {"$regex": query, "$options": "i"}}
                        ]
                    }
                elif collection_name == "aphorisms":
                    search_filter = {
                        "$or": [
                            {"author": {"$regex": query, "$options": "i"}},
                            {"text": {"$regex": query, "$options": "i"}},
                            {"context": {"$regex": query, "$options": "i"}}
                        ]
                    }
                else:
                    # Generic search for other collections that use author field
                    search_filter = {
                        "$or": [
                            {"author": {"$regex": query, "$options": "i"}},
                            {"title": {"$regex": query, "$options": "i"}},
                            {"description": {"$regex": query, "$options": "i"}},
                            {"content": {"$regex": query, "$options": "i"}}
                        ]
                    }
                
                cursor = collection.find(search_filter).limit(limit // len(search_collections))
                collection_results = await cursor.to_list(length=limit // len(search_collections))
                
                if collection_results:
                    results[collection_name] = collection_results
                    
            except Exception as e:
                logger.error(f"Search failed for collection {collection_name}: {e}")
                continue
        
        return results
