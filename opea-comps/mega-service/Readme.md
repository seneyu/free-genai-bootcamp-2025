## How to Run the LLM Service

We are using Ollama which is being delivered via docker compose.

We can set the port that the LLM will listening on.
`9000` is ideal when looking at many existing OPEA mega-service default ports.
This will default to 8008 if not set.

```sh
LLM_ENDPOINT_PORT=9000 docker compose up
```

### Download (Pull) a Model

Download (pull) the model via the API for Ollama:

```bash
curl http://localhost:9000/api/pull -d '{
    "model": "llama3.2:1b"
}'
```

## How to access the Jaeger UI

When you run docker compose, it should start up Jaeger.

```sh
http://localhost:16686/
```

## How to Run the Mega Service Example

```sh
python app.py
```

## Testing the App

Install Jq so we can print pretty JSON on output.
https://jqlang.org/download/

```sh
# for Linux system
sudo apt-get install jq

# for macOS
brew install jq
```

cd opea-comps/mega-service

```sh
curl -X POST http://localhost:8000/v1/example-service \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": "Hello, how are you?"
  }' | jq '.' > output/$(date +%s)-response.json
```

```sh
curl -X POST http://localhost:8000/v1/example-service \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Hello, this is a test message"
      }
    ],
    "model": "llama3.2:1b",
    "max_tokens": 100,
    "temperature": 0.7
  }' | jq '.' > output/$(date +%s)-response.json
```

## Journal

There was not enough documentation on OPEA so we had to check their code back and forth to connect the pieces. We added a lot of console logs in `app.py` and used curl commands to test the LLM eg. `./bin/message` and `./bin/ollama-test`.

We finally figured out the correct prompt for Ollama.

Example: `./bin/ollama-test`

```sh
curl http://localhost:9000/api/chat -d '{
    "model": "llama3.2:1b",
    "messages": [
    {
        "role": "user",
        "content": "why is the sky not red?"
    }
    ],
    "stream": false
  }'
```

Start the container with docker compose up, pull the model, run `python app.py`, and in anotoher terminal run `./bin/message`

Here is the response I got back:
![OPEA Ollama response](/opea-comps/assets/opea-ollama-response.png)
