# OpenAI to Triton Server Transformation

## Overview
# This configuration creates an API Gateway route that transforms OpenAI API calls to a Triton Inference Server running LLama models. It performs bidirectional conversion.

## Route Configuration

```bash

curl http://localhost:9180/apisix/admin/routes \
  -H "X-API-KEY: ${admin_key}" \
  -H "Content-Type: application/json" \
  -X PUT \
  -d '{
    "id": "rt_openai_xform",
    "uri": "/v1/chat/completions",
    "name": "openai-to-triton-route",
    "methods": ["POST"],
    "plugins": {
      "serverless-pre-function": {
        "phase": "rewrite",
        "functions": [
          "return function(conf, ctx) 
            local core = require(\"apisix.core\")
            local json = require(\"toolkit.json\")
            
            -- Read OpenAI request body
            local body = core.request.get_body()
            local data = json.decode(body)
            
            -- Format prompt for Llama 3
            local messages = data.messages
            local system_prompt = \"\"
            local user_prompt = \"\"
            for _, msg in ipairs(messages) do
              if msg.role == \"system\" then
                system_prompt = msg.content
              elseif msg.role == \"user\" then
                user_prompt = msg.content
              end
            end
            
            local formatted_prompt = string.format(
              \"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\\n%s<|eot_id|>\\n<|start_header_id|>user<|end_header_id|>\\n%s<|eot_id|>\\n<|start_header_id|>assistant<|end_header_id|>\",
              system_prompt, user_prompt
            )
            
            -- Build Triton request
            local triton_request = {
              inputs = {{
                name = \"text_input\",
                shape = {1},
                datatype = \"BYTES\",
                data = {formatted_prompt}
              }},
              parameters = {
                temperature = data.temperature or 0.7,
                max_tokens = data.max_tokens or 100
              }
            }
            
            -- Rewrite request for Triton
            core.request.set_uri(\"/v2/models/Meta-Llama-3.1-8B-Instruct/generate\")
            core.request.set_header(\"Content-Type\", \"application/json\")
            core.request.set_body(json.encode(triton_request))
          end"
        ]
      },
      "serverless-post-function": {
        "phase": "body_filter",
        "functions": [
          "return function(conf, ctx) 
            local core = require(\"apisix.core\")
            local json = require(\"toolkit.json\")
            
            -- Read Triton response
            local body = core.response.get_body()
            local data = json.decode(body)
            
            -- Extract generated text
            local generated_text = data.outputs[1].data[1]
            
            -- Build OpenAI-style response
            local openai_response = {
              choices = {{
                message = {
                  role = \"assistant\",
                  content = generated_text
                }
              }}
            }
            
            core.response.set_body(json.encode(openai_response))
          end"
        ]
      }
    },
    "upstream": {
      "type": "roundrobin",
      "nodes": {
        "triton-server:8000": 1
      }
    }
  }'
```

## Test the Endpoint

```bash
# Check if the route was created successfully
curl http://localhost:9180/apisix/admin/routes/rt_openai_xform -H "X-API-KEY: ${admin_key}"

# Send a test request
curl -X POST http://localhost:9080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant"},
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "temperature": 0.7
  }'
```
