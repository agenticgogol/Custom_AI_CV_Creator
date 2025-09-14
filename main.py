import os
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nicegui import app

from cv_agent.agent import build_cv_agent
from cv_agent.clients import is_clients_initialized, get_current_provider

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    logger.info("Starting FastAPI app creation...")
    
    # Create FastAPI app
    fastapi_app = FastAPI(
        title="AI CV Creator Agent - Enhanced",
        description="Transform your resume to match job descriptions with AI-powered analysis and multi-LLM support",
        version="2.0.0"
    )
    
    # Add CORS middleware
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize the CV agent (without LLM clients - they'll be configured by user)
    try:
        logger.info("Building CV agent...")
        agent = build_cv_agent(local_memory=True)
        logger.info(f"Agent created successfully: {type(agent)}")
        
        # Set the global agent reference
        from cv_agent.chat_app import set_global_agent
        set_global_agent(agent)
        
        print("✅ CV Agent initialized successfully (LLM clients will be configured by user)")
    except Exception as e:
        logger.error(f"Failed to initialize CV Agent: {e}")
        print(f"❌ Failed to initialize CV Agent: {e}")
        raise e
    
    # Initialize NiceGUI app
    logger.info("Initializing NiceGUI app...")
    from cv_agent.chat_app import init_cv_app
    init_cv_app(fastapi_app)
    logger.info("NiceGUI app initialized")
    
    # Health check endpoint
    @fastapi_app.get("/health")
    async def health_check():
        from cv_agent.chat_app import get_global_agent
        agent = get_global_agent()
        return {
            "status": "healthy",
            "service": "cv-creator-agent-enhanced",
            "version": "2.0.0",
            "agent_initialized": agent is not None,
            "llm_initialized": is_clients_initialized(),
            "current_provider": get_current_provider()
        }
    
    # LLM status endpoint
    @fastapi_app.get("/llm/status")
    async def llm_status():
        return {
            "llm_initialized": is_clients_initialized(),
            "current_provider": get_current_provider(),
            "supported_providers": ["openai", "gemini"]
        }
    
    # Agent status endpoint
    @fastapi_app.get("/agent/status")
    async def agent_status():
        from cv_agent.chat_app import get_global_agent
        agent = get_global_agent()
        return {
            "agent_initialized": agent is not None,
            "agent_type": "LangGraph CV Creator Enhanced" if agent else None,
            "llm_ready": is_clients_initialized(),
            "ready_for_processing": agent is not None and is_clients_initialized()
        }
    
    logger.info("FastAPI app creation completed")
    return fastapi_app


def get_agent():
    """Get the global agent instance - for backwards compatibility"""
    from cv_agent.chat_app import get_global_agent
    return get_global_agent()


def main():
    """Main application entry point"""
    # No longer require environment variables since users will provide API keys
    logger.info("Starting CV Creator Agent - Enhanced Version")
    
    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    environment = os.getenv("ENVIRONMENT", "development")
    
    print(f"🚀 Starting Enhanced CV Creator Agent on {host}:{port}")
    print(f"📋 Environment: {environment}")
    print(f"🤖 Multi-LLM Support: OpenAI GPT-4, Google Gemini")
    print(f"⚙️ User Configuration Required: API keys will be provided via UI")
    
    # Create the app
    fastapi_app = create_app()
    
    # Run the application
    if environment == "development":
        logger.info("Starting in development mode...")
        uvicorn.run(
            fastapi_app,
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )
    else:
        logger.info("Starting in production mode...")
        uvicorn.run(
            fastapi_app,
            host=host,
            port=port,
            log_level="info"
        )


if __name__ == "__main__":
    main()