# mcp_server.py - Single MCP server
from mcp import MCPServer
from .models import OllamaService, OpenAIService, AnthropicService

class PhilosophyMCPServer(MCPServer):
    def __init__(self):
        super().__init__()
        
        # Register the same tools for all models
        self.add_tool(self.chat_with_philosopher_tool)
        self.add_tool(self.explore_concept_tool)
        
        # Different model service implementations
        self.model_services = {
            "ollama": OllamaService(),
            "openai": OpenAIService(), 
            "anthropic": AnthropicService(),
            "together": TogetherAIService()
        }

    # Tool definition (same interface for all models)
    @tool("chat_with_philosopher")
    async def chat_with_philosopher_tool(
        self, 
        philosopher: str, 
        message: str, 
        model_preference: str = "auto"
    ):
        # Route to appropriate model service
        selected_service = self._select_model_service(model_preference, message)
        
        # Each service implements the same interface differently
        return await selected_service.chat_with_philosopher(philosopher, message)