# src/agentic_saas_system/uiba_agent/uiba_core.py

import json
from typing import Dict, Any, Optional, List
from .data_models import UserTurnInput, ProjectBrief, UIMessage, ExtractedRequirement
from .llm_interface import LLMInterface
import datetime # Added import
# from ..shared_knowledge_base.client import SharedKnowledgeBaseClient # Conceptual

class UIBAgent:
    def __init__(self, llm_interface: LLMInterface, skb_client: Optional[Any] = None, uiba_model_name: str = "gpt-3.5-turbo"): # Default to the working alias
        """
        User Interaction & Briefing Agent (UIBA).
        Handles communication with the user, gathers requirements, and produces a Project Brief.
        Now defaults uiba_model_name to 'gpt-3.5-turbo' for the user's public API.
        """
        self.llm_interface = llm_interface
        self.skb_client = skb_client
        self.uiba_model_name = uiba_model_name
        self.dialogue_history: List[Dict[str, str]] = []
        self.current_project_brief_ideas: Dict[str, Any] = {
            "project_name": "Untitled SaaS Project", "high_level_summary": "", "target_audience": None,
            "features": [], "data_models_overview": [], "non_functional_requirements": [],
            "ui_ux_considerations": [], "raw_user_input_log": []
        }
        self.extracted_requirements_log: List[ExtractedRequirement] = []

    async def start_interaction(self, initial_message_text: str = "Hello! I'm the UIBA. How can I help you define your SaaS application today?") -> UIMessage:
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
        Handles a single turn of user input. For this basic loop, it will:
        1. Add user message to history.
        2. Call LLM to get a conversational response based on history.
        3. Add agent response to history.
        4. Return the agent's response.
        (More complex interpretation and brief building is deferred for this step)
        """
        if not user_input.text: # Ensure there's text input
            return UIMessage(message_type="error", text_content="No text input received.")

        self.dialogue_history.append({"role": "user", "content": user_input.text})
        # Ensure raw_user_input_log is initialized if not done in __init__ or start_interaction
        if "raw_user_input_log" not in self.current_project_brief_ideas:
            self.current_project_brief_ideas["raw_user_input_log"] = []
        self.current_project_brief_ideas["raw_user_input_log"].append(user_input)

        # For this basic loop, directly generate a conversational response
        # We'll use a simplified prompt or just the history.
        # The more complex interpretation for brief building will be re-enabled later.

        response_generation_messages = self._build_conversational_response_prompt_messages()

        llm_response_data = None # Initialize to avoid reference before assignment in except block
        try:
            llm_response_data = await self.llm_interface.get_chat_completion(
                messages=response_generation_messages,
                model_name=self.uiba_model_name
            )

            response_text = llm_response_data["choices"][0]["message"]["content"]
            if not response_text: # Handle empty content
                 response_text = "I've received your message. What else would you like to discuss?"


        except Exception as e:
            print(f"Error during LLM conversational response: {e}")
            response_text = "I encountered an issue trying to respond. Please try again."
            # Check if llm_response_data exists and has content, useful for debugging
            if llm_response_data: # Check if it was assigned
                print(f"DEBUG: LLM raw response data on error: {llm_response_data}")


        agent_response = UIMessage(message_type="info_update", text_content=response_text)
        self.dialogue_history.append({"role": "agent", "content": agent_response.text_content})
        return agent_response

    def _build_conversational_response_prompt_messages(self) -> List[Dict[str,str]]:
        """ Builds messages for the LLM to generate a direct conversational response. """
        system_prompt = (
            "You are UIBA, a friendly and helpful AI assistant designed to help users define requirements for a SaaS application. "
            "Engage in a natural conversation. Ask clarifying questions if needed, but primarily aim to be conversational and guide the user. "
            "Keep your responses relatively concise for a chat interface."
        )

        messages = [{"role": "system", "content": system_prompt}]
        # Add recent dialogue history for context (e.g., last 10 turns)
        messages.extend(self.dialogue_history[-10:])
        return messages

    # --- Methods for more complex interpretation and brief building (to be fully enabled later) ---

    def _build_interpretation_prompt_messages(self, user_input: UserTurnInput) -> List[Dict[str,str]]:
        # This method will be used later for detailed requirement extraction.
        # For now, it's not directly called by the simplified handle_user_input.
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

        user_content = user_input.text or ""
        if user_input.multimodal_content:
            user_content += "\n[User provided multimodal content: "
            for item in user_input.multimodal_content:
                user_content += f"{item.type} - {item.description or 'no description'}; "
            user_content += "]"

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here's the latest input from the user: {user_content}"}
        ]

    def _update_project_brief_ideas_from_llm(self, llm_extracted_data: Dict[str, Any]):
        # This method will be used later.
        if "project_name" in llm_extracted_data and llm_extracted_data["project_name"]:
            self.current_project_brief_ideas["project_name"] = llm_extracted_data["project_name"]
        if "high_level_summary" in llm_extracted_data and llm_extracted_data["high_level_summary"]:
            self.current_project_brief_ideas["high_level_summary"] = llm_extracted_data["high_level_summary"]

        for category in ["features", "data_models_overview", "non_functional_requirements", "ui_ux_considerations"]:
            if category in llm_extracted_data and isinstance(llm_extracted_data[category], list):
                if category not in self.current_project_brief_ideas or not isinstance(self.current_project_brief_ideas[category], list):
                    self.current_project_brief_ideas[category] = []
                for item_data in llm_extracted_data[category]:
                    if isinstance(item_data, dict):
                        self.current_project_brief_ideas[category].append(item_data)
                        self.extracted_requirements_log.append(
                            ExtractedRequirement(category=category, description=str(item_data))
                        )
        pass

    async def generate_project_brief(self) -> ProjectBrief:
        # This method will be used later for full brief generation.
        # For this basic loop, return a minimal brief.
        return ProjectBrief(
            project_name=self.current_project_brief_ideas.get("project_name", "Untitled Project"),
            high_level_summary=self.current_project_brief_ideas.get("high_level_summary", "N/A for basic loop"),
            target_audience=self.current_project_brief_ideas.get("target_audience"),
            features=self.current_project_brief_ideas.get("features", []),
            data_models_overview=self.current_project_brief_ideas.get("data_models_overview", []),
            non_functional_requirements=self.current_project_brief_ideas.get("non_functional_requirements", []),
            ui_ux_considerations=self.current_project_brief_ideas.get("ui_ux_considerations", []),
            raw_user_input_log=self.current_project_brief_ideas.get("raw_user_input_log", []),
            generation_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

    async def store_project_brief(self, project_brief: ProjectBrief) -> bool:
        # This method will be used later.
        if self.skb_client:
            try:
                document_id = f"project_brief_{project_brief.project_name.replace(' ', '_')}_{project_brief.generation_timestamp}"
                # In a real scenario: await self.skb_client.store_document(document_id, project_brief.model_dump())
                print(f"INFO: (Basic Loop) Project brief '{project_brief.project_name}' would be stored with ID {document_id}.")
                return True
            except Exception as e:
                print(f"ERROR: Failed to (mock) store project brief: {e}")
                return False
        else:
            print("WARN: SharedKnowledgeBaseClient not configured. Cannot store brief.")
            return False

    def present_to_user(self, ui_message: UIMessage) -> None:
        # This is called by main.py, so it's fine as is.
        # (This method itself doesn't print, it's for structuring the message for the UI layer)
        # The actual printing happens in main.py
        pass

# Conceptual `if __name__ == '__main__':` block in uiba_core.py (not for direct run in subtask)
# async def core_example():
#    # This is where you might put test code for uiba_core itself, if needed.
#    # For now, main.py serves as the entry point for testing interaction.
#    pass
# if __name__ == '__main__':
#    import asyncio
#    asyncio.run(core_example())
