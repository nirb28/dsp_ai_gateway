from typing import Optional, Dict, List, Literal, Any
from pydantic import BaseModel, Field, validator

class GenerateRequest(BaseModel):
    """Schema for text generation request."""
    prompt: str = Field(..., description="The prompt to generate text from")
    temperature: float = Field(0.7, ge=0, le=1, description="Controls randomness. Lower values make responses more deterministic")
    max_tokens: int = Field(150, gt=0, description="Maximum number of tokens to generate")
    provider: Optional[Literal["openai", "groq"]] = Field(None, description="The provider to use for generation")
    model: Optional[str] = Field(None, description="The model to use for generation")

class GenerateResponse(BaseModel):
    """Schema for text generation response."""
    text: str = Field(..., description="The generated text")
    model: str = Field(..., description="The model used for generation")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage information")

class ClientAuth(BaseModel):
    """Schema for client authentication."""
    client_id: str = Field(..., description="Client ID")
    client_secret: str = Field(..., description="Client secret")

class RateLimit(BaseModel):
    """Schema for rate limiting configuration."""
    requests_per_minute: int = Field(..., gt=0, description="Maximum requests per minute")
    tokens_per_day: int = Field(..., gt=0, description="Maximum tokens per day")

class ClientConfig(BaseModel):
    """Schema for client configuration."""
    client_id: str = Field(..., description="Client ID")
    name: str = Field(..., description="Client name")
    client_secret_hash: Optional[str] = Field(None, description="Hashed client secret")
    allowed_providers: List[Literal["openai", "groq"]] = Field(..., description="List of allowed providers")
    default_provider: Literal["openai", "groq"] = Field(..., description="Default provider")
    default_model: str = Field(..., description="Default model")
    max_tokens_limit: int = Field(..., gt=0, description="Maximum tokens limit")
    rate_limit: RateLimit = Field(..., description="Rate limiting configuration")
    allowed_endpoints: List[str] = Field(..., description="List of allowed endpoints")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str = Field(..., description="Error details")
    status_code: int = Field(400, description="HTTP status code")

class ReloadResponse(BaseModel):
    """Schema for client reload response."""
    message: str = Field(..., description="Response message")
    count: int = Field(..., description="Number of clients reloaded")
