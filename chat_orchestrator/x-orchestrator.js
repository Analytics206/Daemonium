// ==========================================
// FASTAPI-BASED ORCHESTRATOR ARCHITECTURE
// ==========================================

// /lib/orchestrator/PhilosopherOrchestrator.js (Server-side, using FastAPI endpoints)
class PhilosopherOrchestrator {
    constructor(fastApiBaseUrl) {
      this.apiBaseUrl = fastApiBaseUrl || process.env.FASTAPI_BASE_URL || 'http://localhost:8000';
      this.activeConversations = new Map(); // In-memory conversation state
      this.apiHeaders = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.FASTAPI_API_KEY}` // If you use API keys
      };
    }
  
    // Helper method for FastAPI calls
    async callFastAPI(endpoint, method = 'GET', body = null) {
      const url = `${this.apiBaseUrl}${endpoint}`;
      const options = {
        method,
        headers: this.apiHeaders
      };
  
      if (body) {
        options.body = JSON.stringify(body);
      }
  
      const response = await fetch(url, options);
      
      if (!response.ok) {
        throw new Error(`FastAPI error: ${response.status} ${response.statusText}`);
      }
  
      return await response.json();
    }
  
    // STEP 1: Initialize with specific philosopher using FastAPI
    async setPhilosopher(philosopherName) {
      try {
        // Get philosopher metadata from FastAPI
        const philosopherData = await this.callFastAPI(`/philosophers/${philosopherName}`);
        
        if (!philosopherData) {
          throw new Error(`Philosopher '${philosopherName}' not found`);
        }
  
        this.currentPhilosopher = philosopherData.slug || philosopherName.toLowerCase();
        this.philosopherData = philosopherData;
        
        console.log(`Initialized orchestrator for ${philosopherData.name}`);
        return true;
        
      } catch (error) {
        console.error(`Failed to initialize philosopher ${philosopherName}:`, error);
        return false;
      }
    }
  
    // STEP 2: Analyze user input using FastAPI endpoints
    async analyzeUserInput(userInput, conversationContext = null) {
      try {
        // Call FastAPI analysis endpoint
        const analysisResult = await this.callFastAPI('/analysis/input', 'POST', {
          text: userInput,
          philosopher: this.currentPhilosopher,
          conversation_context: conversationContext
        });
  
        return {
          detectedThemes: analysisResult.detected_themes || [],
          toneMode: analysisResult.suggested_tone || 'default',
          modernReferences: analysisResult.modern_references || [],
          complexity: analysisResult.complexity_level || 'medium',
          emotional_state: analysisResult.emotional_state || 'neutral',
          requires_tone_shift: analysisResult.requires_tone_shift || false
        };
  
      } catch (error) {
        console.error('Error analyzing user input via FastAPI:', error);
        // Fallback to basic analysis
        return {
          detectedThemes: [],
          toneMode: 'default',
          modernReferences: [],
          complexity: 'medium'
        };
      }
    }
  
    // STEP 3: Gather relevant data from multiple FastAPI endpoints
    async gatherRelevantData(analysis, conversationContext) {
      try {
        // Make parallel calls to multiple FastAPI endpoints
        const [
          persona,
          conversationLogic,
          aphorisms,
          themes,
          modernAdaptations,
          discussionHooks
        ] = await Promise.all([
          // Get persona
          this.callFastAPI(`/philosophers/${this.currentPhilosopher}/persona`),
          
          // Get conversation logic for current tone
          this.callFastAPI(`/philosophers/${this.currentPhilosopher}/conversation-logic`),
          
          // Get relevant aphorisms
          this.callFastAPI(`/philosophers/${this.currentPhilosopher}/aphorisms`, 'POST', {
            themes: analysis.detectedThemes,
            tone: analysis.toneMode,
            exclude_recent: conversationContext?.recent_aphorisms || [],
            limit: 3
          }),
          
          // Get theme details
          analysis.detectedThemes.length > 0 ? 
            this.callFastAPI(`/philosophers/${this.currentPhilosopher}/themes`, 'POST', {
              theme_names: analysis.detectedThemes
            }) : Promise.resolve([]),
          
          // Get modern adaptations if needed
          analysis.modernReferences.length > 0 ?
            this.callFastAPI(`/philosophers/${this.currentPhilosopher}/modern-adaptation`, 'POST', {
              topics: analysis.modernReferences
            }) : Promise.resolve([]),
          
          // Get discussion hooks
          this.callFastAPI(`/philosophers/${this.currentPhilosopher}/discussion-hooks`, 'POST', {
            themes: analysis.detectedThemes,
            tone: analysis.toneMode,
            relationship_depth: conversationContext?.relationship_depth || 'formal'
          })
        ]);
  
        return {
          persona,
          conversationLogic,
          aphorisms: aphorisms.items || aphorisms,
          themes: themes.items || themes,
          modernAdaptations: modernAdaptations.items || modernAdaptations,
          discussionHooks: discussionHooks.items || discussionHooks
        };
  
      } catch (error) {
        console.error('Error gathering data via FastAPI:', error);
        
        // Fallback: get minimal data
        try {
          const persona = await this.callFastAPI(`/philosophers/${this.currentPhilosopher}/persona`);
          return { persona, aphorisms: [], themes: [], discussionHooks: [] };
        } catch (fallbackError) {
          console.error('Fallback failed:', fallbackError);
          return { persona: { name: this.currentPhilosopher }, aphorisms: [], themes: [], discussionHooks: [] };
        }
      }
    }
  
    // STEP 4: Build dynamic response prompt
    buildResponsePrompt(userInput, analysis, relevantData, conversationContext) {
      const philosopher = this.philosopherData;
      const persona = relevantData.persona;
      
      // Get tone configuration
      const toneConfig = relevantData.conversationLogic?.tone_modes?.[analysis.toneMode] || {
        description: 'thoughtful and engaging',
        sentence_structure: 'clear and philosophical'
      };
      
      // Determine core idea to focus on
      let coreIdea = "the fundamental questions of human existence and meaning";
      if (relevantData.themes && relevantData.themes.length > 0) {
        const theme = relevantData.themes[0];
        coreIdea = theme.core_concept || theme.definition || theme.description || coreIdea;
      }
  
      // Select aphorism and discussion hook
      const selectedAphorism = relevantData.aphorisms?.length > 0 ? 
        relevantData.aphorisms[Math.floor(Math.random() * relevantData.aphorisms.length)] : null;
  
      const discussionHook = relevantData.discussionHooks?.length > 0 ?
        relevantData.discussionHooks[Math.floor(Math.random() * relevantData.discussionHooks.length)] :
        { question: "What are your thoughts on this matter?" };
  
      // Build conversation context string
      let contextString = "";
      if (conversationContext && conversationContext.turn_number > 0) {
        contextString = `
  CONVERSATION CONTEXT:
  - Turn ${conversationContext.turn_number + 1} of our conversation
  - Current tone: ${conversationContext.current_tone}
  - Relationship depth: ${conversationContext.relationship_depth}
  - Dominant themes: ${conversationContext.dominant_themes?.join(', ') || 'none'}
  - User's emotional state: ${analysis.emotional_state}`;
      }
  
      // Handle tone shifts
      let toneInstruction = "";
      if (analysis.requires_tone_shift) {
        toneInstruction = `
  TONE SHIFT: Naturally transition to ${analysis.toneMode} tone based on the user's emotional state and conversation context.`;
      }
  
      // Build modern context
      let modernContext = "";
      if (relevantData.modernAdaptations?.length > 0) {
        modernContext = `\nModern Context: ${relevantData.modernAdaptations[0].analysis || relevantData.modernAdaptations[0].description}`;
      }
  
      return `You are ${philosopher.name}, the renowned philosopher.
  
  PERSONA: ${persona.voice_characteristics?.tone || 'philosophical and thoughtful'}
  Style: ${persona.voice_characteristics?.style || 'clear, engaging, thought-provoking'}
  ${contextString}
  ${toneInstruction}
  
  USER'S MESSAGE: "${userInput}"
  
  PHILOSOPHICAL APPROACH:
  - Core theme: ${coreIdea}
  - Response tone: ${analysis.toneMode} - ${toneConfig.description}
  - Structure: ${toneConfig.sentence_structure}${modernContext}
  
  ${selectedAphorism ? `WEAVE IN THIS INSIGHT: "${selectedAphorism.text || selectedAphorism.content}"` : ''}
  
  RESPONSE STRUCTURE:
  1. ${conversationContext ? 'Acknowledge conversation continuity and' : ''} address their question
  2. Apply your philosophical perspective using ${analysis.toneMode} approach
  3. Connect to core themes: ${analysis.detectedThemes.join(', ') || 'existence and meaning'}
  4. End with: "${discussionHook.question || discussionHook.text || 'What do you think?'}"
  
  Maintain your authentic philosophical voice while being engaging and accessible.`;
    }
  
    // Main orchestration method using FastAPI
    async generateConversationalResponse(conversationId, userInput, philosopherName = null) {
      try {
        // Set philosopher if specified
        if (philosopherName && philosopherName !== this.currentPhilosopher) {
          const success = await this.setPhilosopher(philosopherName);
          if (!success) {
            return {
              error: `Philosopher '${philosopherName}' not available`,
              prompt: null
            };
          }
        }
  
        // Get or create conversation state
        let conversationState = this.activeConversations.get(conversationId);
        if (!conversationState) {
          conversationState = {
            conversationId,
            philosopher: this.currentPhilosopher,
            turnNumber: 0,
            currentTone: 'default',
            dominantThemes: [],
            relationshipDepth: 'formal',
            recentAphorisms: [],
            conversationHistory: []
          };
          this.activeConversations.set(conversationId, conversationState);
        }
  
        // Analyze input with conversation context
        const analysis = await this.analyzeUserInput(userInput, {
          turn_number: conversationState.turnNumber,
          current_tone: conversationState.currentTone,
          dominant_themes: conversationState.dominantThemes,
          relationship_depth: conversationState.relationshipDepth
        });
  
        // Gather relevant data via FastAPI
        const relevantData = await this.gatherRelevantData(analysis, {
          recent_aphorisms: conversationState.recentAphorisms,
          relationship_depth: conversationState.relationshipDepth
        });
  
        // Build response prompt
        const prompt = this.buildResponsePrompt(
          userInput, 
          analysis, 
          relevantData, 
          conversationState
        );
  
        // Update conversation state
        conversationState.turnNumber += 1;
        conversationState.currentTone = analysis.toneMode;
        
        // Update themes (accumulate)
        analysis.detectedThemes.forEach(theme => {
          if (!conversationState.dominantThemes.includes(theme)) {
            conversationState.dominantThemes.push(theme);
          }
        });
  
        // Track recent aphorisms
        if (relevantData.aphorisms?.length > 0) {
          conversationState.recentAphorisms.push(relevantData.aphorisms[0].text);
          if (conversationState.recentAphorisms.length > 5) {
            conversationState.recentAphorisms.shift();
          }
        }
  
        // Add to conversation history
        conversationState.conversationHistory.push({
          userInput,
          analysis,
          timestamp: new Date()
        });
  
        // Log interaction via FastAPI
        await this.logInteractionViaFastAPI(conversationId, userInput, analysis, relevantData);
  
        return {
          prompt,
          conversationState: {
            conversationId,
            turnNumber: conversationState.turnNumber,
            currentTone: conversationState.currentTone,
            dominantThemes: conversationState.dominantThemes,
            relationshipDepth: conversationState.relationshipDepth
          },
          metadata: {
            philosopher: this.currentPhilosopher,
            toneShift: analysis.requires_tone_shift ? analysis.toneMode : null,
            themesDetected: analysis.detectedThemes
          }
        };
  
      } catch (error) {
        console.error('Error generating conversational response:', error);
        return {
          error: 'Failed to generate response',
          prompt: this.getFallbackResponse(userInput)
        };
      }
    }
  
    // Log interaction via FastAPI
    async logInteractionViaFastAPI(conversationId, userInput, analysis, relevantData) {
      try {
        await this.callFastAPI('/interactions/log', 'POST', {
          conversation_id: conversationId,
          philosopher: this.currentPhilosopher,
          user_input: userInput,
          analysis: analysis,
          timestamp: new Date().toISOString(),
          collections_used: Object.keys(relevantData)
        });
      } catch (error) {
        console.error('Failed to log interaction:', error);
        // Don't fail the main response for logging errors
      }
    }
  
    // Get available philosophers via FastAPI
    async getAvailablePhilosophers() {
      try {
        const result = await this.callFastAPI('/philosophers');
        return result.philosophers || result;
      } catch (error) {
        console.error('Error fetching philosophers from FastAPI:', error);
        return [];
      }
    }
  
    getFallbackResponse(userInput) {
      return `I am ${this.philosopherData?.name || 'a philosopher'}. You asked: "${userInput}". 
  Let me reflect on this question and offer some philosophical insights.`;
    }
  
    // Cleanup old conversations
    cleanupOldConversations(hoursOld = 24) {
      const cutoff = new Date(Date.now() - (hoursOld * 60 * 60 * 1000));
      
      for (const [conversationId, state] of this.activeConversations.entries()) {
        const lastActivity = state.conversationHistory[state.conversationHistory.length - 1]?.timestamp;
        if (lastActivity && lastActivity < cutoff) {
          this.activeConversations.delete(conversationId);
        }
      }
    }
  }
  
  // ==========================================
  // NEXT.JS API ROUTES (Using FastAPI Orchestrator)
  // ==========================================
  
  // /app/api/chat/route.js
  import { NextRequest, NextResponse } from 'next/server';
  
  // Singleton orchestrator instance
  let orchestratorInstance = null;
  
  function getOrchestrator() {
    if (!orchestratorInstance) {
      orchestratorInstance = new PhilosopherOrchestrator(process.env.FASTAPI_BASE_URL);
    }
    return orchestratorInstance;
  }
  
  export async function POST(request) {
    try {
      const { message, conversationId, philosopher } = await request.json();
      
      if (!message || !conversationId) {
        return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
      }
  
      const orchestrator = getOrchestrator();
      
      // Generate response using FastAPI-based orchestrator
      const result = await orchestrator.generateConversationalResponse(
        conversationId,
        message,
        philosopher
      );
  
      if (result.error) {
        return NextResponse.json({ error: result.error }, { status: 400 });
      }
  
      // Call your LLM with the generated prompt
      const llmResponse = await callLLM(result.prompt);
      
      return NextResponse.json({
        success: true,
        response: llmResponse,
        metadata: result.metadata,
        conversationState: result.conversationState
      });
  
    } catch (error) {
      console.error('Chat API Error:', error);
      return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
  }
  
  // /app/api/philosophers/route.js
  export async function GET() {
    try {
      const orchestrator = getOrchestrator();
      const philosophers = await orchestrator.getAvailablePhilosophers();
      
      return NextResponse.json({ philosophers });
    } catch (error) {
      console.error('Philosophers API Error:', error);
      return NextResponse.json({ error: 'Failed to fetch philosophers' }, { status: 500 });
    }
  }
  
  // Helper function to call LLM
  async function callLLM(prompt) {
    // Your LLM API call (OpenAI, Anthropic, etc.)
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-4',
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 500,
        temperature: 0.8
      })
    });
  
    const data = await response.json();
    return data.choices[0].message.content;
  }
  
  // ==========================================
  // EXPECTED FASTAPI ENDPOINTS
  // ==========================================
  
  /*
  Your FastAPI should have these endpoints:
  
  1. GET /philosophers - List all philosophers
  2. GET /philosophers/{philosopher_name} - Get philosopher details
  3. GET /philosophers/{philosopher_name}/persona - Get persona data
  4. GET /philosophers/{philosopher_name}/conversation-logic - Get conversation logic
  5. POST /philosophers/{philosopher_name}/aphorisms - Get filtered aphorisms
  6. POST /philosophers/{philosopher_name}/themes - Get theme details
  7. POST /philosophers/{philosopher_name}/modern-adaptation - Get modern adaptations
  8. POST /philosophers/{philosopher_name}/discussion-hooks - Get discussion hooks
  9. POST /analysis/input - Analyze user input for themes/tone
  10. POST /interactions/log - Log conversation interactions
  
  Example FastAPI endpoint structure:
  
  @app.get("/philosophers/{philosopher_name}/aphorisms")
  async def get_aphorisms(
      philosopher_name: str,
      themes: List[str] = Query([]),
      tone: str = Query("default"),
      exclude_recent: List[str] = Query([]),
      limit: int = Query(3)
  ):
      # Your existing MongoDB logic here
      collection = db[f"{philosopher_name}_aphorisms"]
      
      filter_query = {}
      if themes:
          filter_query["themes"] = {"$in": themes}
      if exclude_recent:
          filter_query["text"] = {"$nin": exclude_recent}
      
      aphorisms = await collection.find(filter_query).limit(limit).to_list()
      return {"items": aphorisms}
  */
  
  // ==========================================
  // ENVIRONMENT CONFIGURATION
  // ==========================================
  
  // /.env.local
  /*
  FASTAPI_BASE_URL=http://localhost:8000
  FASTAPI_API_KEY=your_fastapi_api_key_if_needed
  OPENAI_API_KEY=your_openai_api_key
  NEXTAUTH_SECRET=your_nextauth_secret
  */
  
  export default PhilosopherOrchestrator;