# PhilosopherOrchestrator - AI Coding Reference Summary

## What You're Building
A backend system that creates intelligent, contextual prompts for philosophical conversations by orchestrating AI agents, managing philosophical datasets, and maintaining conversation coherence through state-driven dialogue.

## Core Problem Being Solved
- **Context Window Optimization**: Keep LLM prompts focused and relevant while maintaining philosophical depth
- **Dynamic Content Selection**: Update conversation context based on user input without breaking flow
- **Coherent Philosophical Dialogue**: Maintain natural philosophical conversation patterns (Socratic, dialectical)
- **Multi-User Session Management**: Handle concurrent users with isolated conversation states

## High-Level Architecture

### Data Flow
```
External APIs → Master Orchestrator → Redis Cache (Master Dataset)
                                        ↓
User Input → Meaning Extraction → State Machine → Chat Orchestrator
                                                      ↓
Context Intelligence → Coherence Check → Prompt Generation → LLM
                                                                ↓
MongoDB (History) ← Response Processing ← LLM Response
```

### Three-Layer System
1. **Master Orchestrator**: Aggregates philosophical data from APIs into Redis-cached master dataset
2. **Chat Orchestrator**: Creates conversation-specific datasets and manages dialogue state
3. **Agent Framework**: Specialized agents handle specific tasks (meaning extraction, context selection, coherence)

## Core Components to Build

### 1. Master Orchestrator Script
```python
# Responsibilities:
- Fetch philosophical data from multiple APIs
- Cache in Redis with TTL-based freshness
- Provide fallback datasets for offline operation
- Support incremental updates and data versioning
```

### 2. Chat Orchestrator Script  
```python
# Responsibilities:
- Initialize conversation state per user session
- Manage context selection based on conversation analysis
- Generate state-appropriate prompts with philosopher persona
- Coordinate with coherence management for smooth updates
```

### 3. Enhanced Agent Framework
```python
# 9 Specialized Agents:
- Master Coordinating Agent (session management)
- Data Aggregation Agent (API calls, Redis management)  
- Context Intelligence Agent (token-aware content selection)
- Enhanced Meaning Extraction Agent (4-layer analysis)
- Philosopher Persona Agent (consistent character voice)
- Conversation State Agent (dialogue state transitions)
- Relevance Scoring Agent (content prioritization)
- Conversation Flow Agent (Socratic/dialectical patterns)
- Coherence Management Agent (smooth context transitions)
- Storage Agent (Redis + MongoDB operations)
```

### 4. Conversation State Machine
```python
# 7 States with Natural Transitions:
Introduction → Exploration → Deep Dive → Socratic Questioning 
                                    ↓
Synthesis ← Dialectical Exchange ← Recovery (when needed)

# Each state has specific:
- Prompt templates
- Transition triggers  
- Content priorities
- Recovery mechanisms
```

### 5. Enhanced Meaning Extraction (4 Layers)
```python
# Layer 1 - Surface: keywords, entities, philosophical terms
# Layer 2 - Conceptual: argument structures, logical patterns
# Layer 3 - Intent: user goals (explore, challenge, clarify, synthesize)
# Layer 4 - Emotional: engagement state, confidence, frustration
```

### 6. Context Window Intelligence
```python
# Token-aware content management:
- Pre-calculate token counts for content types
- Prioritize based on conversation state + user interest
- Model-specific optimization (GPT-4 vs Claude vs Ollama)
- Intelligent compression while maintaining philosophical depth
```

### 7. Coherence Management System
```python
# Ensure context updates don't break conversation flow:
- Score compatibility between old/new context
- Generate transition prompts for major shifts
- Implement gradual context introduction
- Provide recovery when conversations fragment
```

## Required Tech Stack

### Core Backend
```python
# Primary Language: Python 3.9+
# Web Framework: FastAPI (with WebSocket support)
# Async: asyncio for concurrent operations
# Agent Framework: CrewAI or LangGraph
```

### Data & Caching
```python
# Primary Cache: Redis with redis-py (async)
# Persistence: MongoDB with motor (async driver)
# Vector Search: sentence-transformers for semantic similarity
# Token Counting: tiktoken for accurate model-specific counting
```

### NLP & AI
```python
# NLP: spaCy for philosophical text processing
# Embeddings: sentence-transformers for semantic analysis
# Topic Modeling: scikit-learn for conceptual analysis
# Sentiment: TextBlob or similar for emotional layer
```

### LLM Integration
```python
# Local Testing: ollama-python for local models
# API Models: Dynamic client selection based on user subscription
#   - openai (ChatGPT)
#   - anthropic (Claude)  
#   - Custom HTTP clients for other providers (DeepSeek, etc.)
```

### State Management
```python
# State Machine: python-statemachine or transitions
# State Persistence: Redis-backed with automatic expiration
# Session Management: FastAPI sessions with Redis storage
```

## Key Redis Data Structures

