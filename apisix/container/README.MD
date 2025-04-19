curl "http://127.0.0.1:9180/apisix/admin/services/" -H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1'

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

