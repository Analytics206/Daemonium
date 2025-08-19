"""
Chat API router - for chatbot functionality
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from typing import List, Optional, Dict, Any
import logging
import random
import json
from datetime import datetime, timezone
import asyncio

try:
    # Prefer async Redis client from redis-py 4/5
    from redis.asyncio import Redis  # type: ignore
except Exception as _:
    Redis = None  # Will raise at runtime if endpoints are used without dependency

from ..database import DatabaseManager
from ..models import PersonaCoreResponse
from ..models import ChatBlueprintResponse, ChatBlueprint, ConversationLogic, PhilosopherBot, ChatMessage, ChatResponse, ModernAdaptationResponse
from ..config import get_settings
from ..auth import verify_firebase_id_token

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_db_manager():
    """Dependency to get database manager"""
    from ..main import app
    return app.state.db_manager


# ------------------------------
# Redis helpers (scoped to router)
# ------------------------------
def _chat_messages_key(user_id: str, chat_id: str) -> str:
    """Build Redis key for chat message list."""
    return f"chat:{user_id}:{chat_id}:messages"

async def _with_redis(func):
    """Utility to create a short-lived Redis client, run func(redis), and close it.
    Keeps changes minimal and avoids modifying app lifespan.
    """
    settings = get_settings()
    if Redis is None:
        raise HTTPException(status_code=500, detail="Redis client not available. Install 'redis' package.")
    client = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        db=settings.redis_db,
        decode_responses=True,
    )
    try:
        return await func(client)
    finally:
        try:
            await client.close()
        except Exception:
            pass

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
        all_philosophers = set()
        
        # Get philosophers from chat blueprints (nested structure)
        try:
            blueprints = await db_manager.get_chat_blueprints()
            for blueprint in blueprints:
                if "author" in blueprint and blueprint["author"]:
                    all_philosophers.add(blueprint["author"])
        except Exception as e:
            logger.warning(f"Failed to get chat blueprint philosophers: {e}")
        
        # Get philosophers from conversation logic
        try:
            logic_items = await db_manager.get_conversation_logic()
            for item in logic_items:
                if "author" in item and item["author"]:
                    all_philosophers.add(item["author"])
        except Exception as e:
            logger.warning(f"Failed to get conversation logic philosophers: {e}")
        
        # Get philosophers from philosopher bots (nested structure)
        try:
            bots = await db_manager.get_philosopher_bots()
            for bot in bots:
                if "author" in bot and bot["author"]:
                    all_philosophers.add(bot["author"])
        except Exception as e:
            logger.warning(f"Failed to get philosopher bot philosophers: {e}")
        
        # Also get from main philosophers collection for active chat philosophers
        try:
            active_philosophers = await db_manager.get_philosophers(is_active_chat=1)
            for philosopher in active_philosophers:
                if "author" in philosopher and philosopher["author"]:
                    all_philosophers.add(philosopher["author"])
        except Exception as e:
            logger.warning(f"Failed to get active chat philosophers: {e}")
        
        # Convert to sorted list
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
        # Get chat blueprint for the philosopher (use author parameter)
        blueprints = await db_manager.get_chat_blueprints(author=philosopher)
        
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
        # Get chat blueprint (use author parameter)
        blueprints = await db_manager.get_chat_blueprints(author=philosopher)
        blueprint = blueprints[0] if blueprints else {}
        
        # Get conversation logic (use author parameter)
        logic_items = await db_manager.get_conversation_logic(author=philosopher)
        logic = logic_items[0] if logic_items else {}
        
        # Get persona core (search by author field in nested persona structure)
        persona_collection = db_manager.get_collection("persona_core")
        persona = await persona_collection.find_one({
            "$or": [
                {"persona.author": {"$regex": philosopher, "$options": "i"}},
                {"persona.identity.full_name": {"$regex": philosopher, "$options": "i"}}
            ]
        })
        
        # Convert ObjectId to string if persona exists
        if persona and "_id" in persona:
            persona["_id"] = str(persona["_id"])
        
        if not blueprint and not logic and not persona:
            raise HTTPException(status_code=404, detail=f"No personality data found for philosopher '{philosopher}'")
        
        # Extract data from actual JSON structure
        prompt_blueprint = blueprint.get('prompt_blueprint', {})
        conversation_logic_data = logic.get('conversation_logic', {})
        persona_data = persona.get('persona', {}) if persona else {}
        
        personality_profile = {
            "author": philosopher,
            "full_name": persona_data.get('identity', {}).get('full_name', philosopher),
            "birth_date": persona_data.get('identity', {}).get('birth_date', ''),
            "death_date": persona_data.get('identity', {}).get('death_date', ''),
            "nationality": persona_data.get('identity', {}).get('nationality', ''),
            "roles": persona_data.get('identity', {}).get('roles', []),
            "personality_traits": persona_data.get('biography', {}).get('personality_traits', []),
            "speaking_style": persona_data.get('style', {}).get('speaking_style', ''),
            "tone": persona_data.get('style', {}).get('tone', ''),
            "thought_process": persona_data.get('style', {}).get('thought_process', ''),
            "style_devices": persona_data.get('style', {}).get('devices', []),
            "prohibited_patterns": persona_data.get('style', {}).get('prohibited', []),
            "core_principles": persona_data.get('core_principles', []),
            "modes_of_response": persona_data.get('modes_of_response', []),
            "interaction_primary_goal": persona_data.get('interaction_rules', {}).get('primary_goal', ''),
            "interaction_behavior": persona_data.get('interaction_rules', {}).get('behavior', []),
            "conversation_goal": conversation_logic_data.get('primary_goal', ''),
            "response_principles": conversation_logic_data.get('response_strategy', {}).get('core_principles', []),
            "tone_modes": conversation_logic_data.get('tone_selection', {}).get('modes', []),
            "provocation_techniques": conversation_logic_data.get('provocation_methods', {}).get('techniques', []),
            "chat_blueprint_purpose": prompt_blueprint.get('purpose', ''),
            "resources_used": prompt_blueprint.get('meta', {}).get('resources_used', []),
            "response_pipeline": prompt_blueprint.get('response_pipeline', [])
        }
        
        return {
            "success": True,
            "data": personality_profile,
            "message": f"Retrieved comprehensive personality profile for {philosopher}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get personality for {philosopher}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosopher personality")

@router.get("/persona-cores", response_model=PersonaCoreResponse)
async def get_persona_cores(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    philosopher: Optional[str] = Query(None, description="Filter by philosopher"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get persona cores for philosopher chatbots"""
    try:
        collection = db_manager.get_collection("persona_core")
        
        filter_query = {}
        if philosopher:
            # Search in nested persona structure by author field
            filter_query["persona.author"] = {"$regex": philosopher, "$options": "i"}
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        cores = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for each document
        for core in cores:
            if "_id" in core:
                core["_id"] = str(core["_id"])
        
        filter_msg = f" for philosopher '{philosopher}'" if philosopher else ""
        return PersonaCoreResponse(
            data=cores,
            total_count=len(cores),
            message=f"Retrieved {len(cores)} persona core{filter_msg}"
        )
    
    except Exception as e:
        logger.error(f"Failed to get persona core: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve persona core")

