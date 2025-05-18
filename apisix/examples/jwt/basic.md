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
          "key": "ak_tiered_model_exec",
          "secret": "your-secret-key-here",
          "store_in_ctx": "true"
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
                      -- Retrieve the value of the user name and category claim from the JWT token
                      local name_claim_value = jwt_obj.payload.name                      
                      ngx.log(ngx.WARN, \"** DS - serverless pre function\" .. name_claim_value);
                      
                      -- Store the speakerId claim value in the header variable
                      core.request.set_header(ctx, \"name\", name_claim_value)
                      core.request.set_header(ctx, \"usercategory\", jwt_obj.payload.user_category.category.name)
                      core.request.set_header(ctx, \"destURL\", jwt_obj.payload.user_category.category.destURL)
                    end
                  end
              end
            end
          "]
      },
      "proxy-rewrite": {
        "use_real_request_uri_unsafe": true,
        "uri": "/debug/request-info?user_category=$http_usercategory",
        "host1":"$http_destHost"
      }
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
jwt_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6dHJ1ZSwiaWF0IjoxNzQ3NDMxMjU1LCJqdGkiOiIyMTRmNzZhNS0zMTI5LTQ3NDMtYTEzOC1hNWU3OTM4MGM1ZmYiLCJ0eXBlIjoiYWNjZXNzIiwic3ViIjoicHMiLCJuYmYiOjE3NDc0MzEyNTUsImV4cCI6MTc0NzUxNzY1NSwibmFtZSI6IlJlZ3VsYXIgVXNlciIsImVtYWlsIjoidXNlcjFAZXhhbXBsZS5jb20iLCJncm91cHMiOlsidXNlcnMiLCJncnBfdGllcjIiXSwicm9sZXMiOlsidXNlciJdLCJrZXkiOiJha190aWVyZWRfbW9kZWxfZXhlYyIsIm1vZGVscyI6WyJncHQtMy41LXR1cmJvIiwiZ3B0LTQiXSwicmF0ZV9saW1pdCI6MjAwLCJ0aWVyIjoiZW50ZXJwcmlzZSIsInRlYW1fcGVybWlzc2lvbnMiOnsiY2FuX21hbmFnZV91c2VycyI6ZmFsc2UsImNhbl9jcmVhdGVfYXBpX2tleXMiOmZhbHNlLCJjYW5fdmlld19iaWxsaW5nIjpmYWxzZSwibWF4X21vZGVsc19wZXJfcmVxdWVzdCI6MX0sInVzZXJfY2F0ZWdvcnkiOnsiY2F0ZWdvcnkiOnsibmFtZSI6InNpbHZlciIsImdyb3VwcyI6WyJncnBfdGllcjIiLCJjb250cmlidXRvcnMiXSwidGllciI6MiwiZGVzdFVSTCI6ImRlYnVnL3JlcXVlc3QtaW5mbz91c2VyX2NhdGVnb3J5PXNpbHZlciJ9LCJtYXRjaF9tb2RlIjoiVElFUkVEX01BVENIIn19.KX2KeKuwmbEmpwecZQsidUWPZpem4sIKicRBHj8Adlw

curl "http://127.0.0.1:9080/debug/request-info" -i -H "Authorization: Bearer ${jwt_token}"

