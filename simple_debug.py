"""
Simple debugging script for the DSP AI Gateway.

This script focuses on isolating the core issues with the model tests
by providing a step-by-step approach to debugging.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
print(f"Added {project_root} to Python path")

# Set test API keys in environment variables
os.environ['OPENAI_API_KEY'] = 'sk-test-key-for-openai'
os.environ['GROQ_API_KEY'] = 'gsk-test-key-for-groq'

# Step 1: Import settings and check API keys
print("\n=== Step 1: Import settings and check API keys ===")
try:
    from app.core.config import settings
    print(f"Settings imported successfully")
    print(f"OPENAI_API_KEY in settings: {settings.OPENAI_API_KEY[:5]}... (length: {len(settings.OPENAI_API_KEY)})")
    print(f"GROQ_API_KEY in settings: {settings.GROQ_API_KEY[:5]}... (length: {len(settings.GROQ_API_KEY)})")
except Exception as e:
    print(f"Error importing settings: {e}")
    import traceback
    traceback.print_exc()

# Step 2: Create a simple mock for OpenAI
print("\n=== Step 2: Create a simple mock for OpenAI ===")
try:
    from unittest.mock import patch, MagicMock
    
    # Create the mock
    mock_openai = MagicMock()
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    # Create a mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 30
    
    # Set up the mock client to return the mock response
    mock_client.chat.completions.create.return_value = mock_response
    
    print("Mock OpenAI client created successfully")
except Exception as e:
    print(f"Error creating mock: {e}")
    import traceback
    traceback.print_exc()

# Step 3: Try to create an OpenAI model with the mock
print("\n=== Step 3: Try to create an OpenAI model with the mock ===")
try:
    with patch("openai.OpenAI", mock_openai):
        from app.models.llm import OpenAIModel
        
        # Create the model
        model = OpenAIModel("gpt-4")
        print(f"OpenAI model created successfully: {model}")
        print(f"Model name: {model.model_name}")
except Exception as e:
    print(f"Error creating OpenAI model: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Try to generate text with the model
print("\n=== Step 4: Try to generate text with the model ===")
try:
    import asyncio
    
    with patch("openai.OpenAI", mock_openai):
        from app.models.llm import OpenAIModel
        
        # Create the model
        model = OpenAIModel("gpt-4")
        
        # Generate text
        response = asyncio.run(model.generate("Test prompt"))
        print(f"Generated text successfully: {response}")
except Exception as e:
    print(f"Error generating text: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Check if the mock was called correctly
print("\n=== Step 5: Check if the mock was called correctly ===")
try:
    if mock_client.chat.completions.create.called:
        print("Mock client was called correctly")
        call_args = mock_client.chat.completions.create.call_args
        print(f"Called with args: {call_args}")
    else:
        print("Mock client was not called")
except Exception as e:
    print(f"Error checking mock calls: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Debugging complete ===")
