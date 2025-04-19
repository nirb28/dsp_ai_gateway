docker compose up

curl -i -X GET   http://localhost:9080/get   -H "apikey: dspai-key"

curl -i -X GET   http://localhost:9080/hello

curl -i "http://127.0.0.1:9080/get" -H "X-APISIX-Dynamic-Debug: 1" -H "apikey: consumer1-key"

curl "http://127.0.0.1:9080/v1/chat/completions" -X POST -H "X-APISIX-Dynamic-Debug: 1"  -H "Content-Type: application/json"   -H "Host: api.openai.com:443"   -d '{
    "model": "gpt-3.5-turbo",
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

