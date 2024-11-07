# Ailite

A lightweight Python interface for AI model interactions through Hugging Face's infrastructure.

## Installation

```bash
pip install ailite
```

## Usage

### 1. Initially SETUP Server Deployment with `serve()`

Launch your own API server:

```python
from ailite import serve

# Start server on http://0.0.0.0:11435
serve()
```

### 1. Quick Start with `ai()`

The simplest way to get started:

```python
from ailite import ai
response = ai("Explain quantum computing")
print(response)
```
### 2. Customization with `ai()`
```python
from ailite import ai
response = ai(
    "Explain quantum computing",
    model="nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
    conversation=False
)
```
### 3. Streaming Response with `ai()`
```python
from ailite import ai
# With streaming
for chunk in ai(
    "Write a story about space",
    stream=True
):
    print(chunk, end="")
```


### 4. Client Usage with `HUGPIClient`

For more control over interactions:

```python
from ailite import HUGPIClient

client = HUGPIClient(
    api_key="your_email@gmail.com_your_password",
    model="nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
    system_prompt="You are a helpful assistant..."
)

# Generate text
response = client.messages.create(
    prompt="What is the theory of relativity?",
    conversation=True
)
print(response.content[0]["text"])

# Chat conversation
messages = [
    {"role": "user", "content": "Hi, how are you?"},
    {"role": "assistant", "content": "I'm doing well, how can I help?"},
    {"role": "user", "content": "Tell me about AI"}
]
response = client.messages.create(messages=messages)
```

### 5. Base Model with `HUGPiLLM`

For direct model interactions:

```python
from ailite import HUGPiLLM

llm = HUGPiLLM(
    hf_email="your_email@gmail.com",
    hf_password="your_password",
    default_llm=3,  # Model index
    system_prompt="Custom system instructions here"
)

response = llm.generate("Explain machine learning")
```

## Dependencies

```
fastapi>=0.68.0
pydantic>=1.8.0
uvicorn>=0.15.0
requests>=2.26.0
```

## License

MIT License - see LICENSE file for details.