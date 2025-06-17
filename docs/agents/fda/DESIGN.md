# DESIGN DOCUMENT: Feature Development Agent (FDA)

## 1. Overview

The Feature Development Agent (FDA) is a core component of the multi-agent SaaS development system responsible for writing the actual source code for application features. It takes detailed task definitions, module designs, and API specifications from the Module & API Design Agent (MPA) and translates them into functional frontend and backend code.

The FDA operates within the `OpenHands` execution environment, leveraging Large Language Models (specifically `devstral-small` via `LocalAI`) for code generation and integrating principles from `ymichael/open-codex` for precise code manipulation, file system operations, and sandboxed execution of snippets or build commands.

## 2. Role & Responsibilities

*   **Code Implementation:** Write source code for both frontend and backend components as per specifications. This includes UI elements, business logic, API client code (for frontend), and API endpoint implementation (for backend).
*   **Task Interpretation:** Understand and implement tasks assigned by the MPA, including feature requirements, function signatures, and interaction patterns.
*   **Adherence to Design:** Follow architectural guidelines, API specifications, and coding standards defined by the MPA or global configuration.
*   **Unit Test Stub Generation:** Generate basic unit test stubs or simple tests for the code it produces, to be fleshed out or executed by the QATA.
*   **Version Control:** Commit implemented features and changes to a version control system (e.g., Git) in a structured manner (e.g., feature branches).
*   **Dependency Management:** Identify and declare necessary libraries or dependencies for the code it writes (e.g., updating `requirements.txt` or `package.json`).
*   **Iterative Refinement:** Refine generated code based on feedback from linters, build tools, the Bug Detection & Debugging Agent (BDA), or the Quality Assurance & Testing Agent (QATA).

## 3. Core Logic & Operations

### 3.1. Workflow (per task):

1.  **Task Acquisition:** Receives a task definition from the MPA/Orchestrator (e.g., "Implement POST /api/users endpoint" or "Create React component for user login form"). The task includes references to relevant API specs, data models, and UI mockups from the SKB.
2.  **Context Gathering:** Retrieves necessary context from the SKB, such as:
    *   Detailed API specification for the endpoint/module.
    *   Data model definitions.
    *   Relevant existing codebase (e.g., utility functions, base classes).
    *   Coding standards and preferred libraries from the `TechnologyStackDocument`.
3.  **Code Generation (Iterative LLM Interaction):**
    *   Constructs detailed prompts for `devstral-small` (via `LLMInterface`) to generate code for the specific function, class, module, or component.
    *   Prompts will include:
        *   The function/method signature.
        *   Input/output specifications.
        *   Relevant data structures.
        *   Brief description of the logic to be implemented.
        *   Existing surrounding code (if modifying a file).
        *   Instructions to adhere to the project's language and framework.
    *   The FDA may break down complex generation tasks into smaller LLM calls (e.g., generate function body, then generate error handling, then generate comments).
    *   **Diff Application (Open Codex Principle):** For modifications to existing files, the FDA may prompt the LLM to return a diff, which is then applied to the local file. This allows for more controlled changes.
4.  **File Manipulation (OpenHands & Open Codex Principle):**
    *   Uses `OpenHands` capabilities (or integrated `open-codex` logic) to:
        *   Create new files.
        *   Read existing files to provide context to the LLM.
        *   Write or patch generated code into the appropriate files in the workspace.
5.  **Basic Validation & Linting:**
    *   After code generation, the FDA may trigger linters or basic build commands (e.g., `npm run build` for frontend, `python -m compileall` for backend) within the `OpenHands` sandboxed environment to catch syntax errors or obvious issues.
    *   Feedback from these tools can be used to prompt the LLM for corrections (iterative refinement).
6.  **Unit Test Stub Generation:**
    *   Prompts the LLM to generate boilerplate for unit tests relevant to the implemented code.
7.  **Dependency Update:**
    *   If new libraries are used, prompts the LLM to generate commands to add them (e.g., `npm install <package>` or `poetry add <package>`) and to update dependency files. These commands are then run via `OpenHands`.
8.  **Version Control:**
    *   Stages changes.
    *   Prompts the LLM to generate a concise commit message.
    *   Commits the code to the appropriate feature branch.
9.  **Status Update:** Reports task completion (or issues encountered) to the MPA/Orchestrator and updates the task status in the SKB.

### 3.2. Key Internal Components:

*   **`FDAgent` Class (e.g., `fda_core.py` - to be created):** Manages the FDA's workflow.
*   **`LLMInterface` (shared):** For code generation and related queries.
*   **File System Tool (via `OpenHands` or adapted `open-codex`):** For reading, writing, patching files.
*   **Command Execution Tool (via `OpenHands`):** For running linters, build tools, test stubs, VCS commands.
*   **Code Parsing/AST Utilities (Optional):** For more advanced code understanding or manipulation, though primarily relying on LLM for this.

## 4. Data Structures

*   **Input:**
    *   `TaskDefinition` (from MPA via SKB): Describes the feature/function to implement, inputs, outputs, dependencies, references to API specs, and data models.
    *   `APISpecification` (from SKB).
    *   `DataSchemaDefinition` (from SKB).
    *   Relevant existing source code files.
*   **Internal State:**
    *   Current code being worked on.
    *   LLM conversation history for the current task.
    *   Feedback from linters/build tools.
*   **Output:**
    *   New or modified **source code files** (e.g., `.py`, `.js`, `.tsx`, `.html`, `.css`).
    *   Basic **unit test files**.
    *   Updated **dependency files** (e.g., `requirements.txt`, `package.json`).
    *   **Commit messages**.
    *   Status updates to the Orchestrator/SKB.

