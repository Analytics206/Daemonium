# models/base.py
class BaseModelService:
    async def chat_with_philosopher(self, philosopher: str, message: str) -> str:
        context = await self.get_context(philosopher, message)
        prompt = self.build_prompt(philosopher, message, context)
        return await self.generate_response(prompt)
    
    def build_prompt(self, philosopher: str, message: str, context: dict) -> str:
        # Base prompt template - can be overridden
        return f"""You are {philosopher}. {context['bio']}
        
Core ideas: {context['main_ideas']}
Relevant aphorisms: {context['aphorisms']}

User asks: {message}

Respond as {philosopher} would:"""

# models/ollama.py
class OllamaService(BaseModelService):
    async def generate_response(self, prompt: str) -> str:
        response = await self.ollama_client.generate(
            model="llama3.1:8b",
            prompt=prompt,
            options={
                "temperature": 0.8,
                "top_p": 0.9,
                "max_tokens": 500
            }
        )
        return response['response']

# models/openai.py  
class OpenAIService(BaseModelService):
    def build_prompt(self, philosopher: str, message: str, context: dict) -> str:
        # OpenAI-specific prompt optimization
        return f"""You are {philosopher}, the renowned philosopher.

Background: {context['bio']}
Key Philosophy: {context['main_ideas']}

Guidelines:
- Respond in {philosopher}'s voice and style
- Reference relevant concepts naturally
- Be authentic to their historical perspective

User: {message}

{philosopher}:"""
    
    async def generate_response(self, prompt: str) -> str:
        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )
        return response.choices[0].message.content

# models/anthropic.py
class AnthropicService(BaseModelService):
    def build_prompt(self, philosopher: str, message: str, context: dict) -> str:
        # Anthropic Claude-specific prompt style
        return f"""<philosopher>{philosopher}</philosopher>
<context>
{context['bio']}
Key ideas: {context['main_ideas']}
Relevant quotes: {context['aphorisms']}
</context>

<instruction>
Respond as {philosopher} would, drawing from their authentic philosophical perspective and historical context.
</instruction>

<user_message>
{message}
</user_message>"""
    
    async def generate_response(self, prompt: str) -> str:
        response = await self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=450
        )
        return response.content[0].text