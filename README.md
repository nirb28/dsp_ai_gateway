# DSP AI Gateway

An API Gateway for accessing large language models (LLMs) with client authentication and configuration management using FastAPI and Uvicorn.

## Features

- **Client Authentication**: Secure access through client IDs and secrets
- **Client-Specific Configurations**: Each client has their own configuration stored in JSON files
- **Multiple LLM Providers**: Support for OpenAI and Groq
- **Endpoint Access Control**: Control which endpoints each client can access
- **Provider Access Control**: Control which LLM providers each client can use
- **Rate Limiting**: Configure request and token limits per client
- **Embedded Virtual Environment**: All scripts use a local virtual environment

## Project Structure

```
dsp_ai_gateway/
├── app/
│   ├── api/
│   │   └── endpoints.py      # API endpoints
│   ├── clients/
│   │   ├── auth.py           # Client authentication
│   │   └── configs/          # Client configuration files
│   │       ├── test_client.json
│   │       ├── openai_only_client.json
│   │       └── groq_only_client.json
│   ├── core/
│   │   └── config.py         # Application configuration
│   ├── models/
│   │   └── llm.py            # LLM provider implementations
│   ├── schemas/
│   │   └── base.py           # Request and response schemas
│   └── main.py               # Main application entry point
├── tests/
│   ├── test_api.py           # API endpoint tests
│   ├── test_client_auth.py   # Client authentication tests
│   ├── test_config.py        # Configuration tests
│   ├── test_integration.py   # Integration tests
│   └── test_models.py        # LLM model tests
├── requirements.txt          # Project dependencies
├── setup_venv.ps1            # PowerShell script to set up virtual environment
├── setup_venv.bat            # Batch script to set up virtual environment
├── run_api.ps1               # PowerShell script to run the API
├── run_api.bat               # Batch script to run the API
├── run_tests.ps1             # PowerShell script to run tests
├── run_tests.bat             # Batch script to run tests
└── README.md                 # This file
```

## Setup

### Prerequisites

- Python 3.8 or higher
- API keys for OpenAI and/or Groq

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/dsp_ai_gateway.git
   cd dsp_ai_gateway
   ```

2. Set up the embedded virtual environment:
   ```
   # Using PowerShell
   .\setup_venv.ps1

   # Using Command Prompt
   setup_venv.bat
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GROQ_API_KEY=your_groq_api_key
   DEFAULT_PROVIDER=groq
   DEFAULT_MODEL=mixtral-8x7b-32768
   ```

## Running the API

Run the API using the provided scripts:

```
# Using PowerShell
.\run_api.ps1

# Using Command Prompt
run_api.bat
```

The API will be available at http://localhost:8000.

## API Documentation

Once the API is running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Client Configuration

Client configurations are stored in JSON files in the `app/clients/configs` directory. Each client has the following attributes:

```json
{
    "client_id": "test_client",
    "name": "Test Client",
    "allowed_providers": ["openai", "groq"],
    "default_provider": "groq",
    "default_model": "mixtral-8x7b-32768",
    "max_tokens_limit": 2000,
    "rate_limit": {
        "requests_per_minute": 60,
        "tokens_per_day": 100000
    },
    "allowed_endpoints": ["generate", "clients/reload"],
    "created_at": "2025-03-16T20:00:00-04:00",
    "updated_at": "2025-03-16T20:00:00-04:00"
}
```

## Client Authentication

Clients are authenticated using a client ID and secret in the request headers:

```
client_id: test_client
client_secret: password
```

In a production environment, client secrets should be stored securely in a database rather than in code.

## Running Tests

Run the tests using the provided scripts:

```
# Using PowerShell
.\run_tests.ps1

# Using Command Prompt
run_tests.bat
```

## API Endpoints

### Generate Text

```
POST /api/v1/generate
```

Request body:
```json
{
    "prompt": "Hello, world!",
    "temperature": 0.7,
    "max_tokens": 150,
    "provider": "groq",
    "model": "mixtral-8x7b-32768"
}
```

Response:
```json
{
    "text": "Hello there! How can I assist you today?",
    "model": "mixtral-8x7b-32768",
    "usage": {
        "prompt_tokens": 3,
        "completion_tokens": 9,
        "total_tokens": 12
    }
}
```

### Reload Client Configurations

```
GET /api/v1/clients/reload
```

Response:
```json
{
    "message": "Successfully reloaded 3 client configurations",
    "count": 3
}
```

## Security Considerations

- In a production environment, client secrets should be stored in a secure database.
- API keys should be stored securely and not committed to version control.
- Consider implementing additional security measures such as rate limiting and IP filtering.

## License

[MIT License](LICENSE)
