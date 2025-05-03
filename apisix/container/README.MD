docker stop $(docker ps -a -q); docker compose up -d

export admin_key=<admin>
export OPENAI_API_KEY=<key>

# ADMIN
curl "http://127.0.0.1:9180/apisix/admin/services/" -H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1'

curl "http://127.0.0.1:9180/apisix/admin/plugins/list" -X GET   -H "X-API-KEY: ${admin_key}"


# Simple Example

curl -i "http://127.0.0.1:9180/apisix/admin/routes" -H "X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" -X PUT -d '
{
  "id": "getting-started-ip",
  "uri": "/ip",
  "upstream": {
    "type": "roundrobin",
    "nodes": {
      "httpbin.org:80": 1
    }
  }
}'

curl -i -X GET "http://localhost:9080/ip"

curl "http://127.0.0.1:9180/apisix/admin/upstreams/3" -H "X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" -X PUT -d '
{
  "type": "roundrobin",
  "nodes": {
    "httpbin.org:80": 1
  }
}'

curl -i "http://127.0.0.1:9180/apisix/admin/routes" -H "X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" -X PUT -d '
{
  "id": "getting-started-ip",
  "uri": "/ip",
  "upstream_id": "3"
}'

# Load Balancer

curl -i "http://127.0.0.1:9180/apisix/admin/routes" -H "X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" -X PUT -d '
{
  "id": "getting-started-headers",
  "uri": "/headers",
  "upstream" : {
    "type": "roundrobin",
    "nodes": {
      "httpbin.org:443": 1,
      "mock.api7.ai:443": 1
    },
    "pass_host": "node",
    "scheme": "https"
  }
}'

hc=$(seq 100 | xargs -I {} curl "http://127.0.0.1:9080/headers" -sL | grep "httpbin" | wc -l); echo httpbin.org: $hc, mock.api7.ai: $((100 - $hc))

# Add consumer with key-auth

curl -i "http://127.0.0.1:9180/apisix/admin/consumers" -H "X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" -X PUT -d '
{
  "username": "tom",
  "plugins": {
    "key-auth": {
      "key": "secret-key"
    }
  }
}'

curl -i "http://127.0.0.1:9180/apisix/admin/routes/getting-started-ip" -H "X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" -X PATCH -d '
{
  "plugins": {
    "key-auth": {}
  }
}'

# Pipeline

curl -X PUT 'http://127.0.0.1:9180/apisix/admin/routes/5' \
--header 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1' \
--header 'Content-Type: application/json' \
--data-raw '{
   "uri":"/my-credit-cards",
   "plugins":{
      "pipeline-request":{
         "nodes":[
            {
               "url":"https://random-data-api.com/api/v2/credit_cards"
            },
            {
               "url":"http://127.0.0.1:9080/filter"
            }
         ]
      }
   }
}'

# Open AI 

curl "http://127.0.0.1:9180/apisix/admin/routes" -X PUT   -H "X-API-KEY: ${admin_key}"   -d '{
    "id": "ai-proxy-route",
    "uri": "/openai",
    "methods": ["POST"],
    "plugins": {
      "ai-proxy": {
        "provider": "openai",
        "auth": {
          "header": {
            "Authorization": "Bearer '"$OPENAI_API_KEY"'"
          }
        },
        "options":{
          "model": "gpt-3.5-turbo"
        }
      }
    }
  }'

curl "http://127.0.0.1:9080/openai" -X POST \
  -H "Content-Type: application/json" \
  -H "Host: api.openai.com:443" \
  -d '{
    "messages": [
      {
        "role": "system",
        "content": "You are a computer scientist."
      },
      {
        "role": "user",
        "content": "Explain in one sentence what a Turing machine is."
      }
    ]
  }'

# Grok 3

curl https://api.x.ai/v1/chat/completions 
  -H "Content-Type: application/json" 
  -H "Authorization: Bearer '"$GROK3_API_KEY"'"
  -d '{
  "messages": [
    {
      "role": "system",
      "content": "You are a test assistant."
    },
    {
      "role": "user",
      "content": "Testing. Just say hi and hello world and nothing else."
    }
  ],
  "model": "grok-3-latest",
  "stream": false,
  "temperature": 0
}'

# Alibaba

curl "http://127.0.0.1:9180/apisix/admin/routes" -X PUT -H "X-API-KEY: ${admin_key}" -d '{
    "id": "ai-proxy-alibaba-route",  
    "uri": "/alibaba",
    "plugins": {
      "ai-proxy": {
        "provider": "openai-compatible",        
        "auth": {
          "header": {
            "Authorization": "Bearer sk-b263337dfa574304bf5981468e83b373"
          }
        },
        "options":{
          "model": "qwen-plus"
        },
        "override": {
          "endpoint": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
        }
      }
    },
    "upstream": {
      "type": "roundrobin",
      "nodes": {
        "somerandom.com:443": 1
      },
      "scheme": "https",
      "pass_host": "node"
    }
  }'

curl "http://127.0.0.1:9080/alibaba" -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "system",
        "content": "You are a computer scientist."
      },
      {
        "role": "user",
        "content": "Explain in one sentence what a Turing machine is."
      }
    ]
  }'


# JWT Auth

curl http://127.0.0.1:9180/apisix/admin/services/ct-dev -H "X-API-KEY: $admin_key" -X PUT -d '
{
    "plugins": {
        "limit-count": {
            "count": 2,
            "time_window": 60,
            "rejected_code": 503,
            "key": "remote_addr"
        }
    },
    "upstream": {
        "type": "roundrobin",
        "nodes": {
          "192.168.1.25:8000": 1
        }
    }
}'

curl http://127.0.0.1:9180/apisix/admin/routes/rt-ct-dev \
-H "X-API-KEY: $admin_key" -X PUT -d '
{
    "methods": ["GET"],
    "uri": "/ct",
    "service_id": "ct-dev"
}'

curl -i -X GET "http://localhost:9080/ct"
