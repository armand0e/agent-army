# DESIGN DOCUMENT: User Interaction & Briefing Agent (UIBA)

## 1. Overview

The User Interaction & Briefing Agent (UIBA) serves as the primary interface between human users and the multi-agent SaaS development system. Its core purpose is to effectively gather, interpret, and clarify user requirements for a desired SaaS application, and then translate these requirements into a structured "Project Brief" that can be utilized by the Master Planner Agent (MPA) and other downstream agents.

The UIBA aims to provide a natural, intuitive, and efficient interaction experience for the user, capable of handling textual and potentially multimodal inputs.

## 2. Role & Responsibilities

*   **User Interaction:** Act as the conversational frontend for the system, engaging users to understand their needs.
*   **Requirements Elicitation:** Proactively ask clarifying questions to resolve ambiguities and elicit detailed information about desired features, target audience, data aspects, UI/UX preferences, and non-functional requirements.
*   **Input Processing:** Process user inputs, which may include text, and in future iterations, speech, diagrams, or UI sketches/screenshots.
*   **Requirement Structuring:** Convert unstructured user inputs into a well-defined, structured `ProjectBrief` (defined in `uiba_agent.data_models.ProjectBrief`).
*   **Dialogue Management:** Maintain conversation context and history to ensure coherent and relevant interactions.
*   **User Feedback & Presentation:** Present interim summaries, clarifications, and the final Project Brief back to the user for validation and confirmation.
*   **Handover to MPA:** Store the finalized Project Brief in the Shared Knowledge Base (SKB) and notify the MPA (or orchestrator) that a new brief is ready.

## 3. Core Logic & Operations

The UIBA operates through a cycle of receiving input, processing it (often involving LLM interaction), updating its internal state (dialogue history, current understanding of requirements), and generating a response or action.

### 3.1. Interaction Flow:

1.  **Initiation:** UIBA starts a new session, typically with a greeting and an open-ended question to elicit the user's initial request.
2.  **Input Handling:**
    *   Receives `UserTurnInput` (text and optional multimodal content).
    *   Appends user input to the dialogue history.
    *   Logs raw input to the `ProjectBrief.raw_user_input_log`.
3.  **Interpretation & Information Extraction:**
    *   Constructs a prompt for an LLM (e.g., `devstral-small` via `LLMInterface`) using the current user input and relevant dialogue history.
    *   The prompt instructs the LLM to extract key information related to the `ProjectBrief` fields (project name, summary, features, data models, NFRs, UI/UX notes) and to identify areas needing clarification. The LLM should be prompted to return this in a structured JSON format.
    *   (Future: For multimodal input, `magistral-small` would be used. The content might be pre-processed, e.g., images converted to a format the LLM can understand, or descriptions generated).
4.  **Updating Brief Ideas:**
    *   The structured JSON output from the LLM is parsed.
    *   The `UIBAgent.current_project_brief_ideas` (an internal dictionary mirroring `ProjectBrief` structure) is updated with the new information.
    *   Individual `ExtractedRequirement` objects are logged.
5.  **Response Generation / Next Action Decision:**
    *   Based on the current state of `current_project_brief_ideas` and the LLM's interpretation (e.g., if the LLM suggested clarification questions), UIBA formulates its next response.
    *   This typically involves another LLM call, prompted to:
        *   Ask clarifying questions.
        *   Confirm understanding of a specific point.
        *   Prompt for more details in a specific area.
        *   Offer to summarize gathered information.
    *   The response is formatted as a `UIMessage`.
6.  **Iteration:** Steps 2-5 repeat until the user indicates they have provided all necessary information, or UIBA determines the brief is sufficiently complete.
7.  **Project Brief Generation:**
    *   User can explicitly request brief generation (e.g., via `--generate_brief` in the CLI version), or UIBA/orchestrator can trigger it.
    *   `UIBAgent.generate_project_brief()` is called. This might involve a final LLM call to synthesize and structure all `current_project_brief_ideas` into a coherent `ProjectBrief` Pydantic model.
8.  **Presentation & Storage:**
    *   The generated `ProjectBrief` is presented to the user for review (optional step, or summary presented).
    *   `UIBAgent.store_project_brief()` saves the `ProjectBrief` to the Shared Knowledge Base.

### 3.2. Key Internal Components (Code Reference):

*   **`UIBAgent` Class (`uiba_core.py`):** Orchestrates all UIBA functionalities.
*   **`LLMInterface` (`llm_interface.py`):** Handles all communication with the LocalAI-served LLMs.
*   **Data Models (`data_models.py`):** Defines `UserTurnInput`, `ProjectBrief`, `UIMessage`, etc., using Pydantic.

## 4. Data Structures

The primary data structures managed and produced by UIBA are defined in `src/agentic_saas_system/uiba_agent/data_models.py`.

*   **Input:** `UserTurnInput` (capturing text and multimodal content).
*   **Internal State:**
    *   `dialogue_history`: List of conversation turns.
    *   `current_project_brief_ideas`: A dictionary that accumulates information, mirroring the structure of the `ProjectBrief`.
    *   `extracted_requirements_log`: A list of `ExtractedRequirement` objects.
*   **Output:** `ProjectBrief` (a Pydantic model containing all structured requirements).
*   **Communication with User:** `UIMessage` (for text and potential structured UI content).

