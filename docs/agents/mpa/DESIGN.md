# DESIGN DOCUMENT: Module & API Design Agent (MPA)

## 1. Overview

The Module & API Design Agent (MPA), also referred to as the Master Planner Agent in initial concepts, is a critical component of the multi-agent SaaS development system. Its primary function is to take the user-validated "Project Brief" (produced by the UIBA) and transform it into a comprehensive technical blueprint for the application. This blueprint includes selecting the technology stack, defining the software architecture, designing modules and their corresponding APIs, and breaking down the overall project into actionable tasks for downstream development and QA agents.

The MPA acts as the chief architect and initial project manager, ensuring that the technical plan aligns with the user's requirements and follows sound engineering principles.

## 2. Role & Responsibilities

*   **Project Brief Analysis:** Ingest and thoroughly analyze the `ProjectBrief` provided by the UIBA via the Shared Knowledge Base (SKB).
*   **Technology Stack Selection:** Propose an appropriate technology stack (e.g., frontend framework, backend language/framework, database type) based on project requirements, complexity, scalability needs, and potentially pre-defined organizational preferences or best practices.
*   **Architectural Design:** Define the high-level software architecture (e.g., monolithic, microservices, serverless, event-driven). This includes identifying major components/modules and their interactions.
*   **Module Design:** Break down the application into logical modules, defining the scope and responsibilities of each.
*   **API Specification:** Design detailed API contracts for interactions between modules and for external interfaces. This includes defining endpoints, request/response formats, authentication/authorization mechanisms, and data schemas (likely using OpenAPI or a similar standard).
*   **Task Decomposition:** Decompose features and modules into smaller, actionable development tasks to be assigned to specialized agents (FDA, BDA, DMA, etc.). Define dependencies between tasks.
*   **Data Modeling (High-Level):** Refine the initial data model ideas from the `ProjectBrief` into a more formal database schema design, coordinating with the Database Management Agent (DMA).
*   **Prototype Generation (Conceptual):** As per the guiding document, rapidly create quick prototypes (e.g., code stubs, API mock servers, basic UI wireframes if `magistral-small` is leveraged) to test and validate design ideas.
*   **Feasibility Checks:** Interact with other agents (e.g., FDA, IDA) to validate the feasibility of certain design choices or technology selections.
*   **Documentation:** Store all generated artifacts (Tech Stack Document, Architecture Document, API Specifications, Task List, Data Schema) in the SKB.

## 3. Core Logic & Operations

### 3.1. Workflow:

1.  **Activation:** The MPA is activated when a new, validated `ProjectBrief` is available in the SKB (notification likely from UIBA or the Orchestrator).
2.  **Brief Ingestion:** Retrieves and parses the `ProjectBrief` from the SKB.
3.  **Analysis & Initial Planning (LLM-driven):**
    *   Constructs a series of prompts for an LLM (e.g., `devstral-small`) to analyze the brief.
    *   **Tech Stack Selection:** Prompts the LLM to recommend a tech stack, possibly providing it with a list of preferred/supported technologies or constraints.
    *   **Architecture Design:** Prompts the LLM to propose a suitable architecture, outlining key components and reasoning. May use ToT prompting to explore options.
    *   **Module Identification:** Prompts the LLM to identify logical modules based on features in the brief.
4.  **Detailed API Design (LLM-driven, iterative):**
    *   For each module/feature interaction, prompts the LLM to define API endpoints, request/response payloads (JSON schema), HTTP methods, and status codes.
    *   This may be an iterative process, refining API designs based on consistency checks or simulated interactions.
    *   Aims to produce an OpenAPI (Swagger) specification.
5.  **Data Schema Design (Collaboration with DMA):**
    *   Refines data model ideas from the brief.
    *   Generates a logical data schema.
    *   May create tasks for the DMA to formalize and implement this schema.
