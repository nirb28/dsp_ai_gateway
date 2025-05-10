{
curl "http://127.0.0.1:9180/apisix/admin/routes" -X PUT \
 -H "X-API-KEY: ${admin_key}" \
 -d '{
    "id": "jwt-route-basic",
    "uri": "/debug/*",
    "plugins": {
        
    },
    "upstream": {
        "type": "roundrobin",
        "nodes": {
        "192.168.1.25:5000": 1
    }
    }
}'  
}

# Check route
curl "http://127.0.0.1:9180/apisix/admin/routes/jwt-route-basic" -X GET -H "X-API-KEY: ${admin_key}"

# Execute route
curl "http://127.0.0.1:9080/debug/request-info"
