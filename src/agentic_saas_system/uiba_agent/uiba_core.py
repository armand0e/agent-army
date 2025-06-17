# src/agentic_saas_system/uiba_agent/uiba_core.py

from typing import Dict, Any, Optional, List, Tuple
from .data_models import UserTurnInput, ProjectBrief, UIMessage, ExtractedRequirement # Using specific models
from .llm_interface import LLMInterface
import json # Added for parsing LLM JSON responses
# from ..shared_knowledge_base.client import SharedKnowledgeBaseClient # Conceptual

class UIBAgent:
    def __init__(self, llm_interface: LLMInterface, skb_client: Optional[Any] = None, uiba_model_name: str = "devstral-small-iq4nl-gguf"): # Patched Any for SKB
        """
        User Interaction & Briefing Agent (UIBA).
        Handles communication with the user, gathers requirements, and produces a Project Brief.
        """
        self.llm_interface = llm_interface
        self.skb_client = skb_client
        self.uiba_model_name = uiba_model_name # Model to be used by UIBA
        self.dialogue_history: List[Dict[str, str]] = []
        self.current_project_brief_ideas: Dict[str, Any] = { # Initialize keys based on ProjectBrief
            "project_name": "Untitled SaaS Project",
            "high_level_summary": "",
            "target_audience": None,
            "features": [],
            "data_models_overview": [],
            "non_functional_requirements": [],
            "ui_ux_considerations": [],
            "raw_user_input_log": []
        }
        self.extracted_requirements_log: List[ExtractedRequirement] = []


    async def start_interaction(self, initial_message_text: str = "Hello! I'm here to help you define your SaaS application. What are you envisioning?") -> UIMessage:
        """
        Starts or restarts an interaction with the user.
        """
        self.dialogue_history = []
        self.current_project_brief_ideas = {
            "project_name": "Untitled SaaS Project", "high_level_summary": "", "target_audience": None,
            "features": [], "data_models_overview": [], "non_functional_requirements": [],
            "ui_ux_considerations": [], "raw_user_input_log": []
        }
        self.extracted_requirements_log = []

        agent_response = UIMessage(message_type="greeting", text_content=initial_message_text)
        self.dialogue_history.append({"role": "agent", "content": agent_response.text_content})
        return agent_response

    async def handle_user_input(self, user_input: UserTurnInput) -> UIMessage:
        """
        Handles a single turn of user input.
        Processes it, updates dialogue state, and returns agent's response.
        """
        self.dialogue_history.append({"role": "user", "content": user_input.text or ""})
        if user_input.text: # Add to raw log
             # Ensure raw_user_input_log is initialized
            if "raw_user_input_log" not in self.current_project_brief_ideas:
                self.current_project_brief_ideas["raw_user_input_log"] = []
            self.current_project_brief_ideas["raw_user_input_log"].append(user_input)

        # 1. Interpret user input using LLM
        interpretation_prompt_messages = self._build_interpretation_prompt_messages(user_input)

        try:
            llm_response_data = await self.llm_interface.get_chat_completion(
                messages=interpretation_prompt_messages,
                model_name=self.uiba_model_name, # Or a specific model for this task
                json_mode=True # Expecting structured JSON output for requirements
            )

            # Assuming LLM returns JSON string in content, parse it
            content_str = llm_response_data["choices"][0]["message"]["content"]
            structured_interpretation = json.loads(content_str) if content_str else {}

            # Process structured_interpretation to update brief ideas and log extracted requirements
            self._update_project_brief_ideas_from_llm(structured_interpretation)

        except Exception as e:
            print(f"Error during LLM interpretation: {e}")
            # Fallback or error handling
            error_response = UIMessage(message_type="error", text_content="I had trouble understanding that. Could you try rephrasing?")
            self.dialogue_history.append({"role": "agent", "content": error_response.text_content})
            return error_response

        # 2. Generate next response to user (e.g., ask clarification questions, confirm understanding)
        # This would typically be another LLM call based on the current dialogue and brief state
        response_generation_messages = self._build_response_generation_prompt_messages()
        try:
            llm_response_for_user = await self.llm_interface.get_chat_completion(
                messages=response_generation_messages,
                model_name=self.uiba_model_name
            )
            response_text = llm_response_for_user["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error during LLM response generation: {e}")
            response_text = "I'm processing your input. What's next?" # Fallback

        agent_response = UIMessage(message_type="info_update", text_content=response_text)
        self.dialogue_history.append({"role": "agent", "content": agent_response.text_content})
        return agent_response

    def _build_interpretation_prompt_messages(self, user_input: UserTurnInput) -> List[Dict[str,str]]:
        """
        Builds messages for the LLM to interpret user input and extract structured information.
        Should instruct the LLM to output JSON matching parts of ProjectBrief or ExtractedRequirement.
        """
        system_prompt = (
            "You are an expert requirements gathering assistant for SaaS applications. "
            "Your goal is to extract structured information from the user's input. "
            "The user is describing a SaaS application they want to build. "
            "Focus on identifying: project name, high-level summary, target audience, "
            "specific features (with name, description, user_stories, acceptance_criteria), "
            "data model ideas (name, attributes, relationships), "
            "non-functional requirements (category, requirement, metric), "
            "and UI/UX considerations (element_description, notes, multimodal_references). "
            "If the user provides unclear information, formulate clarifying questions. "
            "Always respond in JSON format with keys corresponding to these categories. "
            "For example: {\"project_name\": \"New App\", \"features\": [{\"name\": \"Login\", ...}]}"
        )

        # Simplified context for now, could include more of dialogue_history or current_project_brief_ideas
        user_content = user_input.text or ""
        if user_input.multimodal_content:
            user_content += "\n[User provided multimodal content: "
            for item in user_input.multimodal_content:
                user_content += f"{item.type} - {item.description or 'no description'}; "
            user_content += "]"
            # Note: Actual multimodal processing requires a capable model and different API handling.
            # This string representation is just a placeholder for Devstral.

        return [
            {"role": "system", "content": system_prompt},
            # Could add previous few turns of dialogue_history here for more context
            {"role": "user", "content": f"Here's the latest input from the user: {user_content}"}
        ]

    def _build_response_generation_prompt_messages(self) -> List[Dict[str,str]]:
        """ Builds messages for the LLM to generate the next conversational turn to the user. """
        system_prompt = (
            "You are a helpful and friendly assistant helping a user define a SaaS application. "
            "Based on the current conversation history and the information gathered so far for the project brief, "
            "decide on the best next response. This could be: "
            "1. Asking a clarifying question about a recently mentioned topic. "
            "2. Confirming understanding of a feature. "
            "3. Prompting the user for more details on a specific area (e.g., 'Tell me more about the data you need to store.'). "
            "4. Summarizing what has been gathered so far if it seems like a good point to do so. "
            "Keep your responses concise and focused on moving the requirements gathering forward."
        )

        # Include relevant parts of dialogue_history and current_project_brief_ideas
        # For brevity, just using dialogue_history for now
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.dialogue_history[-5:]) # Last 5 turns for context
        messages.append({"role": "user", "content": "What should I say next to the user?"}) # Prompt for the LLM's response
        return messages

    def _update_project_brief_ideas_from_llm(self, llm_extracted_data: Dict[str, Any]):
        """
        Updates the internal project_brief_ideas with data extracted by the LLM.
        Also logs individual requirements.
        """
        # This needs to be robust and carefully map LLM output keys to ProjectBrief fields.
        # Example:
        if "project_name" in llm_extracted_data and llm_extracted_data["project_name"]:
            self.current_project_brief_ideas["project_name"] = llm_extracted_data["project_name"]
        if "high_level_summary" in llm_extracted_data and llm_extracted_data["high_level_summary"]:
            self.current_project_brief_ideas["high_level_summary"] = llm_extracted_data["high_level_summary"]
        # ... and so on for other direct fields ...

        for category in ["features", "data_models_overview", "non_functional_requirements", "ui_ux_considerations"]:
            if category in llm_extracted_data and isinstance(llm_extracted_data[category], list):
                # Ensure the category list exists in current_project_brief_ideas
                if category not in self.current_project_brief_ideas or not isinstance(self.current_project_brief_ideas[category], list):
                    self.current_project_brief_ideas[category] = []

                for item_data in llm_extracted_data[category]:
                    try:
                        # Here you would validate/parse item_data into the respective Pydantic model
                        # For now, just appending if it's a dict.
                        if isinstance(item_data, dict):
                            self.current_project_brief_ideas[category].append(item_data)
                            # Log as ExtractedRequirement
                            self.extracted_requirements_log.append(
                                ExtractedRequirement(category=category, description=str(item_data))
                            )
                    except Exception as e: # Catch Pydantic validation errors or other issues
                        print(f"Warning: Could not parse item for {category}: {item_data}, Error: {e}")

        # print(f"DEBUG: Project brief ideas updated after LLM: {self.current_project_brief_ideas}")


    async def generate_project_brief(self) -> ProjectBrief:
        """
        Consolidates the gathered information into a final ProjectBrief structure.
        This could involve a final LLM call to synthesize and structure, or just use current_project_brief_ideas.
        For now, we'll directly construct from current_project_brief_ideas.
        """
        # In a more advanced version, an LLM call could be made here to refine the brief.
        # final_brief_prompt_messages = self._build_final_brief_prompt_messages()
        # llm_final_brief_data = await self.llm_interface.get_chat_completion(...)
        # parsed_brief_data = json.loads(llm_final_brief_data["choices"][0]["message"]["content"])
        # return ProjectBrief(**parsed_brief_data)

        import datetime # For timestamp
        return ProjectBrief(
            project_name=self.current_project_brief_ideas.get("project_name", "Untitled Project"),
            high_level_summary=self.current_project_brief_ideas.get("high_level_summary", ""),
            target_audience=self.current_project_brief_ideas.get("target_audience"),
            features=self.current_project_brief_ideas.get("features", []),
            data_models_overview=self.current_project_brief_ideas.get("data_models_overview", []),
            non_functional_requirements=self.current_project_brief_ideas.get("non_functional_requirements", []),
            ui_ux_considerations=self.current_project_brief_ideas.get("ui_ux_considerations", []),
            raw_user_input_log=self.current_project_brief_ideas.get("raw_user_input_log", []),
            generation_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

    async def store_project_brief(self, project_brief: ProjectBrief) -> bool:
        """
        Stores the generated ProjectBrief into the Shared Knowledge Base.
        Returns True if successful, False otherwise.
        """
        if self.skb_client:
            try:
                document_id = f"project_brief_{project_brief.project_name.replace(' ', '_')}_{project_brief.generation_timestamp}"
                # self.skb_client.store_document(document_id, project_brief.model_dump()) # Use .model_dump() for Pydantic
                print(f"INFO: Project brief would be stored with ID {document_id}: {project_brief.model_dump_json(indent=2)}") # Placeholder
                return True
            except Exception as e:
                print(f"ERROR: Failed to store project brief: {e}")
                return False
        else:
            print("WARN: SharedKnowledgeBaseClient not configured. Cannot store brief.")
            return False

    def present_to_user(self, ui_message: UIMessage) -> None:
        """
        Presents information back to the user.
        (This would interact with the actual UI/CLI layer)
        """
        print(f"UIBA to User ({ui_message.message_type}): {ui_message.text_content}")
        if ui_message.structured_content:
            print(f"UIBA to User (Structured): {ui_message.structured_content}")

# Example Usage (conceptual)
async def run_uiba_example():
    # Mock LLMInterface and SKBClient for conceptual demonstration
    class MockLLMInterface(LLMInterface): # Inherit to ensure methods are present
        async def get_chat_completion(self, messages: List[Dict[str, str]], model_name: str, temperature: float = 0.7, max_tokens: int = 1500, json_mode: bool = False, tools=None, tool_choice=None) -> Dict[str, Any]:
            print(f"DEBUG: MockLLM received messages for model {model_name}: {messages[-1]['content'][:100]}...")

            # Need access to current_project_brief_ideas for one of the mocked responses.
            # This is a bit of a hack for a mock; in reality, the LLM is stateless.
            # We'll pass a reference or make it accessible if needed, or simplify the mock.
            # For now, let's assume it can't access self.current_project_brief_ideas directly.
            # We'll simplify the mock response that used it.

            last_user_message_content = ""
            if messages and messages[-1]['role'] == 'user':
                 last_user_message_content = messages[-1]['content']

            if json_mode: # For interpretation prompt
                if "blog platform" in last_user_message_content:
                    return {"choices": [{"message": {"content": json.dumps({
                        "project_name": "My Blog Platform",
                        "high_level_summary": "A platform for users to write and share posts.",
                        "features": [{"name": "User Registration", "description": "Users can sign up."}]
                    })}}]}
                elif "user accounts and posts" in last_user_message_content:
                     return {"choices": [{"message": {"content": json.dumps({
                        "features": [{"name": "Create Posts", "description": "Users can create posts."}],
                        "data_models_overview": [{"name": "User", "attributes": {"id": "int"}}]
                    })}}]}
                else:
                    return {"choices": [{"message": {"content": json.dumps({})}}]} # Empty JSON
            else: # For response generation
                # Simplified mock that doesn't need current_project_brief_ideas
                return {"choices": [{"message": {"content": "Understood. What else can you tell me about the project?"}}]}


    class MockSKBClient:
        async def store_document(self, doc_id: str, data: Dict[str, Any]): # Made async for consistency
            print(f"DEBUG: SKB storing document '{doc_id}': {data}")
            return True

    # Initialize
    # mock_llm = MockLLMInterface() # No base_url needed if using default in LLMInterface
    # mock_skb = MockSKBClient()
    # uiba = UIBAgent(llm_interface=mock_llm, skb_client=mock_skb, uiba_model_name="mock_devstral")

    # # Interaction
    # initial_response = await uiba.start_interaction()
    # uiba.present_to_user(initial_response)

    # turn1_input = UserTurnInput(text="I want to build a blog platform.", timestamp="now")
    # response1 = await uiba.handle_user_input(turn1_input)
    # uiba.present_to_user(response1)

    # turn2_input = UserTurnInput(text="It should have user accounts and posts.", timestamp="now")
    # response2 = await uiba.handle_user_input(turn2_input)
    # uiba.present_to_user(response2)

    # # Generate and store brief
    # final_brief = await uiba.generate_project_brief()
    # uiba.present_to_user(UIMessage(message_type="brief_summary", text_content="Here is the project brief:", structured_content=final_brief.model_dump()))

    # if final_brief:
    #    await uiba.store_project_brief(final_brief)

    # await mock_llm.close() # Close the client
    pass


if __name__ == '__main__':
    # import asyncio
    # asyncio.run(run_uiba_example())
    pass