6.  **Task Decomposition (LLM-driven):**
    *   For each feature in the `ProjectBrief`, prompts the LLM to break it down into:
        *   Backend tasks (API implementation, logic).
        *   Frontend tasks (UI component development, API integration).
        *   Database tasks (schema changes, query development - often via DMA).
        *   Testing tasks (unit, integration - for QATA).
    *   Defines dependencies between these tasks.
7.  **Prototyping (Optional/Iterative):**
    *   If necessary, MPA instructs an appropriate agent (e.g., FDA for code stubs, or uses its own LLM call with specific code-generation prompts) to create minimal prototypes for high-risk areas to validate design choices.
8.  **Storing Artifacts:** All generated design documents (Tech Stack, Architecture, API Specs, Task List, Data Schema) are stored in the SKB with clear versioning and linkage to the original `ProjectBrief`.
9.  **Handover to Orchestrator:** Notifies the main Orchestrator that planning is complete and development tasks are ready for assignment.

### 3.2. Key Internal Components:

*   **`MPAAgent` Class (e.g., `mpa_core.py` - to be created):** Orchestrates MPA functionalities.
*   **`LLMInterface` (shared):** For interactions with `devstral-small`.
*   **Data Models (e.g., `mpa_data_models.py` - to be created):** For `ProjectPlan`, `APISpecification`, `TaskDefinition`.

## 4. Data Structures

*   **Input:**
    *   `ProjectBrief` (from UIBA via SKB).
*   **Internal State:**
    *   Current analysis of the brief.
    *   Drafts of architecture, tech stack, API designs.
    *   List of decomposed tasks.
*   **Output (stored in SKB):**
    *   **`TechnologyStackDocument`**: Specifies chosen languages, frameworks, libraries, databases.
        *   Example: `{"frontend": "React 20.x", "backend": "Python 3.11 + FastAPI 0.100.x", "database": "PostgreSQL 15"}`
    *   **`ArchitectureDocument`**: Describes the high-level architecture, components, modules, and their interactions (could include diagrams if `magistral-small` is used for generation, or textual descriptions).
    *   **`APISpecification`**: Detailed API contracts, likely in OpenAPI (JSON/YAML) format.
    *   **`TaskList`**: A structured list of tasks for other agents, including descriptions, dependencies, assigned agent type (FDA, BDA etc.), and estimated effort/complexity (LLM generated).
        *   Example Task: `{"task_id": "MPA-T001", "description": "Implement user registration API endpoint", "assigned_to_type": "FDA", "depends_on": [], "inputs": ["ProjectBrief.features.UserRegistration", "APISpec.auth_endpoints"], "outputs": ["Implemented API code", "Unit tests"]}`
    *   **`DataSchemaDefinition`**: Logical data schema, possibly DDL-like or a structured format.

## 5. API and Interaction Points

*   **UIBA (via SKB):**
    *   **Reads:** `ProjectBrief` from SKB.
*   **Shared Knowledge Base (SKB):**
    *   **Writes:** `TechnologyStackDocument`, `ArchitectureDocument`, `APISpecification`, `TaskList`, `DataSchemaDefinition`.
    *   **Reads:** `ProjectBrief`, potentially existing architectural patterns, best practices, or templates stored in SKB.
*   **Development Agents (FDA, BDA, DMA, etc. via Orchestrator & SKB):**
    *   MPA makes tasks available (e.g., by updating their status in SKB or on a task board). The Orchestrator then assigns these to available agents.
*   **Orchestrator:**
    *   Receives notification from UIBA/Orchestrator when a `ProjectBrief` is ready.
    *   Notifies Orchestrator when planning is complete and tasks are defined.
*   **LLM Service (via `LLMInterface`):**
    *   Extensive interaction for analysis, design generation, and task decomposition using `devstral-small`.

## 6. Prompt Engineering Strategies (High-Level)

Leveraging Section 4 of the user-provided comprehensive document:

