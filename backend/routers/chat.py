"""
Chat API router - for chatbot functionality
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
import logging
import random

from ..database import DatabaseManager
from ..models import ChatBlueprintResponse, ChatBlueprint, ConversationLogic, PhilosopherBot, ChatMessage, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_db_manager():
    """Dependency to get database manager"""
    from ..main import app
    return app.state.db_manager

@router.get("/blueprints", response_model=ChatBlueprintResponse)
async def get_chat_blueprints(
    author: Optional[str] = Query(None, description="Filter by author"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get chat blueprints for philosopher personalities"""
    try:
        blueprints = await db_manager.get_chat_blueprints(author=author)
        
        # Convert to Pydantic models
        blueprint_models = []
        for blueprint in blueprints:
            try:
                blueprint_models.append(ChatBlueprint(**blueprint))
            except Exception as e:
                logger.warning(f"Failed to parse chat blueprint {blueprint.get('_id', 'unknown')}: {e}")
                continue
        
        filter_msg = f" for author '{author}'" if author else ""
        return ChatBlueprintResponse(
            data=blueprint_models,
            total_count=len(blueprint_models),
            message=f"Retrieved {len(blueprint_models)} chat blueprints{filter_msg}"
        )
    
    except Exception as e:
        logger.error(f"Failed to get chat blueprints: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat blueprints")

