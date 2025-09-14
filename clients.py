import os
from typing import Optional, Literal
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

class DynamicLLMClient:
    """Dynamic LLM client that can be configured at runtime"""
    
    def __init__(self):
        self._client_analyzer = None
        self._client_generator = None
        self._current_provider = None
        self._current_api_key = None
    
    def initialize_clients(self, provider: Literal["openai", "gemini"], api_key: str) -> bool:
        """Initialize clients with the specified provider and API key"""
        try:
            if provider == "openai":
                self._client_analyzer = ChatOpenAI(
                    openai_api_key=api_key,
                    model="gpt-4o",
                    temperature=0.1,
                    max_tokens=4000,
                    timeout=30,
                    max_retries=3
                )
                self._client_generator = ChatOpenAI(
                    openai_api_key=api_key,
                    model="gpt-4o",
                    temperature=0.1,
                    max_tokens=4000,
                    timeout=30,
                    max_retries=3
                )
            elif provider == "gemini":
                self._client_analyzer = ChatGoogleGenerativeAI(
                    google_api_key=api_key,
                    model="gemini-1.5-pro",
                    temperature=0.1,
                    max_tokens=4000,
                    timeout=30,
                    max_retries=3
                )
                self._client_generator = ChatGoogleGenerativeAI(
                    google_api_key=api_key,
                    model="gemini-1.5-pro", 
                    temperature=0.1,
                    max_tokens=4000,
                    timeout=30,
                    max_retries=3
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            self._current_provider = provider
            self._current_api_key = api_key
            return True
            
        except Exception as e:
            print(f"Failed to initialize {provider} clients: {e}")
            return False
    
    def get_analyzer_client(self):
        """Get the analyzer client"""
        if not self._client_analyzer:
            raise ValueError("Clients not initialized. Call initialize_clients() first.")
        return self._client_analyzer
    
    def get_generator_client(self):
        """Get the generator client"""
        if not self._client_generator:
            raise ValueError("Clients not initialized. Call initialize_clients() first.")
        return self._client_generator
    
    def is_initialized(self) -> bool:
        """Check if clients are initialized"""
        return self._client_analyzer is not None and self._client_generator is not None
    
    def get_current_provider(self) -> Optional[str]:
        """Get the current provider"""
        return self._current_provider

# Global client manager instance
_client_manager = DynamicLLMClient()

def initialize_llm_clients(provider: Literal["openai", "gemini"], api_key: str) -> bool:
    """Initialize LLM clients with the specified provider and API key"""
    return _client_manager.initialize_clients(provider, api_key)

def get_client_analyzer():
    """Get the analyzer client"""
    return _client_manager.get_analyzer_client()

def get_client_generator():
    """Get the generator client"""
    return _client_manager.get_generator_client()

def is_clients_initialized() -> bool:
    """Check if clients are initialized"""
    return _client_manager.is_initialized()

def get_current_provider() -> Optional[str]:
    """Get the current LLM provider"""
    return _client_manager.get_current_provider()

# For backward compatibility - these will raise errors if not initialized
@property
def client_analyzer():
    return get_client_analyzer()

@property  
def client_generator():
    return get_client_generator()