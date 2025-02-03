import requests
import json
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
USE_OLLAMA = True  # Switch between Ollama (True) and OpenAI (False)

# Ollama settings
OLLAMA_URL = "http://192.168.0.225:11434/api/chat"
OLLAMA_MODEL = "deepseek-r1:7b"

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-3.5-turbo"

# Common settings
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f"Bearer {OPENAI_API_KEY}" if not USE_OLLAMA else ""
}

def create_chat_message(content: str) -> Dict[str, Any]:
    if USE_OLLAMA:
        return {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": content}],
            "stream": True
        }
    else:
        return {
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": content}],
            "stream": True
        }

def fetch_chat_response(content: str) -> Optional[requests.Response]:
    url = OLLAMA_URL if USE_OLLAMA else OPENAI_URL
    data = create_chat_message(content)
    
    try:
        response = requests.post(url, json=data, headers=HEADERS, stream=True)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

def process_streaming_response(response: Optional[requests.Response]) -> str:
    full_response = ""
    if response:
        print("\nAI Response:", flush=True)
        print("-" * 50)
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode('utf-8'))
                    if USE_OLLAMA:
                        content = chunk.get('message', {}).get('content', '')
                    else:
                        content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                    
                    if content:
                        full_response += content
                        print(content, end='', flush=True)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
        print("\n" + "-" * 50)
    return full_response

def main():
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        response = fetch_chat_response(user_input)
        full_response = process_streaming_response(response)

if __name__ == "__main__":
    main()