*   **System Prompts:** Define MPA's role as an expert software architect and planner. Instruct it to be thorough, consider best practices, and output structured information (e.g., JSON for task lists, YAML for API specs if generated directly).
*   **Decomposition Prompting (DECOMP & Plan-and-Solve):**
    *   Crucial for breaking down the `ProjectBrief` into an architectural plan, then into modules, then into API specs, and finally into implementable tasks.
    *   **PS Prompting:** MPA will first generate a high-level plan (e.g., "1. Define Tech Stack, 2. Design Core Architecture, 3. Detail APIs for X, Y, Z modules, 4. Decompose features A, B, C into tasks") before diving into each step.
*   **Chain-of-Thought (CoT) Prompting:**
    *   Used within each major planning step (tech stack selection, architecture design) to ensure the LLM "thinks through" options, pros/cons, and justifications. For example: "To select the tech stack for a project with requirements X, Y, Z, let's think step by step. First, consider frontend needs... Second, backend needs... Third, database options..."
*   **Tree of Thought (ToT) Prompting (Conceptual):**
    *   For critical architectural decisions, MPA could use ToT to explore multiple design alternatives (e.g., microservices vs. monolith, different database types), evaluating each path before settling on a recommendation. This requires more complex interaction with the LLM.
*   **Few-shot Prompting:** Provide examples of good API design, task decomposition for similar features, or architectural pattern descriptions to guide the LLM. These examples could be stored in the SKB.
*   **Reflexion Prompting (Conceptual):** After drafting an initial architecture or API spec, MPA could use an LLM call to critique its own design: "Review the following API design for completeness, consistency, and adherence to REST principles. Identify any potential issues."

## 7. Error Handling & Edge Cases

*   **Incomplete/Ambiguous `ProjectBrief`:** If the brief from UIBA is insufficient, MPA should flag these areas and potentially request UIBA to re-engage the user for clarification (or the Orchestrator handles this loop).
*   **Contradictory Requirements:** Identify contradictions in the brief and attempt to resolve them or flag them for clarification.
*   **LLM Fails to Generate Sensible Design:** Retry with modified prompts, different CoT paths, or simplified sub-problems. If persistent, escalate to an error state (human review needed).
*   **Infeasible Design Choices:** If a proposed design is deemed infeasible (e.g., a chosen technology doesn't support a critical feature), MPA needs to backtrack and explore alternatives. This is where iterative refinement and potentially ToT are useful.
*   **Task Generation Issues:** Ensure generated tasks are well-defined, actionable, and have clear dependencies.

## 8. Dependencies

*   **Internal:**
    *   UIBA: Provides the `ProjectBrief`.
    *   `LLMInterface`: For all LLM interactions.
    *   `SharedKnowledgeBaseClient`: For reading the brief and storing all design artifacts.
    *   Orchestrator: For activation and task handover.
    *   Other specialized agents (FDA, DMA, etc.): For potential feasibility checks (though this is more an interaction than a hard dependency for initial design).
*   **External:**
    *   `LocalAI` server running with `devstral-small`.
    *   Python libraries (e.g., for OpenAPI generation if not directly from LLM, Pydantic for its own data models).

## 9. Future Considerations / Enhancements

*   **Automated Feasibility Analysis:** Deeper integration with development agents during the planning phase to get early feedback on the complexity or feasibility of proposed designs.
*   **Cost/Effort Estimation:** LLM-driven estimation of development effort for generated tasks.
*   **Security by Design:** Incorporating security considerations and threat modeling into the architectural design phase.
*   **Scalability & Performance Modeling:** Early-stage analysis of potential performance bottlenecks or scalability issues based on the architecture.
*   **Visual Architecture Generation:** Using `magistral-small` (if capable) to generate diagrams (component diagrams, sequence diagrams) as part of the `ArchitectureDocument`.

This document outlines the design for the MPA, which plays a pivotal role in translating user needs into a concrete technical plan.
