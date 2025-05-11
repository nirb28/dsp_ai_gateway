# Admin
# Add consumer / plugin-config / upstream
curl "http://127.0.0.1:9180/apisix/admin/consumers" -X PUT -H "X-API-KEY: ${admin_key}" -d '{
    "username": "cs_72344_examples_jwt1",
    "labels": {
      "custom_id": "72344_examples_jwt1-custom"
    },
    "plugins": {
      "limit-count": {
        "count": 2000,
        "time_window": 30,
        "rejected_code": 429
      },
      "jwt-auth": {
          "key": "user-key",
          "secret": "your-secret-key-here",
          "store_in_ctx": "true"
      },
      "proxy-rewrite": {
            "uri": "/$http_destURL",
            "host1":"$http_destHost"
      },
      "serverless-pre-function": {
          "phase": "rewrite",
          "functions" : ["return function(conf, ctx)
              -- Import neccessary libraries
              local core = require(\"apisix.core\")
              local jwt = require(\"resty.jwt\")

              -- Retrieve the JWT token from the Authorization header
              local jwt_token = core.request.header(ctx, \"Authorization\")
              if jwt_token ~= nil then
                  -- Remove the Bearer prefix from the JWT token
                  local _, _, jwt_token_only = string.find(jwt_token, \"Bearer%s+(.+)\")
                  if jwt_token_only ~= nil then
                    -- Decode the JWT token
                    local jwt_obj = jwt:load_jwt(jwt_token_only)
                    if jwt_obj.valid then
                      -- Retrieve the value of the speakerId claim from the JWT token
                      local speakerId_claim_value = jwt_obj.payload.speakerId
                      local destURL_claim_value = jwt_obj.payload.destURL
                      local destHost_claim_value = jwt_obj.payload.destHost
                      
                      ngx.log(ngx.WARN, \"** DS - serverless pre function\" .. destURL_claim_value);

                      -- Store the speakerId claim value in the header variable
                      core.request.set_header(ctx, \"speakerId\", speakerId_claim_value)
                      core.request.set_header(ctx, \"destURL\", destURL_claim_value)
                      core.request.set_header(ctx, \"destHost\", destHost_claim_value)
                    end
                  end
              end
            end
          "]}
    }
  }'

curl http://127.0.0.1:9180/apisix/admin/plugin_configs -H "X-API-KEY: $admin_key" -X PUT -i \
-d '
{
   "id":"pc_jwt",
   "desc": "JWT Auth Setup",
   "plugins":{
      "jwt-auth": {}
   }
}'

curl "http://127.0.0.1:9180/apisix/admin/upstreams" -X PUT -H "X-API-KEY: ${admin_key}" -d '
{
   "id": "up_dev_debug_http",
   "name":"Debug upstream",
   "desc":"Register Mock API as the upstream",
   "nodes":{
      "192.168.1.25:5000": 1
   }
}'

curl "http://127.0.0.1:9180/apisix/admin/routes" -X PUT -H "X-API-KEY: ${admin_key}" -d '{
    "id": "rt_jwt_route_basic",
    "uri": "/debug/*",
    "upstream_id":"up_dev_debug_http",
    "plugin_config_id":"pc_jwt"
}'

## Read route: 
curl "http://127.0.0.1:9180/apisix/admin/routes/rt_jwt_route_basic" -X GET -H "X-API-KEY: ${admin_key}" 

## Non Admin
## Execute route

# jwt: 
jwt_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJ1c2VyLWtleSIsImV4cCI6OTk5OTk5OTk5OSwic3BlYWtlcklkIjoxLCJkZXN0VVJMIjoiL2RlYnVnL3JlcXVlc3QtaW5mbyIsImRlc3RIb3N0IjoiMTkyLjE2OC4xLjI1OjUwMDAifQ.eKRGOt4NSIDhoO1C5REOuWaKmmhxxmvOsxJXTeqVnFM
curl "http://127.0.0.1:9080/debug/dest-read-from-jwt" -i -H "Authorization: Bearer ${jwt_token}"

