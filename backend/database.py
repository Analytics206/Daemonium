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
            "bibliography",
            "book_summary", 
            "books",
            "chat_blueprint",
            "conversation_logic",
            "discussion_hook",
            "idea_summary",
            "modern_adaptation",
            "persona_core",
            "philosopher_bio",
            "philosopher_bot",
            "philosopher_summary",
            "philosophers",
            "philosophy_schools",
            "philosophy_themes",
            "top_10_ideas"
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
        philosophers = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and ensure proper field mapping
        for philosopher in philosophers:
            if "_id" in philosopher:
                philosopher["_id"] = str(philosopher["_id"])
            # Ensure we have the required fields
            if "author" not in philosopher and "philosopher" in philosopher:
                philosopher["author"] = philosopher["philosopher"]
        
        return philosophers
    
    async def get_philosopher_by_id(self, philosopher_id: str) -> Optional[Dict[str, Any]]:
        """Get philosopher by author name (philosopher_id parameter now accepts author name)"""
        collection = self.get_collection("philosophers")
        
        # Search using both author and philosopher fields with case-insensitive regex
        query = {
            "$or": [
                {"author": {"$regex": philosopher_id, "$options": "i"}},
                {"philosopher": {"$regex": philosopher_id, "$options": "i"}}
            ]
        }
        
        philosopher = await collection.find_one(query)
        
        if philosopher:
            # Convert ObjectId to string
            philosopher["_id"] = str(philosopher["_id"])
            # Ensure we have the required fields
            if "author" not in philosopher and "philosopher" in philosopher:
                philosopher["author"] = philosopher["philosopher"]
        
        return philosopher
    
    # Philosophy Schools methods
    async def get_philosophy_schools(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get philosophy schools with pagination"""
        collection = self.get_collection("philosophy_schools")
        cursor = collection.find({}).skip(skip).limit(limit)
        schools = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and ensure proper field mapping
        for school in schools:
            if "_id" in school:
                school["_id"] = str(school["_id"])
            # Map schoolID to school_id if needed
            if "schoolID" in school and "school_id" not in school:
                school["school_id"] = school["schoolID"]
        
        return schools
    
    async def get_philosophy_school_by_id(self, school_id: str) -> Optional[Dict[str, Any]]:
        """Get philosophy school by ID"""
        from bson import ObjectId
        collection = self.get_collection("philosophy_schools")
        
        # Try multiple ways to find the school
        school = None
        
        # Try by ObjectId first
        try:
            school = await collection.find_one({"_id": ObjectId(school_id)})
        except:
            pass
            
        # Try by string _id
        if not school:
            school = await collection.find_one({"_id": school_id})
            
        # Try by school_id field
        if not school:
            try:
                school_id_int = int(school_id)
                school = await collection.find_one({"school_id": school_id_int})
            except ValueError:
                school = await collection.find_one({"school_id": school_id})
                
        # Try by schoolID field (from JSON)
        if not school:
            try:
                school_id_int = int(school_id)
                school = await collection.find_one({"schoolID": school_id_int})
            except ValueError:
                school = await collection.find_one({"schoolID": school_id})
        
        if school:
            # Convert ObjectId to string
            school["_id"] = str(school["_id"])
            # Map schoolID to school_id if needed
            if "schoolID" in school and "school_id" not in school:
                school["school_id"] = school["schoolID"]
        
        return school
    
    async def search_philosophy_schools(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search philosophy schools by name, category, or content"""
        collection = self.get_collection("philosophy_schools")
        
        # Create a text search filter - search both original and normalized fields
        search_filter = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"school": {"$regex": query, "$options": "i"}},  # From JSON structure
                {"category": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}},
                {"core_principles": {"$regex": query, "$options": "i"}},
                {"corePrinciples": {"$regex": query, "$options": "i"}}  # From JSON structure
            ]
        }
        
        cursor = collection.find(search_filter).limit(limit)
        schools = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and ensure proper field mapping
        for school in schools:
            if "_id" in school:
                school["_id"] = str(school["_id"])
            # Map schoolID to school_id if needed
            if "schoolID" in school and "school_id" not in school:
                school["school_id"] = school["schoolID"]
        
        return schools
    
    async def get_philosophers_by_school(self, school_id: str, skip: int = 0, limit: int = 100, is_active_chat: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get philosophers belonging to a specific school with optional active chat filter"""
        collection = self.get_collection("philosophers")
        
        # Handle both string and integer school_id
        try:
            school_id_int = int(school_id)
            filter_query = {"school_id": school_id_int}
        except ValueError:
            filter_query = {"school_id": school_id}
            
        if is_active_chat is not None:
            filter_query["is_active_chat"] = is_active_chat
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        philosophers = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and ensure proper field mapping
        for philosopher in philosophers:
            if "_id" in philosopher:
                philosopher["_id"] = str(philosopher["_id"])
            # Ensure we have the required fields
            if "author" not in philosopher and "philosopher" in philosopher:
                philosopher["author"] = philosopher["philosopher"]
        
        return philosophers
    
    async def get_philosopher_with_school(self, philosopher_id: str) -> Optional[Dict[str, Any]]:
        """Get philosopher with their associated school information"""
        philosopher = await self.get_philosopher_by_id(philosopher_id)
        if not philosopher:
            return None
        
        result = {"philosopher": philosopher, "school": None}
        
        # Get school information if school_id exists
        if philosopher.get("school_id"):
            school = await self.get_philosophy_school_by_id(str(philosopher['school_id']))
            if school:
                school["_id"] = str(school["_id"]) if "_id" in school else None
            result["school"] = school
        
        return result
    
    async def get_philosopher_with_school_by_name(self, philosopher_name: str) -> Optional[Dict[str, Any]]:
        """Get philosopher with their associated school information by name"""
        # Search for philosopher by name (author or philosopher field)
        collection = self.get_collection("philosophers")
        philosopher = await collection.find_one({
            "$or": [
                {"author": {"$regex": philosopher_name, "$options": "i"}},
                {"philosopher": {"$regex": philosopher_name, "$options": "i"}}
            ]
        })
        
        if not philosopher:
            return None
        
        # Convert ObjectId to string and ensure proper field mapping
        if "_id" in philosopher:
            philosopher["_id"] = str(philosopher["_id"])
        if "author" not in philosopher and "philosopher" in philosopher:
            philosopher["author"] = philosopher["philosopher"]
        
        result = {"philosopher": philosopher, "school": None}
        
        # Get school information if school_id exists
        if philosopher.get("school_id"):
            school = await self.get_philosophy_school_by_id(str(philosopher['school_id']))
            if school:
                school["_id"] = str(school["_id"]) if "_id" in school else None
            result["school"] = school
        
        return result
    
    async def search_philosophers(self, query: str, limit: int = 10, is_active_chat: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search philosophers by author name or content with optional active chat filter"""
        collection = self.get_collection("philosophers")
        
        # Create a text search filter - search both author and philosopher fields
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
        philosophers = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and ensure proper field mapping
        for philosopher in philosophers:
            if "_id" in philosopher:
                philosopher["_id"] = str(philosopher["_id"])
            # Ensure we have the required fields
            if "author" not in philosopher and "philosopher" in philosopher:
                philosopher["author"] = philosopher["philosopher"]
        
        return philosophers
    
    # Methods to get data by author across collections
    async def get_aphorisms_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get aphorisms by author"""
        collection = self.get_collection("aphorisms")
        cursor = collection.find({"author": author}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_book_summaries_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get book summaries by author"""
        collection = self.get_collection("book_summary")
        cursor = collection.find({"author": author}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_top_ideas_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get top ten ideas by author"""
        collection = self.get_collection("top_10_ideas")
        cursor = collection.find({"author": author}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_idea_summaries_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get idea summaries by author"""
        collection = self.get_collection("idea_summary")
        cursor = collection.find({"author": author}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_philosophy_themes_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get philosophy themes by author"""
        collection = self.get_collection("philosophy_themes")
        cursor = collection.find({"author": {"$regex": author, "$options": "i"}}).skip(skip).limit(limit)
        themes = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and ensure proper field mapping
        for theme in themes:
            if "_id" in theme:
                theme["_id"] = str(theme["_id"])
            # Ensure we have the required fields
            if "author" not in theme and "philosopher" in theme:
                theme["author"] = theme["philosopher"]
        
        return themes
    
    async def get_philosophy_themes(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get philosophy themes with pagination"""
        collection = self.get_collection("philosophy_themes")
        cursor = collection.find({}).skip(skip).limit(limit)
        themes = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and ensure proper field mapping
        for theme in themes:
            if "_id" in theme:
                theme["_id"] = str(theme["_id"])
            # Ensure we have the required fields
            if "author" not in theme and "philosopher" in theme:
                theme["author"] = theme["philosopher"]
        
        return themes
    
    async def get_philosopher_summaries_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get philosopher summaries by author"""
        collection = self.get_collection("philosopher_summary")
        cursor = collection.find({"author": {"$regex": author, "$options": "i"}}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_modern_adaptations_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get modern adaptations by author"""
        collection = self.get_collection("modern_adaptation")
        cursor = collection.find({"author": {"$regex": author, "$options": "i"}}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_persona_cores_by_author(self, author: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get persona cores by author"""
        collection = self.get_collection("persona_core")
        cursor = collection.find({"persona.author": {"$regex": author, "$options": "i"}}).skip(skip).limit(limit)
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
        collection = self.get_collection("book_summary")
        cursor = collection.find({}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    # Bibliography-related methods
    async def get_bibliographies(self, skip: int = 0, limit: int = 100, author: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get bibliographies with pagination and optional author filter"""
        collection = self.get_collection("bibliography")
        
        filter_query = {}
        if author:
            filter_query["author"] = {"$regex": author, "$options": "i"}
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        bibliographies = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for bibliography in bibliographies:
            if "_id" in bibliography:
                bibliography["_id"] = str(bibliography["_id"])
        
        return bibliographies
    
    async def get_bibliography_by_id(self, bibliography_id: str) -> Optional[Dict[str, Any]]:
        """Get bibliography by ID"""
        collection = self.get_collection("bibliography")
        bibliography = await collection.find_one({"_id": bibliography_id})
        
        if bibliography and "_id" in bibliography:
            bibliography["_id"] = str(bibliography["_id"])
        
        return bibliography
    
    async def get_bibliography_by_author(self, author: str) -> Optional[Dict[str, Any]]:
        """Get bibliography by author name"""
        collection = self.get_collection("bibliography")
        bibliography = await collection.find_one({"author": {"$regex": author, "$options": "i"}})
        
        if bibliography and "_id" in bibliography:
            bibliography["_id"] = str(bibliography["_id"])
        
        return bibliography
    
    async def search_bibliographies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search bibliographies by author, description, or content"""
        collection = self.get_collection("bibliography")
        
        search_filter = {
            "$or": [
                {"author": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"background": {"$regex": query, "$options": "i"}},
                {"works": {"$regex": query, "$options": "i"}},
                {"major_themes": {"$regex": query, "$options": "i"}},
                {"influence": {"$regex": query, "$options": "i"}},
                {"note": {"$regex": query, "$options": "i"}}
            ]
        }
        
        cursor = collection.find(search_filter).limit(limit)
        bibliographies = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for bibliography in bibliographies:
            if "_id" in bibliography:
                bibliography["_id"] = str(bibliography["_id"])
        
        return bibliographies
    
    # Aphorism-related methods
    async def get_aphorisms(self, skip: int = 0, limit: int = 100, philosopher: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get aphorisms with pagination and optional philosopher filter"""
        collection = self.get_collection("aphorisms")
        
        filter_query = {}
        if philosopher:
            # Match either author or philosopher field for backward compatibility
            filter_query["$or"] = [
                {"author": {"$regex": philosopher, "$options": "i"}},
                {"philosopher": {"$regex": philosopher, "$options": "i"}}
            ]
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        aphorisms = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and ensure proper field mapping
        for aphorism in aphorisms:
            if "_id" in aphorism:
                aphorism["_id"] = str(aphorism["_id"])
            # Ensure we have the required fields
            if "author" not in aphorism and "philosopher" in aphorism:
                aphorism["author"] = aphorism["philosopher"]
        
        return aphorisms
    
    async def get_random_aphorisms(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get random aphorisms"""
        collection = self.get_collection("aphorisms")
        cursor = collection.aggregate([{"$sample": {"size": count}}])
        aphorisms = await cursor.to_list(length=count)
        
        # Convert ObjectId to string and ensure proper field mapping
        for aphorism in aphorisms:
            if "_id" in aphorism:
                aphorism["_id"] = str(aphorism["_id"])
            # Ensure we have the required fields
            if "author" not in aphorism and "philosopher" in aphorism:
                aphorism["author"] = aphorism["philosopher"]
        
        return aphorisms
    
    # Ideas-related methods
    async def get_top_ideas(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get top ten ideas with pagination"""
        collection = self.get_collection("top_10_ideas")
        cursor = collection.find({}).skip(skip).limit(limit)
        ideas = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and ensure proper field mapping
        for idea in ideas:
            if "_id" in idea:
                idea["_id"] = str(idea["_id"])
            # Ensure we have the required fields
            if "author" not in idea and "philosopher" in idea:
                idea["author"] = idea["philosopher"]
        
        return ideas
    
    async def get_idea_summaries(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get idea summaries with pagination"""
        collection = self.get_collection("idea_summary")
        cursor = collection.find({}).skip(skip).limit(limit)
        ideas = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and ensure proper field mapping
        for idea in ideas:
            if "_id" in idea:
                idea["_id"] = str(idea["_id"])
            # Ensure we have the required fields
            if "author" not in idea and "philosopher" in idea:
                idea["author"] = idea["philosopher"]
        
        return ideas
    
    # Chat-related methods
    async def get_chat_blueprints(self, author: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get chat blueprints from the database"""
        collection = self.get_collection("chat_blueprint")
        query = {}
        if author:
            # Search in nested structure and flat structure
            query = {
                "$or": [
                    {"prompt_blueprint.author": {"$regex": author, "$options": "i"}},
                    {"author": {"$regex": author, "$options": "i"}}
                ]
            }
        cursor = collection.find(query)
        blueprints = await cursor.to_list(length=100)
        
        # Convert ObjectId to string and handle nested structure
        for blueprint in blueprints:
            if "_id" in blueprint:
                blueprint["_id"] = str(blueprint["_id"])
            
            # Handle nested structure - extract data from prompt_blueprint if it exists
            if "prompt_blueprint" in blueprint:
                nested_data = blueprint["prompt_blueprint"]
                # Copy nested fields to top level for model compatibility
                if "author" in nested_data:
                    blueprint["author"] = nested_data["author"]
                # Extract other relevant fields if they exist
                for field in ["personality_traits", "speaking_style", "core_beliefs", "typical_responses", "conversation_starters"]:
                    if field in nested_data:
                        blueprint[field] = nested_data[field]
            
            # Ensure we have the required fields
            if "author" not in blueprint and "philosopher" in blueprint:
                blueprint["author"] = blueprint["philosopher"]
        
        return blueprints
    
    async def get_philosopher_bots(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get philosopher bot configurations"""
        collection = self.get_collection("philosopher_bot")
        cursor = collection.find({}).skip(skip).limit(limit)
        bots = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and handle nested structure
        for bot in bots:
            if "_id" in bot:
                bot["_id"] = str(bot["_id"])
            
            # Handle nested structure - extract data from persona if it exists
            if "persona" in bot:
                persona_data = bot["persona"]
                # Copy nested fields to top level for model compatibility
                if "author" in persona_data:
                    bot["author"] = persona_data["author"]
                # Extract other relevant fields if they exist
                for field in ["category", "language", "style", "philosophical_themes"]:
                    if field in persona_data:
                        bot[field] = persona_data[field]
            
            # Ensure we have the required fields
            if "author" not in bot and "philosopher" in bot:
                bot["author"] = bot["philosopher"]
            elif "author" not in bot and "name" in bot:
                bot["author"] = bot["name"]
        
        return bots
    
    async def get_conversation_logic(self, author: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get conversation logic from the database"""
        collection = self.get_collection("conversation_logic")
        query = {}
        if author:
            # Search both author and philosopher fields
            query = {
                "$or": [
                    {"author": {"$regex": author, "$options": "i"}},
                    {"philosopher": {"$regex": author, "$options": "i"}}
                ]
            }
        cursor = collection.find(query)
        logic_items = await cursor.to_list(length=100)
        
        # Convert ObjectId to string and ensure proper field mapping
        for item in logic_items:
            if "_id" in item:
                item["_id"] = str(item["_id"])
            # Ensure we have the required fields
            if "author" not in item and "philosopher" in item:
                item["author"] = item["philosopher"]
        
        return logic_items
    
    # Search methods
    async def global_search(self, query: str, limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """Search across multiple collections"""
        results = {}
        
        # Search in key collections
        search_collections = [
            "philosophers",
            "philosopher_summary",
            "books", 
            "book_summary",
            "aphorisms",
            "top_10_ideas",
            "idea_summary",
            "philosophy_themes",
            "persona_core"
        ]
        
        for collection_name in search_collections:
            try:
                collection = self.get_collection(collection_name)
                
                # Create text search filter based on collection structure
                if collection_name == "philosophers":
                    search_filter = {
                        "$or": [
                            {"author": {"$regex": query, "$options": "i"}},
                            {"philosopher": {"$regex": query, "$options": "i"}},
                            {"summary": {"$regex": query, "$options": "i"}},
                            {"content": {"$regex": query, "$options": "i"}}
                        ]
                    }
                elif collection_name == "philosopher_summary":
                    search_filter = {
                        "$or": [
                            {"author": {"$regex": query, "$options": "i"}},
                            {"title": {"$regex": query, "$options": "i"}},
                            {"description": {"$regex": query, "$options": "i"}},
                            {"sections": {"$regex": query, "$options": "i"}}
                        ]
                    }
                elif collection_name in ["books", "book_summary"]:
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
                elif collection_name == "idea_summary":
                    search_filter = {
                        "$or": [
                            {"author": {"$regex": query, "$options": "i"}},
                            {"category": {"$regex": query, "$options": "i"}},
                            {"title": {"$regex": query, "$options": "i"}},
                            {"quote": {"$regex": query, "$options": "i"}},
                            {"summary.section": {"$regex": query, "$options": "i"}},
                            {"summary.content": {"$regex": query, "$options": "i"}},
                            {"key_books": {"$regex": query, "$options": "i"}}
                        ]
                    }
                elif collection_name == "top_10_ideas":
                    search_filter = {
                        "$or": [
                            {"author": {"$regex": query, "$options": "i"}},
                            {"category": {"$regex": query, "$options": "i"}},
                            {"top_ideas.idea": {"$regex": query, "$options": "i"}},
                            {"top_ideas.description": {"$regex": query, "$options": "i"}},
                            {"top_ideas.key_books": {"$regex": query, "$options": "i"}}
                        ]
                    }
                elif collection_name == "modern_adaptation":
                    search_filter = {
                        "$or": [
                            {"author": {"$regex": query, "$options": "i"}},
                            {"category": {"$regex": query, "$options": "i"}},
                            {"modern_adaptation.purpose": {"$regex": query, "$options": "i"}},
                            {"modern_adaptation.context_awareness.historical_self_reference": {"$regex": query, "$options": "i"}},
                            {"modern_adaptation.context_awareness.era_contrast_rules": {"$regex": query, "$options": "i"}},
                            {"modern_adaptation.modern_topics.name": {"$regex": query, "$options": "i"}},
                            {"modern_adaptation.modern_topics.analysis": {"$regex": query, "$options": "i"}},
                            {"modern_adaptation.adaptive_templates.pattern": {"$regex": query, "$options": "i"}},
                            {"modern_adaptation.tone_instructions": {"$regex": query, "$options": "i"}}
                        ]
                    }
                elif collection_name == "philosophy_themes":
                    search_filter = {
                        "$or": [
                            {"author": {"$regex": query, "$options": "i"}},
                            {"category": {"$regex": query, "$options": "i"}},
                            {"philosophy_and_themes.core_ideas.name": {"$regex": query, "$options": "i"}},
                            {"philosophy_and_themes.core_ideas.summary": {"$regex": query, "$options": "i"}},
                            {"philosophy_and_themes.core_ideas.discussion_hooks": {"$regex": query, "$options": "i"}},
                            {"philosophy_and_themes.perspectivism_framework.principle": {"$regex": query, "$options": "i"}},
                            {"philosophy_and_themes.perspectivism_framework.implications": {"$regex": query, "$options": "i"}},
                            {"philosophy_and_themes.perspectivism_framework.example_prompts": {"$regex": query, "$options": "i"}},
                            {"philosophy_and_themes.aphorisms": {"$regex": query, "$options": "i"}},
                            {"philosophy_and_themes.discussion_templates.type": {"$regex": query, "$options": "i"}},
                            {"philosophy_and_themes.discussion_templates.pattern": {"$regex": query, "$options": "i"}}
                        ]
                    }
                elif collection_name == "persona_core":
                    search_filter = {
                        "$or": [
                            {"persona.author": {"$regex": query, "$options": "i"}},
                            {"persona.identity.full_name": {"$regex": query, "$options": "i"}},
                            {"persona.biography.overview": {"$regex": query, "$options": "i"}},
                            {"persona.biography.historical_context": {"$regex": query, "$options": "i"}},
                            {"persona.core_principles": {"$regex": query, "$options": "i"}},
                            {"persona.style.tone": {"$regex": query, "$options": "i"}},
                            {"persona.style.speaking_style": {"$regex": query, "$options": "i"}},
                            {"persona.interaction_rules.primary_goal": {"$regex": query, "$options": "i"}},
                            {"persona.modes_of_response.name": {"$regex": query, "$options": "i"}},
                            {"persona.modes_of_response.description": {"$regex": query, "$options": "i"}}
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
