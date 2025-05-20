# APISIX: Multi-Model OpenAI to Triton Transformer

## Create the Route
curl http://localhost:9180/apisix/admin/routes/openai_triton_proxy \
  -H "X-API-KEY: ${admin_key}" \
  -H "Content-Type: application/json" \
  -X PUT \
  -d '{
    "uri": "/v1/chat/completions",
    "name": "openai-to-triton-route",
    "methods": ["POST"],
    "plugins": {
      "serverless-pre-function": {
        "phase": "rewrite",
        "functions": [
          "return function(conf, ctx)
            -- Import modules
            local core = require(\"apisix.core\")
            local cjson = require(\"cjson\")

            -- Debug logs
            core.log.info(\"==== [1] OpenAI request received ====\")
            
            -- Get and parse request body
            ngx.req.read_body()
            local body = ngx.req.get_body_data()
            if not body then
                core.log.error(\"[1.1] No request body found\")
                return 400, {error = \"Missing request body\"}
            end
            
            local ok, data = pcall(cjson.decode, body)
            if not ok or not data then
                core.log.error(\"[1.2] Failed to parse JSON request: \", body)
                return 400, {error = \"Invalid JSON in request body\"}
            end
            
            core.log.info(\"[1.3] OpenAI request: \", cjson.encode(data))
            
            -- Basic validation
            if not data.messages then
                core.log.error(\"[1.4] Messages field missing in request\")
                return 400, {error = \"Invalid request format: missing messages\"}
            end
            
            -- Extract prompts
            core.log.info(\"==== [2] Extracting prompt content ====\")
            local system_prompt = \"\"
            local user_prompt = \"\"
            for i, msg in ipairs(data.messages) do
                core.log.info(\"[2.1] Message \", i, \": role=\", msg.role)
                if msg.role == \"system\" then
                    system_prompt = msg.content
                    core.log.info(\"[2.2] System prompt: \", system_prompt)
                elseif msg.role == \"user\" then
                    user_prompt = msg.content
                    core.log.info(\"[2.3] User prompt: \", user_prompt)
                end
            end
            
            -- Format Llama prompt
            core.log.info(\"==== [3] Formatting for LLama ====\")
            local prompt = string.format(
                \"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\\n%s<|eot_id|>\\n<|start_header_id|>user<|end_header_id|>\\n%s<|eot_id|>\\n<|start_header_id|>assistant<|end_header_id|>\",
                system_prompt, user_prompt
            )
            
            -- Model selection logic
            core.log.info(\"==== [4] Model selection ====\")
            local model_name = \"Meta-Llama-3.1-8B-Instruct\"  -- Default model
            
            -- Set upstream based on model selection
            local use_70b = false
            
            -- Check for model parameter in the request
            if data.model then
                -- Direct model selection based on model name
                if data.model == \"llama-3-70b\" or data.model:find(\"70[Bb]\") then
                    model_name = \"Meta-Llama-3.1-70B-Instruct\"
                    use_70b = true
                    core.log.info(\"[4.1] Selected 70B Llama model with 70B server\")
                elseif data.model == \"llama-3-8b\" or data.model:find(\"8[Bb]\") then
                    model_name = \"Meta-Llama-3.1-8B-Instruct\"
                    use_70b = false
                    core.log.info(\"[4.2] Selected 8B Llama model with 8B server\")
                else
                    -- Keep default if model name is not recognized
                    core.log.info(\"[4.3] Using default 8B model (unrecognized model name)\")
                end
            end
            
            -- Set a query parameter to be used for upstream selection
            -- We'll modify the current query string to add our parameter
            local args = ngx.req.get_uri_args()
            args["use_70b"] = tostring(use_70b)
            ngx.req.set_uri_args(args)
            core.log.info("[4.4] Set use_70b query parameter to: " .. tostring(use_70b))
            
            -- Build Triton request using simplified format
            core.log.info(\"==== [5] Building Triton request ====\")
            local triton_request = {
                text_input = prompt,
                parameters = {
                    stream = false,
                    temperature = data.temperature or 0.7,
                    top_p = data.top_p or 0.95,
                    max_tokens = data.max_tokens or 100
                }
            }
            
            core.log.info(\"[5.1] Triton request: \", cjson.encode(triton_request))
            
            -- Modify request for Triton
            core.log.info(\"==== [6] Setting upstream and headers ====\")
            local target_uri = \"/v2/models/\" .. model_name .. \"/generate\"
            ngx.var.upstream_uri = target_uri
            core.log.info(\"[6.1] Set upstream URI: \", target_uri)
            
            ngx.req.set_header(\"Content-Type\", \"application/json\")
            core.log.info(\"[6.2] Set Content-Type header\")
            
            local req_body = cjson.encode(triton_request)
            ngx.req.set_body_data(req_body)
            core.log.info(\"[6.3] Request body set, length: \", #req_body)
            core.log.info(\"==== [7] Request transformation complete ====\")
          end"
        ]
      },
      "serverless-post-function": {
        "phase": "body_filter",
        "functions": [
          "return function(conf, ctx)
            -- Import modules
            local core = require(\"apisix.core\")
            local cjson = require(\"cjson\")
            
            -- Log entering body filter phase
            core.log.info(\"==== [1] Processing Triton response ====\")
            
            -- In body_filter phase, response is in ngx.arg[1]
            local chunk = ngx.arg[1]
            local is_last = ngx.arg[2]
            
            -- Get the context table to store our buffered data between calls
            ctx.response_buffer = ctx.response_buffer or \"\"
            
            -- Debug the current state
            core.log.info(\"[1.1] Body filter received: chunk_length=\" .. (chunk and #chunk or 0) .. \", is_last=\" .. tostring(is_last))
            
            if chunk and #chunk > 0 then
                -- Append this chunk to our buffer
                ctx.response_buffer = ctx.response_buffer .. chunk
                core.log.info(\"[1.2] Added chunk to buffer, new buffer length: \" .. #ctx.response_buffer)
            end
            
            -- Only continue processing if this is the last chunk
            if not is_last then
                core.log.info(\"[1.3] Not the last chunk, waiting for more\")
                ngx.arg[1] = nil  -- Remove this chunk from the response
                return
            end
            
            -- We have the complete response, now process it
            core.log.info(\"[1.4] Processing complete response, buffer length: \" .. #ctx.response_buffer)
            
            -- Parse response
            core.log.info(\"==== [2] Parsing Triton response ====\")
            local ok, triton_resp = pcall(cjson.decode, ctx.response_buffer)
            if not ok then
                core.log.error(\"[2.1] Failed to decode response: \" .. ctx.response_buffer:sub(1, 100) .. \"...\")
                ngx.arg[1] = cjson.encode({error = \"Failed to decode model response\"})
                return
            end
            
            core.log.info(\"[2.2] Response decoded successfully\")
            
            -- Extract generated text - using the simplified format
            core.log.info(\"==== [3] Extracting generated text ====\")
            local generated_text = nil
            
            -- Try different response formats
            local raw_text = nil
            if triton_resp.text_output then
                core.log.info(\"[3.1] Found text_output field\")
                raw_text = triton_resp.text_output
            elseif triton_resp.response then
                core.log.info(\"[3.2] Found response field\")
                raw_text = triton_resp.response
            elseif triton_resp.output then
                core.log.info(\"[3.3] Found output field\")
                raw_text = triton_resp.output
            -- Fall back to standard Triton format
            elseif triton_resp.outputs and triton_resp.outputs[1] and 
                  triton_resp.outputs[1].data and triton_resp.outputs[1].data[1] then
                core.log.info(\"[3.4] Found standard Triton format\")
                raw_text = triton_resp.outputs[1].data[1]
            end
            
            -- Extract only the assistants response
            core.log.info(\"[3.5] Extracting assistants response from raw text\")
            core.log.info(\"[3.6] Raw text: \" .. (raw_text and raw_text:sub(1, 100) or \"nil\") .. \"...\")
            
            if raw_text then
                -- Find the assistants part
                local assistant_marker = \"<|start_header_id|>assistant<|end_header_id|>\"
                local _, assistant_start = string.find(raw_text, assistant_marker)
                
                if assistant_start then
                    -- Extract everything after the assistant marker
                    generated_text = string.sub(raw_text, assistant_start + 1)
                    core.log.info(\"[3.7] Extracted assistant response: \" .. generated_text:sub(1, 50) .. \"...\")
                else
                    -- Fallback if marker not found
                    core.log.warn(\"[3.8] Assistant marker not found, using full text\")
                    generated_text = raw_text
                end
            end
            
            if not generated_text then
                core.log.error(\"[3.5] Could not find text in response: \", cjson.encode(triton_resp))
                ngx.arg[1] = cjson.encode({error = \"Invalid model response format\"})
                return
            end
            
            core.log.info(\"[3.6] Extracted text: \", generated_text:sub(1, 50), \"...\")
            
            -- Determine model name (extract from request URI)
            local model_name = \"llama-proxy\"
            local uri = ngx.var.upstream_uri
            if uri then
                local pattern = \"/v2/models/([^/]+)/generate\"
                local match = string.match(uri, pattern)
                if match then
                    model_name = match
                    core.log.info(\"[3.7] Extracted model name from URI: \", model_name)
                end
            end
            
            -- Create OpenAI-style response
            core.log.info(\"==== [4] Building OpenAI response ====\")
            local openai_resp = {
                id = \"chatcmpl-\" .. ngx.time(),
                object = \"chat.completion\",
                created = ngx.time(),
                model = model_name,
                choices = {
                    {
                        index = 0,
                        message = {
                            role = \"assistant\",
                            content = generated_text
                        },
                        finish_reason = \"stop\"
                    }
                },
                usage = {
                    prompt_tokens = 0,
                    completion_tokens = 0,
                    total_tokens = 0
                }
            }
            
            -- Return transformed response
            core.log.info(\"[4.1] OpenAI response built successfully\")
            local resp_json = cjson.encode(openai_resp)
            ngx.arg[1] = resp_json
            core.log.info(\"[4.2] Response transformation complete, length: \", #resp_json)
          end"
        ]
      }
    },
    "upstream": {
      "type": "chash",
      "key": "arg_use_70b",
      "nodes": {
        "192.168.1.25:5001": 1,
        "192.168.1.26:5001": 1
      }
    }
  }'


## Test the Route with Different Models

### Test with 8B Model (Default)
curl -X POST http://localhost:9080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant"},
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "temperature": 0.7
  }'

### Test with 70B Model
curl -X POST http://localhost:9080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3-70b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant"},
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "temperature": 0.7
  }'

### Directly Test the Mock Service

Using multi-model selection, you can verify that both models work correctly with the mock service:

```bash
# Test the 8B model
curl -X POST http://192.168.1.25:5001/v2/models/Meta-Llama-3.1-8B-Instruct/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text_input": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\nYou are a helpful assistant<|eot_id|>\n<|start_header_id|>user<|end_header_id|>\nWhat is the capital of France?<|eot_id|>\n<|start_header_id|>assistant<|end_header_id|>",
    "parameters": {
      "stream": false,
      "temperature": 0.7,
      "top_p": 0.95,
      "max_tokens": 100
    }
  }'

# Test the 70B model
curl -X POST http://192.168.1.25:5001/v2/models/Meta-Llama-3.1-70B-Instruct/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text_input": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\nYou are a helpful assistant<|eot_id|>\n<|start_header_id|>user<|end_header_id|>\nWhat is the capital of France?<|eot_id|>\n<|start_header_id|>assistant<|end_header_id|>",
    "parameters": {
      "stream": false,
      "temperature": 0.7,
      "top_p": 0.95,
      "max_tokens": 100
    }
  }'
```
