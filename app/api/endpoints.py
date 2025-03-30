from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from app.schemas.base import GenerateRequest, GenerateResponse, ClientConfig, ReloadResponse
from app.clients.auth import get_client_auth, check_endpoint_access, client_manager
from app.models.llm import get_model

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate_text(
    request: GenerateRequest,
    client_config: ClientConfig = Depends(get_client_auth),
    _: None = Depends(lambda client_config=None: check_endpoint_access("generate", client_config)),
) -> Dict[str, Any]:
    """Generate text using the specified model and provider.
    
    Args:
        request: Text generation request
        client_config: Client configuration
    
    Returns:
        Dict[str, Any]: Generated text and metadata
    
    Raises:
        HTTPException: If request is invalid or generation fails
    """
    # Check max tokens limit
    if request.max_tokens > client_config.max_tokens_limit:
        raise HTTPException(
            status_code=400, 
            detail=f"Max tokens limit exceeded. Maximum allowed: {client_config.max_tokens_limit}"
        )
    
    # Use client default provider if not specified
    provider = request.provider or client_config.default_provider
    
    # Check provider permission
    if provider not in client_config.allowed_providers:
        raise HTTPException(
            status_code=403, 
            detail=f"Client does not have permission to use provider: {provider}"
        )
    
    # Use client default model if not specified
    model_name = request.model or client_config.default_model
    
    try:
        # Get model instance
        model = get_model(provider, model_name)
        
        # Generate text
        response = await model.generate(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")

@router.get("/clients/reload", response_model=ReloadResponse)
async def reload_clients(
    client_config: ClientConfig = Depends(get_client_auth),
    _: None = Depends(lambda client_config=None: check_endpoint_access("clients/reload", client_config)),
) -> Dict[str, Any]:
    """Reload client configurations.
    
    Args:
        client_config: Client configuration
    
    Returns:
        Dict[str, Any]: Reload response
    """
    count = client_manager.reload_clients()
    return {
        "message": f"Successfully reloaded {count} client configurations",
        "count": count
    }
