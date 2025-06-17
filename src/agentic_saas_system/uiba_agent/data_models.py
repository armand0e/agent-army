# src/agentic_saas_system/uiba_agent/data_models.py

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field # Using Pydantic for robust data modeling

# --- Input Data Models ---

class MultimodalContent(BaseModel):
    type: str # e.g., "image_url", "image_base64", "document_url"
    content: str # URL or base64 encoded data or text content of document
    description: Optional[str] = None # Optional user description of the content

class UserTurnInput(BaseModel):
    text: Optional[str] = None
    multimodal_content: Optional[List[MultimodalContent]] = None
    timestamp: str # ISO format timestamp

# --- Intermediate Data Models ---

class ExtractedRequirement(BaseModel):
    category: str # e.g., "feature", "non_functional", "user_story", "data_model_idea", "ui_ux_note"
    description: str
    priority: Optional[int] = None # e.g., 1-5
    source_turn_id: Optional[str] = None # To trace back to user's input turn

class DialogueContext(BaseModel):
    session_id: str
    history: List[Dict[str, str]] # List of {"role": "user/agent", "content": "..."}
    current_extracted_requirements: List[ExtractedRequirement] = Field(default_factory=list)

# --- Output Data Models (Project Brief for MPA) ---

class FeatureDescription(BaseModel):
    id: str = Field(description="Unique ID for the feature")
    name: str
    description: str
    user_stories: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)

class DataModelElement(BaseModel):
    name: str
    attributes: Dict[str, str] # e.g., {"user_id": "integer", "username": "string"}
    relationships: Optional[List[str]] = None # e.g., ["User has many Posts"]

class NonFunctionalRequirement(BaseModel):
    category: str # e.g., "Performance", "Security", "Scalability", "Usability"
    requirement: str
    metric: Optional[str] = None # How it might be measured

class UIUXConsideration(BaseModel):
    element_description: str # e.g., "User dashboard", "Login page"
    notes: List[str]
    # Could include references to multimodal inputs if provided by user (e.g., sketch IDs)
    multimodal_references: Optional[List[str]] = None

class ProjectBrief(BaseModel):
    project_name: str = "Untitled SaaS Project"
    high_level_summary: str
    target_audience: Optional[str] = None

    features: List[FeatureDescription] = Field(default_factory=list)
    data_models_overview: List[DataModelElement] = Field(default_factory=list)
    non_functional_requirements: List[NonFunctionalRequirement] = Field(default_factory=list)
    ui_ux_considerations: List[UIUXConsideration] = Field(default_factory=list)

    raw_user_input_log: List[UserTurnInput] = Field(default_factory=list) # For traceability
    generation_timestamp: str

# --- Agent Communication Models (for presenting to user) ---

class UIMessage(BaseModel):
    message_type: str # e.g., "clarification_question", "info_update", "brief_summary", "error"
    text_content: str
    # Optional structured content for UIs that can render more than text
    structured_content: Optional[Dict[str, Any]] = None


if __name__ == '__main__':
    # Example Usage:

    # User Input
    turn1 = UserTurnInput(
        text="I want a blog platform.",
        timestamp="2025-01-01T10:00:00Z"
    )
    turn2 = UserTurnInput(
        text="Users should be able to register and create posts with rich text.",
        multimodal_content=[
            MultimodalContent(type="image_url", content="http://example.com/sketch.png", description="UI sketch for post editor")
        ],
        timestamp="2025-01-01T10:05:00Z"
    )
    # print("--- User Input Example ---")
    # print(turn1.model_dump_json(indent=2))
    # print(turn2.model_dump_json(indent=2))

    # Project Brief
    brief = ProjectBrief(
        project_name="My Awesome Blog",
        high_level_summary="A platform for users to create and share blog posts.",
        target_audience="General public, writers",
        features=[
            FeatureDescription(
                id="FEAT-001",
                name="User Registration",
                description="Allow users to create new accounts.",
                user_stories=["As a new user, I want to register so I can create posts."],
                acceptance_criteria=["User provides email and password.", "Account is created successfully."]
            ),
            FeatureDescription(
                id="FEAT-002",
                name="Create Post",
                description="Allow registered users to create new blog posts with rich text formatting.",
                user_stories=["As a registered user, I want to create a new post with a rich text editor."],
                acceptance_criteria=["Post has a title and body.", "Rich text formatting is saved."]
            )
        ],
        data_models_overview=[
            DataModelElement(name="User", attributes={"id": "int", "email": "str", "password_hash": "str"}),
            DataModelElement(name="Post", attributes={"id": "int", "user_id": "int", "title": "str", "body_text": "str", "created_at": "datetime"})
        ],
        non_functional_requirements=[
            NonFunctionalRequirement(category="Security", requirement="Passwords must be hashed.")
        ],
        ui_ux_considerations=[
            UIUXConsideration(element_description="Post Editor", notes=["Should support common rich text features like bold, italics, lists, images."], multimodal_references=["sketch.png"])
        ],
        raw_user_input_log=[turn1, turn2],
        generation_timestamp="2025-01-01T11:00:00Z"
    )
    # print("\n--- Project Brief Example ---")
    # print(brief.model_dump_json(indent=2))

    # UI Message
    ui_message = UIMessage(
        message_type="clarification_question",
        text_content="You mentioned rich text for posts. Are there any specific formatting options you consider essential (e.g., headings, code blocks, image uploads)?"
    )
    # print("\n--- UI Message Example ---")
    # print(ui_message.model_dump_json(indent=2))
    pass # Keep if __name__ == '__main__' block but do nothing for now
