from typing import Dict, Optional, Any, Literal
import logging
from openai import OpenAI
from groq import Groq
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class BaseModel:
    """Base class for LLM models."""
    
    def __init__(self, model_name: str):
        """Initialize the model.
        
        Args:
            model_name: Name of the model
        """
        self.model_name = model_name
    
    async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 150) -> Dict[str, Any]:
        """Generate text from a prompt.
        
        Args:
            prompt: The prompt to generate text from
            temperature: Controls randomness
            max_tokens: Maximum number of tokens to generate
        
        Returns:
            Dict[str, Any]: Generated text and metadata
        """
        raise NotImplementedError("Subclasses must implement generate method")


class OpenAIModel(BaseModel):
    """OpenAI model implementation."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize the OpenAI model.
        
        Args:
            model_name: Name of the OpenAI model
        """
        super().__init__(model_name)
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 150) -> Dict[str, Any]:
        """Generate text using OpenAI.
        
        Args:
            prompt: The prompt to generate text from
            temperature: Controls randomness
            max_tokens: Maximum number of tokens to generate
        
        Returns:
            Dict[str, Any]: Generated text and metadata
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "text": response.choices[0].message.content,
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {e}")
            raise


class GroqModel(BaseModel):
    """Groq model implementation."""
    
    def __init__(self, model_name: str = "mixtral-8x7b-32768"):
        """Initialize the Groq model.
        
        Args:
            model_name: Name of the Groq model
        """
        super().__init__(model_name)
        self.client = Groq(api_key=settings.GROQ_API_KEY)
    
    async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 150) -> Dict[str, Any]:
        """Generate text using Groq.
        
        Args:
            prompt: The prompt to generate text from
            temperature: Controls randomness
            max_tokens: Maximum number of tokens to generate
        
        Returns:
            Dict[str, Any]: Generated text and metadata
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "text": response.choices[0].message.content,
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"Error generating text with Groq: {e}")
            raise


def get_model(provider: Optional[Literal["openai", "groq"]] = None, model_name: Optional[str] = None) -> BaseModel:
    """Get a model instance based on provider and model name.
    
    Args:
        provider: Provider name (openai or groq)
        model_name: Model name
    
    Returns:
        BaseModel: Model instance
    
    Raises:
        ValueError: If provider is invalid
    """
    # Use default provider if not specified
    if provider is None:
        provider = settings.DEFAULT_PROVIDER
    
    # Use default model if not specified
    if model_name is None:
        model_name = settings.DEFAULT_MODEL
    
    # Create model instance based on provider
    if provider == "openai":
        return OpenAIModel(model_name)
    elif provider == "groq":
        return GroqModel(model_name)
    else:
        raise ValueError(f"Invalid provider: {provider}")
