# src/agentic_saas_system/uiba_agent/main.py

import asyncio
import uuid # For generating session IDs

from .uiba_core import UIBAgent
from .llm_interface import LLMInterface
from .data_models import UserTurnInput, UIMessage

# Conceptual placeholder for SharedKnowledgeBaseClient
# from ..shared_knowledge_base.client import SharedKnowledgeBaseClient

class MockSKBClient:
    """A mock SKB client for standalone UIBA testing."""
    async def store_document(self, doc_id: str, data: dict):
        print(f"MOCK SKB: Storing document '{doc_id}': {data.get('project_name', 'N/A')}")
        return True

    async def retrieve_document(self, doc_id: str):
        print(f"MOCK SKB: Retrieving document '{doc_id}'")
        return None # Or some mock data

async def run_uiba_interactive_session():
    """
    Simulates an interactive session with the UIBAgent for testing or standalone use.
    """
    session_id = str(uuid.uuid4())
    print(f"Starting UIBA Interactive Session (ID: {session_id})")
    print("Type 'exit' or 'quit' to end the session.")
    print("Type '--generate_brief' to attempt generating and storing the project brief.")
    print("-" * 30)

    # Initialize dependencies
    # In a real system, LLMInterface might take API keys/base_urls from config
    llm_interface = LLMInterface()

    # Using MockSKBClient for this standalone example
    # skb_client = SharedKnowledgeBaseClient(...) # If we had a real one
    skb_client = MockSKBClient()

    # Specify the model UIBA should use (should come from config ideally)
    uiba_model = "devstral-small-iq4nl-gguf" # Example model name for LocalAI

    uiba_agent = UIBAgent(llm_interface=llm_interface, skb_client=skb_client, uiba_model_name=uiba_model)

    try:
        initial_agent_message: UIMessage = await uiba_agent.start_interaction()
        print(f"Agent: {initial_agent_message.text_content}")

        while True:
            user_text = input("User: ")

            if user_text.lower() in ["exit", "quit"]:
                print("Exiting session.")
                break

            if user_text.lower() == "--generate_brief":
                print("Attempting to generate project brief...")
                project_brief = await uiba_agent.generate_project_brief()
                if project_brief:
                    print("\n--- Generated Project Brief ---")
                    print(project_brief.model_dump_json(indent=2))
                    print("--- End of Brief ---")
                    # Attempt to store it (using mock SKB here)
                    if skb_client: # Check if skb_client is not None
                        stored = await uiba_agent.store_project_brief(project_brief)
                        if stored:
                            print("Project brief (mock) stored successfully.")
                        else:
                            print("Failed to (mock) store project brief.")
                else:
                    print("No project brief generated yet or an error occurred.")
                continue

            current_timestamp = asyncio.get_event_loop().time() # Simple timestamp for example
            user_turn = UserTurnInput(
                text=user_text,
                # multimodal_content can be added here if we simulate it
                timestamp=str(current_timestamp)
            )

            agent_response: UIMessage = await uiba_agent.handle_user_input(user_turn)
            print(f"Agent: {agent_response.text_content}")
            if agent_response.message_type == "error":
                print("An error occurred. Please try rephrasing or check logs.")

    except Exception as e:
        print(f"An unexpected error occurred during the session: {e}")
    finally:
        print("Closing LLM interface.")
        await llm_interface.close()
        print("UIBA session ended.")

if __name__ == "__main__":
    # This allows running the UIBA in a simple interactive command-line mode.
    # For a full system, UIBA would be part of a larger orchestration.

    # Note: This requires a LocalAI server to be running and accessible at
    #       http://localhost:8080 with the specified model loaded.
    #       If not, httpx.RequestError will occur.

    print("UIBA Main - Standalone Interactive Mode")
    print("Ensure LocalAI is running with the required models.")

    try:
        asyncio.run(run_uiba_interactive_session())
    except KeyboardInterrupt:
        print("\nSession terminated by user.")
    except Exception as e:
        # This top-level catch is for issues during asyncio.run itself or unhandled ones from the session
        print(f"Fatal error running UIBA session: {e}")