@router.get("/conversation-logic", response_model=ChatBlueprintResponse)
async def get_conversation_logic(
    author: Optional[str] = Query(None, description="Filter by author"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get conversation logic for philosophers"""
    try:
        logic = await db_manager.get_conversation_logic(author=author)
        
        # Convert to Pydantic models
        logic_models = []
        for item in logic:
            try:
                logic_models.append(ConversationLogic(**item))
            except Exception as e:
                logger.warning(f"Failed to parse conversation logic {item.get('_id', 'unknown')}: {e}")
                continue
        
        filter_msg = f" for author '{author}'" if author else ""
        return ChatBlueprintResponse(
            data=logic_models,
            total_count=len(logic_models),
            message=f"Retrieved {len(logic_models)} conversation logic items{filter_msg}"
        )
    
    except Exception as e:
        logger.error(f"Failed to get conversation logic: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation logic")

@router.get("/philosopher-bots", response_model=ChatBlueprintResponse)
async def get_philosopher_bots(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get philosopher bot configurations"""
    try:
        bots = await db_manager.get_philosopher_bots(skip=skip, limit=limit)
        
        # Convert to Pydantic models
        bot_models = []
        for bot in bots:
            try:
                bot_models.append(PhilosopherBot(**bot))
            except Exception as e:
                logger.warning(f"Failed to parse philosopher bot {bot.get('_id', 'unknown')}: {e}")
                continue
        
        return ChatBlueprintResponse(
            data=bot_models,
            total_count=len(bot_models),
            message=f"Retrieved {len(bot_models)} philosopher bot configurations"
        )
    
    except Exception as e:
        logger.error(f"Failed to get philosopher bots: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosopher bots")

@router.get("/available-philosophers", response_model=dict)
async def get_available_philosophers(
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get list of available philosophers for chat"""
    try:
        # Get unique philosophers from chat blueprints
        blueprints_collection = db_manager.get_collection("chat_blueprints")
        blueprint_philosophers = await blueprints_collection.distinct("author")
        
        # Get unique philosophers from conversation logic
        logic_collection = db_manager.get_collection("conversation_logic")
        logic_philosophers = await logic_collection.distinct("author")
        
        # Get unique philosophers from philosopher bots
        bots_collection = db_manager.get_collection("philosopher_bots")
        bot_philosophers = await bots_collection.distinct("author")
        
        # Combine and deduplicate
        all_philosophers = set(blueprint_philosophers + logic_philosophers + bot_philosophers)
        available_philosophers = sorted(list(all_philosophers))
        
        return {
            "success": True,
            "philosophers": available_philosophers,
            "total_count": len(available_philosophers),
            "message": f"Found {len(available_philosophers)} available philosophers for chat"
        }
    
    except Exception as e:
        logger.error(f"Failed to get available philosophers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve available philosophers")

@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    message: ChatMessage,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Send a message to a philosopher chatbot (mock implementation)"""
    try:
        # This is a mock implementation - in production you'd integrate with your LLM
        author = message.author or "Nietzsche"  # Default to Nietzsche
        
        # Get author's chat blueprint for personality
        blueprint = None
        blueprints = await db_manager.get_chat_blueprints(author=author)
        if blueprints:
            blueprint = blueprints[0]
        
        # Get conversation logic
        logic = None
        conversation_logic = await db_manager.get_conversation_logic(author=author)
        if conversation_logic:
            logic = conversation_logic[0]
        
        # Mock response generation (replace with actual LLM integration)
        mock_responses = [
            f"As {author}, I find your question intriguing. Let me share my perspective...",
            f"From my philosophical standpoint, {message.message.lower()} touches upon fundamental questions of existence.",
            f"In my view, this relates to the deeper nature of human experience and consciousness.",
            f"Your inquiry reminds me of my thoughts on the human condition and our search for meaning."
        ]
        
        # Add author-specific responses if blueprint available
        if blueprint and blueprint.get('typical_responses'):
            mock_responses.extend(list(blueprint['typical_responses'].values()))
        
        response_text = random.choice(mock_responses)
        
        # Add context if provided
        if message.context:
            response_text += f" Given the context you've provided about {message.context}, I would add..."
        
        return ChatResponse(
            response=response_text,
            author=author,
            confidence=0.85,
            sources=[f"{author} philosophical writings", "Chat blueprint", "Conversation logic"],
            message=f"Response generated for {author}"
        )
    
    except Exception as e:
        logger.error(f"Failed to process chat message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")

@router.get("/conversation-starters/{philosopher}", response_model=dict)
async def get_conversation_starters(
    philosopher: str,
    count: int = Query(5, ge=1, le=20, description="Number of conversation starters to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get conversation starters for a specific philosopher"""
    try:
        # Get chat blueprint for the philosopher
        blueprints = await db_manager.get_chat_blueprints(philosopher=philosopher)
        
        if not blueprints:
            raise HTTPException(status_code=404, detail=f"No chat configuration found for philosopher '{philosopher}'")
        
        blueprint = blueprints[0]
        conversation_starters = blueprint.get('conversation_starters', [])
        
        # If not enough starters in blueprint, add generic ones
        if len(conversation_starters) < count:
            generic_starters = [
                f"What is your view on the meaning of life, {philosopher}?",
                f"How do you approach the question of morality, {philosopher}?",
                f"What role does suffering play in human existence, {philosopher}?",
                f"How should we understand the nature of truth, {philosopher}?",
                f"What is your perspective on human freedom and choice, {philosopher}?"
            ]
            conversation_starters.extend(generic_starters)
        
        # Return requested number of starters
        selected_starters = conversation_starters[:count]
        
        return {
            "success": True,
            "philosopher": philosopher,
            "conversation_starters": selected_starters,
            "total_count": len(selected_starters),
            "message": f"Retrieved {len(selected_starters)} conversation starters for {philosopher}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation starters for {philosopher}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation starters")

@router.get("/personality/{philosopher}", response_model=dict)
async def get_philosopher_personality(
    philosopher: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get personality profile for a philosopher"""
    try:
        # Get chat blueprint
        blueprints = await db_manager.get_chat_blueprints(philosopher=philosopher)
        blueprint = blueprints[0] if blueprints else {}
        
        # Get conversation logic
        logic_items = await db_manager.get_conversation_logic(philosopher=philosopher)
        logic = logic_items[0] if logic_items else {}
        
        # Get persona core
        persona_collection = db_manager.get_collection("persona_cores")
        persona = await persona_collection.find_one({"philosopher": {"$regex": philosopher, "$options": "i"}})
        
        if not blueprint and not logic and not persona:
            raise HTTPException(status_code=404, detail=f"No personality data found for philosopher '{philosopher}'")
        
        personality_profile = {
            "author": philosopher,
            "personality_traits": blueprint.get('personality_traits', []),
            "speaking_style": blueprint.get('speaking_style', ''),
            "core_beliefs": blueprint.get('core_beliefs', []),
            "argumentation_style": logic.get('argumentation_style', ''),
            "topic_preferences": logic.get('topic_preferences', []),
            "persona_core": persona.get('core_attributes', {}) if persona else {}
        }
        
        return {
            "success": True,
            "data": personality_profile,
            "message": f"Retrieved personality profile for {philosopher}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get personality for {philosopher}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosopher personality")