## 5. API and Interaction Points

*   **MPA / Orchestrator (via SKB & Message Bus/API):**
    *   **Receives:** `TaskDefinition` objects.
    *   **Sends:** Task completion status, encountered issues, requests for clarification on specs.
*   **Shared Knowledge Base (SKB):**
    *   **Reads:** `TaskDefinition`, `APISpecification`, `DataSchemaDefinition`, `TechnologyStackDocument`, coding standards, existing relevant code.
    *   **Writes:** (Potentially) Pointers to new/modified code in VCS, status of code generation.
*   **LLM Service (`devstral-small` via `LLMInterface`):**
    *   Sends detailed prompts for code generation, explanation, diff creation, commit message generation.
    *   Receives generated code, diffs, text.
*   **Version Control System (e.g., Git, via `OpenHands` command execution):**
    *   Commits code, creates branches, etc.
*   **Bug Detection & Debugging Agent (BDA):**
    *   If FDA's initial code has issues identified by basic checks or later by QATA, the task might be refined or passed to BDA for detailed debugging. FDA would then receive corrected code or suggestions from BDA.
*   **Quality Assurance & Testing Agent (QATA):**
    *   Hands over implemented code and unit test stubs for comprehensive testing.
    *   Receives detailed test failure reports from QATA, which trigger refinement cycles.
*   **OpenHands Environment:**
    *   Provides file system access, sandboxed command execution, and potentially other tools.

## 6. Prompt Engineering Strategies for Code Generation

Based on Section 4 of the user-provided comprehensive document and general best practices:

*   **Role-Specific System Prompts:** "You are an expert [Frontend/Backend] developer proficient in [Language/Framework from Tech Stack]. Your task is to implement the following [function/class/component]..."
*   **Clear Task Definition in Prompt:** Include:
    *   Function/class/component name.
    *   Expected input parameters (names, types, descriptions).
    *   Expected output/return value (type, description).
    *   Detailed description of the logic to be implemented.
    *   Relevant data models or API schemas.
*   **Few-Shot Examples:** Provide examples of similar well-written code snippets from the existing codebase or style guide, especially for complex patterns or framework-specific idioms.
*   **Contextual Code:** Include surrounding code (e.g., the class definition if implementing a method, imports if adding to a file) to help the LLM maintain context and consistency.
*   **Iterative Prompts:**
    *   First, ask for the core logic.
    *   Then, ask for error handling.
    *   Then, ask for comments or documentation strings.
    *   Then, ask for unit test stubs.
*   **Requesting Specific Formats:**
    *   Ask for code within specific delimiters (e.g., Markdown code blocks with language identifiers).
    *   Ask for diffs when modifying existing code.
*   **Reflexion for Code:** After initial generation, use a follow-up prompt: "Review the code you just wrote for correctness, adherence to [language/project] best practices, and potential bugs. Suggest improvements or provide a revised version."
*   **Program-of-Thoughts (PoT) for Complex Logic:** If the logic is complex, prompt the LLM to first outline the steps in pseudocode or as comments within the code structure, then fill in the implementation.

## 7. Error Handling & Edge Cases

*   **Compilation/Syntax Errors in Generated Code:**
    *   Capture stderr from build tools/linters.
    *   Feed the error message back to the LLM along with the problematic code and ask for a fix. Repeat a few times.
*   **LLM Produces Incomplete or Irrelevant Code:**
    *   Retry with a more specific prompt or break the task down further.
    *   If the LLM seems "stuck," try a slightly different phrasing or ask for a different approach.
*   **Failure to Apply Diff:** If a generated diff doesn't apply cleanly, revert and request a new diff or full code block from the LLM.
*   **Task Specification Ambiguity:** If the task from MPA is unclear, FDA should flag this and request clarification from MPA (via Orchestrator).
*   **Dependency Conflicts:** If adding a new library causes conflicts, this needs to be flagged. (More advanced: LLM could be asked to suggest solutions to dependency issues).
*   **VCS Errors:** Handle errors during commit (e.g., merge conflicts, though FDA should ideally work on clean feature branches).

## 8. Dependencies

*   **Internal:**
    *   MPA: Provides `TaskDefinition`, `APISpecification`, `DataSchemaDefinition`.
    *   `LLMInterface`: For LLM communication.
    *   `SharedKnowledgeBaseClient`: To fetch context and specifications.
    *   Orchestrator: For task assignment and status reporting.
    *   BDA/QATA: For feedback and iterative refinement.
    *   `OpenHands` environment: For file operations and command execution.
    *   (Conceptual) `open-codex` logic: For sandboxed execution, precise file patching.
*   **External:**
    *   `LocalAI` server with `devstral-small`.
    *   Version Control System (e.g., Git executable).
    *   Relevant language/framework toolchains (Node.js, Python, Java, etc.) available within the `OpenHands` execution sandbox.

## 9. Future Considerations / Enhancements

*   **Automated Code Optimization:** FDA could prompt LLMs to optimize generated code for performance or readability based on specific metrics or guidelines.
*   **Security Vulnerability Scanning:** Integrate tools to scan generated code for common vulnerabilities and prompt LLM for fixes.
*   **More Sophisticated Scaffolding:** Generate entire project structures or modules based on high-level descriptions from MPA.
*   **Self-Correction based on QATA Feedback:** Deeper integration where FDA directly uses detailed QATA reports to guide LLM-driven code corrections without needing BDA for all issues.
*   **Understanding Existing Complex Codebases:** Enhancing FDA's ability to understand and safely modify large, existing codebases, not just generate new code.

This document outlines the design for the FDA, the primary code-writing agent in the system.
