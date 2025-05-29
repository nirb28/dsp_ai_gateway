# DSP AI System - Technical Specification

## System Overview

The Data Science Platform (DSP) AI system provides enterprise-grade infrastructure for secure, scalable, and configurable access to large language models (LLMs). The system enables organization-wide AI capabilities while enforcing robust security, governance, and access controls through a modular architecture.

## System Architecture

The DSP AI system consists of the following key components that work together to provide a comprehensive AI access and governance solution:

### 1. DSP AI Gateway

**Core Functionality**: API Gateway for securely accessing large language models.

**Key Requirements**:
- Client authentication using client IDs and secrets
- Client-specific configuration management stored in JSON files
- Support for multiple LLM providers (OpenAI, Groq, with future extension to additional providers)
- Endpoint access control to restrict which endpoints clients can access
- Provider access control to restrict which LLM providers clients can use
- Rate limiting for requests and tokens per client
- Local virtual environment for deployment isolation

**Technical Implementation**:
- FastAPI and Uvicorn for high-performance API service
- Configuration management through structured JSON files
- Comprehensive test suite for reliability verification

### 2. DSP AI JWT Token Service

**Core Functionality**: Authentication and authorization service for generating JWT tokens.

**Key Requirements**:
- Multiple authentication methods (LDAP/Active Directory and file-based)
- Configurable JWT token generation with appropriate signing keys
- Individual API key configuration with separate configuration files
- Dynamic claim generation via function calls and API calls
- Token decoding and verification mechanisms

**Technical Implementation**:
- Flask-based microservice architecture
- YAML configuration for service settings
- Direct integration with API gateway JWT-Auth plugin

### 3. DSP AI Control Tower

**Core Functionality**: Policy evaluation engine for governance and compliance.

**Key Requirements**:
- Policy evaluation using Open Policy Agent (OPA)
- Client-specific policy files for granular control
- Batch evaluation support for multiple authorization requests
- Fine-grained permission system for detailed access management
- Integration with enterprise security systems (SSO and IAM)

**Technical Implementation**:
- Rego policy language for defining authorization rules
- RESTful API for policy evaluation requests
- JSON-based request and response format

### 4. API Integration Layer

**Core Functionality**: Request/response transformation and routing.

**Key Requirements**:
- Request transformation between different model API formats
- Response transformation to standardize outputs
- Model server selection based on request parameters
- Detailed logging for debugging and troubleshooting
- Advanced caching for common requests to improve performance

**Technical Implementation**:
- Lua-based serverless functions for pre/post-processing
- Configurable transformation rules
- Consistent hashing for server selection
- Header-based model routing

### 5. LangChain Integration

**Core Functionality**: Advanced LLM workflows and use cases.

**Key Requirements**:
- Chained prompts for complex workflows
- Document retrieval integration for context augmentation
- Memory systems for conversation context
- Tool integration for LLMs with external services
- Comprehensive observability and metrics for model performance

**Technical Implementation**:
- Python-based integration with LangChain framework
- Customizable prompt templates
- Vector database integration for retrieval

### 6. Serverless Deployment (Apache OpenWhisk)

**Core Functionality**: Scalable, on-demand model deployment.

**Key Requirements**:
- Serverless model deployment with on-demand scaling
- Event-driven processing for model execution
- Resource optimization based on demand
- Cold start optimization for LLM inference
- Multi-runtime support (Python, Node.js)
- Edge deployment support for distributed model serving

**Technical Implementation**:
- Container-based deployment as Whisk actions
- Integration with existing authentication mechanisms
- Custom runtime for optimized LLM serving

## Integration Points

The system components integrate at the following key points:

1. **Client Authentication Flow**:
   - Client applications request JWT tokens from DSP AI JWT
   - Tokens are used with the API gateway to access DSP AI Gateway
   - DSP AI Gateway validates client configuration and processes requests

2. **Policy Enforcement Flow**:
   - DSP AI Control Tower evaluates policies before allowing model access
   - JWT tokens contain claims that influence policy decisions
   - Client configurations specify allowed providers and endpoints

3. **Model Request Processing Flow**:
   - API gateway transforms client requests to appropriate model format
   - Requests are routed to the correct model server
   - Responses are transformed back to client-expected format

## Security Considerations

- JWT tokens with appropriate expiration configuration
- Secure storage of API keys in individual configuration files
- Enterprise authentication through LDAP integration
- Secure handling of client secrets

## Deployment Considerations

- Stateless component design for horizontal scaling
- Load balancing through API gateway
- Independent scaling of separate components
- Comprehensive logging and monitoring throughout the system
- Structured logs for aggregation and analysis

---

*Last updated: May 29, 2025*
