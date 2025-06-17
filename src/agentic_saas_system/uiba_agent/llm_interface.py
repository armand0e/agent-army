# src/agentic_saas_system/uiba_agent/llm_interface.py

import httpx # Using httpx for async requests, good for I/O bound LLM calls
import json
import asyncio # Added for the test
from typing import List, Dict, Any, Optional, Union # Added Union

# Configuration for the User-Provided API
USER_API_BASE_URL = "https://lm.armand0e.online/v1"
USER_API_KEY = "sk-291923902182902-kd" # User's provided API key

class LLMInterface:
    def __init__(self, api_key: str = USER_API_KEY, base_url: str = USER_API_BASE_URL): # Modified defaults
        """
        Interface for interacting with an LLM via an OpenAI-compatible API.
        Now defaults to user-provided public API.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=120.0)

    async def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model_name: str, # e.g., "devstral-small-iq4nl-gguf" or a model available on the public API
        temperature: float = 0.7,
        max_tokens: int = 1500,
        json_mode: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None # Added Union here
    ) -> Dict[str, Any]:
        """
        Gets a chat completion from the LLM.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        print(f"DEBUG: Sending request to {self.base_url}/chat/completions with model: {model_name}") # Debug print
        print(f"DEBUG: Payload (first message): {messages[0] if messages else 'No messages'}")


        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            print(f"DEBUG: Received response status: {response.status_code}") # Debug print
            # print(f"DEBUG: Response content: {response.text}") # Be careful if response is large
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"LLM API Error (HTTPStatusError): {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"LLM API Error (RequestError): {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"LLM API Error (JSONDecodeError): Failed to decode response - {e}")
            print(f"LLM Raw Response Text causing JSONDecodeError: {response.text if 'response' in locals() else 'Response object not available'}")
            raise

    async def generate_text_completion( # This method might be less used but kept for now
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        A simplified method for basic text generation.
        """
        messages = [{"role": "user", "content": prompt}]
        response_data = await self.get_chat_completion(
            messages=messages,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e: # Added TypeError
            print(f"Error parsing LLM response: {e} - Data: {response_data}")
            return "Error: Could not parse LLM response."

    async def close(self):
        """
        Closes the HTTP client.
        """
        await self.client.aclose()

async def test_api_endpoint():
    print("Testing user-provided API endpoint...")
    # Use the provided credentials directly for this test
    llm_interface = LLMInterface(api_key=USER_API_KEY, base_url=USER_API_BASE_URL)

    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France? Respond concisely."}
    ]
    # We need to know a model name that is available on the user's endpoint.
    # Let's try a common one, or the one intended for use.
    # If 'devstral-small' is not on that public API, this will fail.
    # A more generic model like "gpt-3.5-turbo" might be safer for a generic endpoint test,
    # but the user intends to use devstral. We'll try with a placeholder and make it easily changeable.
    # IMPORTANT: The user might need to tell us what models are available on their endpoint.
    # For now, let's assume a generic model name for testing the connection.
    # The user's endpoint might not have 'devstral-small'.
    # Let's try a common model name, if that fails, it indicates an issue with model availability or the endpoint itself.

    # Try with a few common model names, or a placeholder that the user can easily change.
    # The user mentioned wanting to use devstral-small. Let's try that first.
    # If it fails, the error message will guide us.
    test_model_name = "devstral-small"
    # Alternative test_model_name = "gpt-3.5-turbo" # if devstral-small is not available
    # Note: "gpt-3.5-turbo" resulted in a successful call to the endpoint, which responded
    # with model "unsloth/devstral-small-2505". Requesting "devstral-small" directly
    # previously caused a server-side model crash (HTTP 400).
    # The user's endpoint might require specific model names or aliases.

    try:
        print(f"Attempting to connect to {llm_interface.base_url} with model '{test_model_name}'...")
        response = await llm_interface.get_chat_completion(test_messages, model_name=test_model_name, max_tokens=50)
        print("\n--- API Test Full Response ---")
        print(json.dumps(response, indent=2))
        if response and response.get("choices") and response["choices"][0].get("message"):
            print("\n--- API Test Assistant's Reply ---")
            print(response["choices"][0]["message"]["content"])
            print("\nAPI Endpoint Test: SUCCESS")
        else:
            print("\nAPI Endpoint Test: FAILED - Response format unexpected.")
            print("Response was: ", response)

    except httpx.HTTPStatusError as e:
        print(f"API Endpoint Test: FAILED (HTTPStatusError)")
        print(f"Status Code: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        if e.response.status_code == 401:
            print("This might be an API key issue.")
        elif e.response.status_code == 404:
            print(f"This might mean the model '{test_model_name}' is not found or the URL path is incorrect.")
        elif e.response.status_code == 429:
            print("Rate limit hit. Please try again later or check your plan for the API.")
    except httpx.RequestError as e:
        print(f"API Endpoint Test: FAILED (RequestError)")
        print(f"Could not connect to the API endpoint: {e}")
        print("Please ensure the URL is correct and the server is running and accessible.")
    except Exception as e:
        print(f"API Endpoint Test: FAILED (Unexpected Error)")
        print(f"An unexpected error occurred: {e}")
    finally:
        await llm_interface.close()

if __name__ == '__main__':
    # This will run the test when the script is executed directly.
    print("Running LLMInterface Test...")
    asyncio.run(test_api_endpoint())
