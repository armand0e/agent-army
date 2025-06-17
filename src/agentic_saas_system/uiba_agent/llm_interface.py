# src/agentic_saas_system/uiba_agent/llm_interface.py

import httpx # Using httpx for async requests, good for I/O bound LLM calls
import json
from typing import List, Dict, Any, Optional, Union

# Configuration for LocalAI (ideally from a central config)
LOCAL_AI_BASE_URL = "http://localhost:8080/v1" # As planned for LocalAI

class LLMInterface:
    def __init__(self, api_key: Optional[str] = "dummy-key", base_url: str = LOCAL_AI_BASE_URL):
        """
        Interface for interacting with a locally hosted LLM via an OpenAI-compatible API (e.g., LocalAI).
        """
        self.base_url = base_url
        self.api_key = api_key # LocalAI might not need a key, but OpenAI spec includes it
        self.client = httpx.AsyncClient(timeout=120.0) # Increased timeout for potentially slow local models

    async def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model_name: str, # e.g., "devstral-small-iq4nl-gguf"
        temperature: float = 0.7,
        max_tokens: int = 1500,
        json_mode: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None, # For function calling / tool use
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None
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

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"LLM API Error (HTTPStatusError): {e.response.status_code} - {e.response.text}")
            # Consider more specific error handling or re-raising custom errors
            raise
        except httpx.RequestError as e:
            print(f"LLM API Error (RequestError): {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"LLM API Error (JSONDecodeError): Failed to decode response - {e}")
            raise

    async def generate_text_completion(
        self,
        prompt: str, # Simpler interface for basic text generation if needed, though chat is preferred
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        A simplified method for basic text generation (less common now with chat models).
        Constructs a chat-like message list internally.
        """
        messages = [{"role": "user", "content": prompt}]
        response_data = await self.get_chat_completion(
            messages=messages,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
        # Extract content from the first choice's message
        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            print(f"Error parsing LLM response: {e} - Data: {response_data}")
            return "Error: Could not parse LLM response."

    async def close(self):
        """
        Closes the HTTP client.
        """
        await self.client.aclose()

if __name__ == '__main__':
    # Example usage (conceptual, requires a running LocalAI server)
    async def main():
        # llm_interface = LLMInterface()
        # try:
        #     messages = [
        #         {"role": "system", "content": "You are a helpful assistant."},
        #         {"role": "user", "content": "What is the capital of France?"}
        #     ]
        #     # Replace 'devstral-test-model' with an actual model name configured in your LocalAI
        #     response = await llm_interface.get_chat_completion(messages, model_name="devstral-test-model")
        #     print("Full response data:")
        #     print(json.dumps(response, indent=2))
        #     if response and response.get("choices"):
        #         print("\nAssistant's reply:")
        #         print(response["choices"][0]["message"]["content"])

        #     # Example of JSON mode (if the model supports it and is prompted correctly)
        #     json_messages = [
        #         {"role": "system", "content": "You are an assistant that only responds in JSON."},
        #         {"role": "user", "content": "Provide user details for user ID 123. Include name and email."}
        #     ]
        #     # json_response = await llm_interface.get_chat_completion(
        #     #     json_messages, model_name="devstral-test-model", json_mode=True
        #     # )
        #     # print("\nJSON mode response data:")
        #     # print(json.dumps(json_response, indent=2))
        #     # if json_response and json_response.get("choices"):
        #     #     print("\nAssistant's JSON reply:")
        #     #     print(json_response["choices"][0]["message"]["content"])

        # except httpx.RequestError as e:
        #     print(f"Could not connect to LocalAI or network error: {e}")
        # except Exception as e:
        #     print(f"An unexpected error occurred: {e}")
        # finally:
        #     await llm_interface.close()
        pass # Keep if __name__ == '__main__' block but do nothing for now

    # import asyncio
    # if __name__ == '__main__':
    #    asyncio.run(main())
    pass
