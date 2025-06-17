# src/agentic_saas_system/uiba_agent/main.py

import asyncio
import uuid
import datetime # For timestamp in UserTurnInput
import httpx # For specific error handling
import traceback # For printing full tracebacks

from .uiba_core import UIBAgent
from .llm_interface import LLMInterface, USER_API_BASE_URL, USER_API_KEY # Import credentials for clarity
from .data_models import UserTurnInput, UIMessage, ProjectBrief # Added ProjectBrief for the --generate_brief command

class MockSKBClient:
    """A mock SKB client for standalone UIBA testing."""
    async def store_document(self, doc_id: str, data: dict): # data should be Dict from Pydantic model_dump
        print(f"MOCK SKB: Storing document '{doc_id}': Project Name '{data.get('project_name', 'N/A')}'")
        return True

    async def retrieve_document(self, doc_id: str):
        print(f"MOCK SKB: Retrieving document '{doc_id}'")
        return None

async def run_uiba_interactive_session():
    """
    Simulates an interactive session with the UIBAgent for testing or standalone use.
    """
    session_id = str(uuid.uuid4())
    print(f"Starting UIBA Interactive Session (ID: {session_id})")
    print(f"Using API Endpoint: {USER_API_BASE_URL}") # Corrected f-string
    print("Type 'exit' or 'quit' to end the session.")
    print("Type '--generate_brief' to attempt generating a (basic) project brief.")
    print("-" * 30)

    # Initialize dependencies using user's public API credentials
    llm_interface = LLMInterface(api_key=USER_API_KEY, base_url=USER_API_BASE_URL)
    skb_client = MockSKBClient()

    # UIBAgent now defaults to "gpt-3.5-turbo", which should work with the user's endpoint for devstral.
    uiba_agent = UIBAgent(llm_interface=llm_interface, skb_client=skb_client)

    try:
        initial_agent_message: UIMessage = await uiba_agent.start_interaction()
        # uiba_agent.present_to_user(initial_agent_message) # main.py will print
        print(f"Agent: {initial_agent_message.text_content}")


        while True:
            user_text = input("User: ").strip()

            if not user_text: # Handle empty input from user
                continue

            if user_text.lower() in ["exit", "quit"]:
                print("Exiting session.")
                break

            if user_text.lower() == "--generate_brief":
                print("Attempting to generate (basic) project brief...")
                # For this basic loop, generate_project_brief returns a minimal brief
                project_brief: ProjectBrief = await uiba_agent.generate_project_brief()
                if project_brief:
                    print("\n--- Generated Project Brief (Basic) ---")
                    # Using model_dump_json for Pydantic models
                    print(project_brief.model_dump_json(indent=2))
                    print("--- End of Brief ---")
                    if uiba_agent.skb_client: # Check if skb_client is configured in agent
                        stored = await uiba_agent.store_project_brief(project_brief)
                        if stored:
                            print("Project brief (mock) stored successfully.")
                        else:
                            print("Failed to (mock) store project brief.")
                else:
                    print("No project brief generated yet or an error occurred.")
                continue

            # Use datetime for timestamp
            current_timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            user_turn = UserTurnInput(
                text=user_text,
                timestamp=current_timestamp_iso
            )

            agent_response: UIMessage = await uiba_agent.handle_user_input(user_turn)
            # uiba_agent.present_to_user(agent_response) # main.py will print
            print(f"Agent: {agent_response.text_content}")

            if agent_response.message_type == "error":
                print(f"Agent Error: {agent_response.text_content}")

    except httpx.RequestError as e:
        print(f"CRITICAL: Could not connect to LLM API at {llm_interface.base_url}. Error: {e}")
        print("Please ensure the API server is running, accessible, and the URL is correct.")
        traceback.print_exc()
    except Exception as e:
        print(f"An unexpected error occurred during the session: {e}")
        traceback.print_exc()
    finally:
        print("Closing LLM interface...")
        await llm_interface.close()
        print("UIBA session ended.")

if __name__ == "__main__":
    print("UIBA Main - Standalone Interactive Mode (Basic Text Loop)")
    print(f"Attempting to use API: {USER_API_BASE_URL}")
    print("Ensure the API endpoint is operational and the model 'gpt-3.5-turbo' (or equivalent for devstral) is available.")

    try:
        asyncio.run(run_uiba_interactive_session())
    except KeyboardInterrupt:
        print("\nSession terminated by user.")
    except Exception as e:
        print(f"Fatal error running UIBA session: {e}")
        traceback.print_exc()
