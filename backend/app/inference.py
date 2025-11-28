import os
import requests
import time
import json
from typing import Optional

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama")

def ensure_model_pulled():
    """
    Check if the TinyLlama model is available in Ollama.
    If not, automatically pull it.
    """
    max_retries = 30
    retry_delay = 2
    
    # Wait for Ollama to be ready
    for attempt in range(max_retries):
        try:
            url = f"{OLLAMA_BASE_URL}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            break  # Ollama is ready
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                print(f"Waiting for Ollama to be ready... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print(f"Warning: Could not connect to Ollama after {max_retries} attempts.")
                print("   The service will use fallback responses until Ollama is available.")
                return
    
    try:
        # Check if model exists
        url = f"{OLLAMA_BASE_URL}/api/tags"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        models = response.json().get("models", [])
        model_names = [model.get("name", "") for model in models]
        
        if OLLAMA_MODEL not in model_names:
            print(f"Model {OLLAMA_MODEL} not found. Pulling model (this may take a few minutes)...")
            pull_url = f"{OLLAMA_BASE_URL}/api/pull"
            pull_response = requests.post(
                pull_url,
                json={"name": OLLAMA_MODEL},
                timeout=None,  # No timeout for model pull
                stream=True
            )
            pull_response.raise_for_status()
            
            # Stream the pull progress
            for line in pull_response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode())
                        if "status" in data:
                            print(f"   {data['status']}")
                        if "completed" in data and "total" in data:
                            completed = data.get("completed", 0)
                            total = data.get("total", 0)
                            if total > 0:
                                percent = (completed / total) * 100
                                print(f"   Progress: {percent:.1f}% ({completed}/{total})")
                    except (json.JSONDecodeError, KeyError):
                        pass
            
            print(f"Model {OLLAMA_MODEL} pulled successfully!")
        else:
            print(f"Model {OLLAMA_MODEL} is already available.")
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not pull model: {e}")
        print("The model will be pulled automatically on first use.")

def ollama_inference(prompt: str, max_tokens: int = 100) -> str:
    """
    Call Ollama API to generate a response using TinyLlama model.
    Falls back to mock response if Ollama is unavailable or model not found.
    """
    try:
        # Prepare the request to Ollama
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7,
            }
        }
        
        response = requests.post(url, json=payload, timeout=60)
        
        # Check if model doesn't exist (Ollama will return 404 or error)
        if response.status_code == 404:
            # Try to pull the model automatically
            print(f"Model {OLLAMA_MODEL} not found. Attempting to pull...")
            try:
                pull_url = f"{OLLAMA_BASE_URL}/api/pull"
                pull_response = requests.post(
                    pull_url,
                    json={"name": OLLAMA_MODEL},
                    timeout=1  # Just trigger, don't wait
                )
            except:
                pass  # Pull initiated, will take time
            
            return f"Model {OLLAMA_MODEL} is being downloaded. Please wait a moment and try again. Using fallback response for now."
        
        response.raise_for_status()
        
        data = response.json()
        return data.get("response", "No response generated").strip()
    
    except requests.exceptions.RequestException as e:
        # Fallback to mock response if Ollama is unavailable
        print(f"Ollama request failed: {e}. Using fallback response.")
        return _fallback_response(prompt)

def _fallback_response(prompt: str) -> str:
    """Fallback mock response when Ollama is unavailable."""
    responses = {
        "hello": "Hello! I'm PocketLLM. How can I help you today?",
        "what": "I'm a lightweight language model running on CPU. I can answer questions and have conversations.",
        "how": "I use quantized models to run efficiently on limited resources."
    }
    
    prompt_lower = prompt.lower()
    for key, response in responses.items():
        if key in prompt_lower:
            return response
    
    return f"I received your message: '{prompt[:50]}...' Ollama is currently unavailable. Please ensure the Ollama service is running and the tinyllama model is pulled."

# Keep the old function name for backward compatibility
def mock_inference(prompt: str, max_tokens: int = 100) -> str:
    """Wrapper that calls Ollama inference."""
    return ollama_inference(prompt, max_tokens)