## 5. API and Interaction Points

*   **User Interface:**
    *   Receives input from the user (text, potentially files/images in a richer UI).
    *   Sends messages (`UIMessage`) back to the user.
    *   The `uiba_agent/main.py` provides a basic CLI for this interaction. A more sophisticated UI (e.g., integrated into OpenHands) would use the `UIBAgent` class methods.
*   **LLM Service (via `LLMInterface`):**
    *   Sends prompts (constructed message lists).
    *   Receives completions (text, or JSON strings).
    *   Target LLMs: `devstral-small` for text processing and structuring, `magistral-small` for multimodal aspects, served by LocalAI.
*   **Shared Knowledge Base (SKB) (via `SharedKnowledgeBaseClient`):**
    *   **Writes:** Stores the finalized `ProjectBrief` document.
    *   **Reads:** (Potentially) Reads user profiles, past project templates, or other contextual information if available and relevant.
*   **Master Planner Agent (MPA) / Orchestrator:**
    *   **Output to MPA:** The `ProjectBrief` stored in the SKB serves as the primary handover.
    *   **Trigger:** UIBA (or the orchestrator) signals the MPA when a new brief is ready.
    *   **Input from Orchestrator/Other Agents:** May receive requests to present system status or messages from other agents to the user. This would likely be through a dedicated method in `UIBAgent` called by the orchestrator.

## 6. Prompt Engineering Strategies (High-Level)

Effective interaction with LLMs is crucial for UIBA. Strategies will be based on Section 4 of the user-provided comprehensive document.

*   **System Prompts:**
    *   For interpretation: Define UIBA's role as an expert requirements gatherer, specify the desired JSON output structure, and instruct it to ask clarifying questions if needed.
    *   For response generation: Define UIBA's persona (helpful, friendly, concise) and the types of responses it should generate (clarifications, confirmations, prompts for more info).
*   **Chain-of-Thought (CoT):**
    *   **Zero-shot CoT:** Appending "Let's think step-by-step" or similar phrases to prompts for complex interpretation or when deciding on clarification questions. For example, when a user provides a vague feature, UIBA's internal LLM call might use CoT to break down what's missing before formulating a question to the user.
*   **Decomposition Prompting:**
    *   The process of filling out the `ProjectBrief` is inherently a decomposition of the user's high-level request into structured parts. Prompts will guide the LLM to fill these parts.
*   **Reflexion Prompting (Conceptual):**
    *   Before presenting a summary or asking a critical clarifying question, UIBA could internally prompt the LLM to review the current dialogue and the formulated question/summary for clarity, completeness, and relevance.
*   **Context Management:**
    *   Include relevant portions of the `dialogue_history` and `current_project_brief_ideas` in prompts to provide context to the LLM.
    *   Careful management to avoid exceeding token limits. Summarization techniques might be needed for very long conversations.
*   **JSON Mode:** Utilize LLM's JSON output mode for structured information extraction to directly populate `ProjectBrief` fields or `ExtractedRequirement` objects.

## 7. Error Handling & Edge Cases

*   **LLM Unavailability:** `LLMInterface` should handle timeouts or connection errors to LocalAI. UIBA should inform the user if it cannot currently process their request.
*   **Invalid LLM Output:** If the LLM fails to produce valid JSON (when expected) or provides irrelevant information:
    *   Retry the request, possibly with a modified prompt.
    *   Ask the user to rephrase their input.
    *   Log the error.
*   **Ambiguous User Input:** The core dialogue loop is designed to handle this by prompting for clarification. The LLM plays a key role in identifying ambiguities.
*   **User Wants to End Interaction Prematurely:** Handle "exit" or "quit" commands gracefully.
*   **No Information Provided:** If the user tries to generate a brief without providing input, UIBA should indicate this.
*   **SKB Unavailability:** If the `SharedKnowledgeBaseClient` fails to store the brief, UIBA should inform the user and log the error. The brief might be temporarily held or the user asked to retry later.

## 8. Dependencies

*   **Internal:**
    *   `llm_interface.py`: For all LLM interactions.
    *   `data_models.py`: For structuring all data.
    *   `SharedKnowledgeBaseClient` (conceptual): For storing the `ProjectBrief`.
    *   Main Orchestrator: For triggering UIBA and receiving notifications.
*   **External:**
    *   `LocalAI` server running with `devstral-small` and (future) `magistral-small` models.
    *   Python libraries: `pydantic`, `httpx`.
    *   (Potentially) A UI framework if not run via CLI.

## 9. Future Considerations / Enhancements

*   **Full Multimodal Input:** True processing of image/diagram content beyond simple textual descriptions.
*   **Speech-to-Text and Text-to-Speech:** For voice interactions.
*   **User Profiles:** Store and retrieve user preferences or past interaction styles.
*   **Proactive Suggestions:** Based on common SaaS patterns, UIBA could suggest features the user hasn't thought of.
*   **Integration with Design Tools:** Directly ingesting content from tools like Figma.
*   **More Sophisticated Dialogue State Tracking:** Using more formal dialogue state management techniques.

This document provides the initial design for the UIBA. It will evolve as the other components of the agentic system are designed and implemented.