@router.get("/modern-adaptations", response_model=ModernAdaptationResponse)
async def get_modern_adaptations(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    philosopher: Optional[str] = Query(None, description="Filter by philosopher"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get modern adaptations of philosophical ideas for chatbot functionality"""
    try:
        collection = db_manager.get_collection("modern_adaptation")
        
        filter_query = {}
        if philosopher:
            filter_query["author"] = {"$regex": philosopher, "$options": "i"}
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        adaptations = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for API response
        for adaptation in adaptations:
            if "_id" in adaptation:
                adaptation["_id"] = str(adaptation["_id"])
        
        filter_msg = f" by philosopher '{philosopher}'" if philosopher else ""
        return ModernAdaptationResponse(
            success=True,
            data=adaptations,
            total_count=len(adaptations),
            message=f"Retrieved {len(adaptations)} modern adaptation{filter_msg}"
        )
    
    except Exception as e:
        logger.error(f"Failed to get modern adaptations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve modern adaptations")


# ==============================
# Redis chat message endpoints
# ==============================
@router.post("/redis/{user_id}/{chat_id}", response_model=dict)
async def push_chat_message_to_redis(
    user_id: str,
    chat_id: str,
    input: Optional[str] = Query(
        None,
        description="User chat input to store (prefer JSON body for large payloads); kept for backward compatibility",
    ),
    ttl_seconds: int = Query(0, ge=0, description="Optional TTL (seconds) for the chat list; 0 means no TTL"),
    request: Request = None,
    background_tasks: BackgroundTasks = None,
    auth_info: Dict[str, Any] = Depends(verify_firebase_id_token),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """Push a chat input into Redis under a list keyed by user_id and chat_id.

    - Key: chat:{user_id}:{chat_id}:messages
    - Operation: RPUSH JSON(message)
    - Optional: set/update TTL if ttl_seconds > 0
    """

    async def _do(redis):
        key = _chat_messages_key(user_id, chat_id)
        now = datetime.now(timezone.utc)

        # Resolve input from query or request body for large payload support
        raw_input: Any = input
        if raw_input is None and request is not None:
            try:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    body = await request.json()
                    # Accept raw string, object, or wrapper { "input": ... }
                    if isinstance(body, str):
                        raw_input = body
                    elif isinstance(body, dict) and "input" in body:
                        raw_input = body.get("input")
                    else:
                        raw_input = body
                else:
                    # Fallback: treat raw body as UTF-8 text
                    raw_input = (await request.body()).decode("utf-8")
            except Exception as ex:
                logger.warning(
                    f"Failed to parse request body for Redis push (user={user_id} chat={chat_id}): {ex}"
                )
                raw_input = None

        if raw_input is None:
            raise HTTPException(status_code=400, detail="Missing 'input' payload")

        # Try to parse the incoming payload as JSON; otherwise treat as string
        parsed: Any
        if isinstance(raw_input, (dict, list)):
            parsed = raw_input
        elif isinstance(raw_input, str):
            try:
                parsed = json.loads(raw_input)
            except Exception:
                parsed = raw_input
        else:
            parsed = str(raw_input)

        # Always include user and chat identifiers
        payload_obj: Dict[str, Any] = {
            "user_id": user_id,
            "chat_id": chat_id,
            "timestamp": now.isoformat(),  # e.g., 2025-08-15T21:32:00.000000+00:00
            "date": now.date().isoformat(),  # e.g., 2025-08-15
        }

        # If client sent structured JSON, surface common fields at top-level
        if isinstance(parsed, dict):
            # Preserve known fields if present
            if "type" in parsed:
                payload_obj["type"] = parsed.get("type")
            if "text" in parsed:
                payload_obj["text"] = parsed.get("text")
            if "state" in parsed:
                # Store session state as-is when provided (e.g., session_start/end)
                payload_obj["state"] = parsed.get("state")
            # Keep original for completeness/debugging
            payload_obj["original"] = parsed
        else:
            # Fallback: store the raw message under 'message'
            payload_obj["message"] = str(parsed)

        payload = json.dumps(payload_obj)
        new_len = await redis.rpush(key, payload)
        if ttl_seconds > 0:
            await redis.expire(key, ttl_seconds)

        # Schedule background persistence to MongoDB without blocking response
        async def _insert_to_mongo(document: Dict[str, Any], collection_name: str):
            try:
                collection = db_manager.get_collection(collection_name)
                await collection.insert_one(document)
            except Exception as ex:
                logger.warning(
                    f"Background insert to MongoDB failed into {collection_name} for user={user_id} chat={chat_id}: {ex}"
                )

        # Enrich document with redis key context
        doc_to_insert = {**payload_obj, "redis_key": key}

        # Determine target collection based on message type
        msg_type = payload_obj.get("type", "")
        target_collection = "chat_reponse_history" if msg_type == "assistant_message" else "chat_history"
        try:
            if background_tasks is not None:
                background_tasks.add_task(_insert_to_mongo, doc_to_insert, target_collection)
            else:
                # Fallback scheduling if BackgroundTasks unavailable
                asyncio.create_task(_insert_to_mongo(doc_to_insert, target_collection))
        except Exception as ex:
            logger.warning(
                f"Failed to schedule background MongoDB insert for user={user_id} chat={chat_id}: {ex}"
            )

        return {
            "success": True,
            "key": key,
            "list_length": new_len,
            "data": payload_obj,
            "message": "Chat input stored in Redis",
        }

    try:
        return await _with_redis(_do)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to push chat message to Redis for user={user_id} chat={chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to push chat message to Redis")

@router.get("/redis/{user_id}/summaries", response_model=dict)
async def list_user_chat_summaries(
    user_id: str,
    max_chats: int = Query(100, ge=1, le=1000, description="Maximum number of chat summaries to return"),
    auth_info: Dict[str, Any] = Depends(verify_firebase_id_token),
):
    """List chat summaries for a user by scanning Redis keys.

    - Pattern: chat:{user_id}:*:messages
    - For each chat, find the first user_message to build a 24-char title
    - Returns a list of objects: { chat_id, title, first_user_text, created_at, last_updated, key, count }
    """

    async def _do(redis):
        pattern = f"chat:{user_id}:*:messages"

        # Collect keys via SCAN to avoid blocking
        cursor = 0
        keys: List[str] = []
        try:
            while True:
                cursor, batch = await redis.scan(cursor=cursor, match=pattern, count=1000)
                if batch:
                    keys.extend(batch)
                if cursor == 0:
                    break
        except Exception as ex:
            logger.error(f"Redis SCAN failed for pattern {pattern}: {ex}")
            keys = []

        summaries = []
        for key in keys:
            try:
                parts = key.split(":")
                if len(parts) < 4:
                    continue
                chat_id = parts[2]

                items = await redis.lrange(key, 0, -1)
                first_user_text = None
                created_at = None
                last_updated = None

                if items:
                    # created_at from first item's timestamp when available
                    try:
                        first_obj = json.loads(items[0])
                        created_at = first_obj.get("timestamp")
                    except Exception:
                        created_at = None

                    # last_updated from last item's timestamp when available
                    try:
                        last_obj = json.loads(items[-1])
                        last_updated = last_obj.get("timestamp")
                    except Exception:
                        last_updated = created_at

                    # find first user message in the list
                    for it in items:
                        text_val = None
                        try:
                            obj = json.loads(it)
                            t = obj.get("type", "")
                            if t == "user_message":
                                text_val = obj.get("text") or obj.get("message")
                            elif not t and "message" in obj:
                                text_val = obj.get("message")
                        except Exception:
                            # raw string fallback
                            text_val = it

                        if text_val:
                            first_user_text = str(text_val)
                            break

                if not first_user_text:
                    first_user_text = "(no user input)"

                title = first_user_text[:24]
                summaries.append(
                    {
                        "chat_id": chat_id,
                        "title": title,
                        "first_user_text": first_user_text,
                        "created_at": created_at,
                        "last_updated": last_updated,
                        "key": key,
                        "count": len(items) if items else 0,
                    }
                )
            except Exception as ex:
                logger.warning(f"Failed to build summary for key {key}: {ex}")
                continue

        # sort by last_updated desc when available
        def _to_dt(ts: Optional[str]):
            try:
                if ts:
                    # handle 'Z' suffix if present
                    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                pass
            return datetime.min.replace(tzinfo=timezone.utc)

        summaries.sort(key=lambda s: _to_dt(s.get("last_updated")), reverse=True)
        if len(summaries) > max_chats:
            summaries = summaries[:max_chats]

        return {
            "success": True,
            "user_id": user_id,
            "total_chats": len(summaries),
            "data": summaries,
            "message": f"Found {len(summaries)} chat summaries for user",
        }

    try:
        return await _with_redis(_do)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list chat summaries from Redis for user={user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list chat summaries from Redis")

@router.get("/redis/{user_id}/{chat_id}", response_model=dict)
async def get_chat_messages_from_redis(
    user_id: str,
    chat_id: str,
    start: int = Query(0, description="Start index for LRANGE"),
    stop: int = Query(-1, description="Stop index for LRANGE (-1 for end)"),
    auth_info: Dict[str, Any] = Depends(verify_firebase_id_token),
):
    """Retrieve chat inputs from Redis list for a given user_id and chat_id.

    Returns an array of message objects in insertion order.
    """

    async def _do(redis):
        key = _chat_messages_key(user_id, chat_id)
        items = await redis.lrange(key, start, stop)
        messages: List[Dict[str, Any]] = []
        for it in items:
            try:
                messages.append(json.loads(it))
            except Exception:
                messages.append({"message": it})
        return {
            "success": True,
            "key": key,
            "count": len(messages),
            "data": messages,
            "message": f"Retrieved {len(messages)} messages from Redis",
        }

    try:
        return await _with_redis(_do)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat messages from Redis for user={user_id} chat={chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat messages from Redis")