### Master Dataset Cache
```python
# Key Pattern: master:{philosopher}:{category}:{version}
# TTL: 24 hours for stable, 1 hour for dynamic content
# Example: master:socrates:biography:v1.2
```

### Session Data Cache
```python
# Key Pattern: session:{user_id}:{session_id}:{component}
# Components: state, context, history_summary, persona_config
# TTL: 2 hours active, 24 hours recent
```

### Context Intelligence Cache
```python
# Key Pattern: context:{session_id}:{state}:{relevance_hash}
# Purpose: Cache expensive context computations
# TTL: 30 minutes
```

## Critical Implementation Details

### 1. Model Configuration (User Subscription-Driven)
```python
# Passed to orchestrators, not managed by them:
user_config = {
    "subscription_tier": "premium",  # determines model access
    "available_models": ["gpt-4", "claude-3", "local-llama"],
    "default_model": "gpt-4",
    "context_limits": {"gpt-4": 8192, "claude-3": 8192},
    "api_keys": {...}  # managed externally
}

# For testing: Always support local Ollama fallback
test_config = {
    "subscription_tier": "test",
    "available_models": ["ollama-llama2", "ollama-mistral"],
    "default_model": "ollama-llama2"
}
```

### 2. Agent Communication Pattern
```python
# Event-driven messaging between agents
# Shared Redis state for session data
# Async task queues for non-blocking operations
# Error handling with graceful degradation

# Example flow:
user_input → meaning_extraction_agent → state_transition_check → 
context_update_needed → relevance_scoring → coherence_check → 
prompt_generation → llm_call → response_processing → storage
```

### 3. Context Window Optimization Strategy
```python
# Priority System (high to low):
1. Current conversation state requirements (always include)
2. User's immediate topic focus (based on meaning extraction)
3. Recent conversation context (last 3-5 turns)
4. Related philosophical concepts (semantic similarity)
5. General philosopher background (compressed as needed)

# Token Budget Allocation:
- 30% for conversation state essentials
- 25% for user focus area
- 20% for recent context
- 15% for related concepts  
- 10% for general background
```

### 4. Coherence Scoring Algorithm
```python
def calculate_coherence_score(current_context, new_content):
    # Semantic similarity (40%)
    semantic_score = cosine_similarity(current_embeddings, new_embeddings)
    
    # Philosophical consistency (30%) 
    philosophy_score = check_philosophical_alignment(current, new)
    
    # Conversation flow (20%)
    flow_score = assess_natural_transition(current_state, new_content)
    
    # Temporal coherence (10%)
    temporal_score = check_logical_progression(conversation_history)
    
    return weighted_average([semantic_score, philosophy_score, flow_score, temporal_score])

# Accept updates only if coherence_score > 0.7
```

### 5. Error Handling & Recovery
```python
# API Failures: Fallback to cached/local datasets
# Redis Failures: Fallback to in-memory with warning
# LLM Failures: Model switching with degradation notice
# Coherence Failures: Recovery state with conversation reset option
# Agent Failures: Graceful degradation with reduced functionality
```

## File Structure You'll Create
```
philosopher_orchestrator/
├── orchestrators/
│   ├── master_orchestrator.py      # Main data aggregation
│   ├── chat_orchestrator.py        # Conversation management
│   └── state_machine.py            # Conversation states
├── agents/
│   ├── base_agent.py               # Agent framework base
│   ├── meaning_extraction_agent.py # 4-layer analysis
│   ├── context_intelligence_agent.py # Token management
│   ├── coherence_agent.py          # Flow management
│   └── persona_agent.py            # Philosopher voice
├── services/
│   ├── redis_service.py            # Cache management
│   ├── mongodb_service.py          # Persistence
│   ├── llm_service.py             # Model integration
│   └── api_service.py             # External data APIs
├── utils/
│   ├── token_counter.py           # Model-specific counting
│   ├── similarity_engine.py       # Semantic search
│   └── config_manager.py          # Environment configuration
├── models/
│   ├── conversation_state.py      # State definitions
│   ├── philosopher_data.py        # Data structures
│   └── session_data.py            # Session management
└── main.py                        # FastAPI application
```

## Key Success Metrics
- **Context Relevance**: >85% of context should be relevant to current conversation
- **Response Coherence**: <5% of responses should require clarification
- **Token Efficiency**: Use <70% of available context window on average
- **State Transitions**: >90% should feel natural to users
- **Multi-User Performance**: Support 50+ concurrent conversations
- **Response Time**: <3 seconds for prompt generation + LLM call

## Testing Strategy
```python
# Unit Tests: Each agent and component individually
# Integration Tests: Full conversation flows
# Performance Tests: Multi-user concurrent sessions  
# Coherence Tests: Context update scenarios
# Model Tests: Local Ollama + API model switching
```

This system creates intelligent, contextual philosophical conversations by intelligently managing what information reaches the LLM while maintaining natural dialogue flow and philosophical depth.