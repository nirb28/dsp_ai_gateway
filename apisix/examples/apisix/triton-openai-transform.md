# APISIX: OpenAI API to Triton Inference Server Transformer

## Create the Route

# Create the transformation route
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

            -- Debug log
            core.log.info(\"OpenAI request received, starting transformation\")
            
            -- Get and parse request body
            ngx.req.read_body()
            local body = ngx.req.get_body_data()
            if not body then
                return 400, {error = \"Missing request body\"}
            end
            
            local data = cjson.decode(body)
            if not data.messages then
                return 400, {error = \"Invalid request format: missing messages\"}
            end
            
            -- Extract prompts
            local system_prompt = \"\"
            local user_prompt = \"\"
            for _, msg in ipairs(data.messages) do
                if msg.role == \"system\" then
                    system_prompt = msg.content
                elseif msg.role == \"user\" then
                    user_prompt = msg.content
                end
            end
            
            -- Format Llama prompt
            local prompt = string.format(
                \"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\\n%s<|eot_id|>\\n<|start_header_id|>user<|end_header_id|>\\n%s<|eot_id|>\\n<|start_header_id|>assistant<|end_header_id|>\",
                system_prompt, user_prompt
            )
            
            -- Build Triton request
            local triton_request = {
                inputs = {
                    {
                        name = \"text_input\",
                        shape = {1},
                        datatype = \"BYTES\",
                        data = {prompt}
                    }
                },
                parameters = {
                    temperature = data.temperature or 0.7,
                    max_tokens = data.max_tokens or 100
                }
            }
            
            -- Modify request for Triton
            ngx.var.upstream_uri = \"/v2/models/Meta-Llama-3.1-8B-Instruct/generate\"
            ngx.req.set_header(\"Content-Type\", \"application/json\")
            ngx.req.set_body_data(cjson.encode(triton_request))
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
            core.log.info(\"Processing Triton response in body_filter phase\")
            
            -- In body_filter phase, response is in ngx.arg[1]
            local chunk = ngx.arg[1]
            
            -- Skip empty chunks or if not the last chunk
            if not chunk or chunk == \"\" or not ngx.arg[2] then
                return
            end
            
            -- Parse response
            local ok, triton_resp = pcall(cjson.decode, chunk)
            if not ok then
                core.log.error(\"Failed to decode Triton response: \", chunk)
                ngx.arg[1] = cjson.encode({error = \"Failed to decode model response\"})
                return
            end
            
            -- Check response format
            if not triton_resp.outputs or not triton_resp.outputs[1] or 
               not triton_resp.outputs[1].data or not triton_resp.outputs[1].data[1] then
                core.log.error(\"Invalid Triton response format\")
                ngx.arg[1] = cjson.encode({error = \"Invalid model response format\"})
                return
            end
            
            -- Extract the generated text
            local generated_text = triton_resp.outputs[1].data[1]
            core.log.info(\"Generated text: \", generated_text)
            
            -- Create OpenAI-style response
            local openai_resp = {
                id = \"chatcmpl-\" .. ngx.time(),
                object = \"chat.completion\",
                created = ngx.time(),
                model = \"llama-proxy\",
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
            core.log.info(\"Returning OpenAI-style response\")
            ngx.arg[1] = cjson.encode(openai_resp)
          end"
        ]
      }
    },
    "upstream": {
      "type": "roundrobin",
      "nodes": {
        "192.168.1.25:5001": 1
      }
    }
  }'

## Verify the route is properly created:
curl http://localhost:9180/apisix/admin/routes/openai_triton_proxy -H "X-API-KEY: ${admin_key}"

## Test the Route
curl -X POST http://localhost:9080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant"},
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "temperature": 0.7
  }'


