docker compose up

curl -i -X GET   http://localhost:9080/get   -H "apikey: dspai-key"

curl -i -X GET   http://localhost:9080/hello

curl -i "http://127.0.0.1:9080/get" -H "X-APISIX-Dynamic-Debug: 1" -H "apikey: consumer1-key"