# DESIGN DOCUMENT: OpenHands Orchestrator Agent Logic

## 1. Overview

This document outlines the design for the agent logic that runs within the `OpenHands` platform, referred to as the "OpenHands Orchestrator Agent" (or simply "Orchestrator Agent"). This agent is responsible for receiving high-level tasks from a user, decomposing them into a sequence of `open-codex`-like operations (the "open-codex-flow"), executing these operations using an `open_codex_lib` within the preconfigured `OpenHands` workspace, managing their execution, and presenting the final results.

The Orchestrator Agent leverages the user's specified LLM (via the `LLMInterface` configured in `OpenHands`) for its own decision-making (task decomposition, flow control) and for instructing the `open_codex_lib`.

## 2. Agent's Purpose and Activation

*   **Purpose:** To act as a user-facing intelligent agent within `OpenHands` that can autonomously perform complex coding and file manipulation tasks by orchestrating a series of more granular `open-codex` operations.
*   **Activation:**
    *   The user interacts with this agent via the `OpenHands` interface (UI or CLI/headless mode).
    *   The user provides a high-level task, e.g., "Refactor the `utils.py` file to make the `calculate_metrics` function more readable and add error handling for division by zero."

## 3. Configuration

The `OpenHands` environment itself will be configured to use the user's LLM:
*   **LLM Endpoint:** `https://lm.armand0e.online/v1`
*   **API Key:** `sk-291923902182902-kd`
*   **Model Name for Orchestrator's internal LLM calls:** `"gpt-3.5-turbo"` (alias for `devstral-small` on the user's endpoint).
*   **Model Name for `open_codex_lib` calls:** Also likely `"gpt-3.5-turbo"`, but this can be specified by the Orchestrator when it invokes `open_codex_lib`.

The `OpenHands` workspace is assumed to be the "Preconfigured Workspace for `open-codex-flow`" as per its design document, containing the `open_codex_lib` and necessary tools.

## 4. Core Logic & Workflow

The Orchestrator Agent's operation follows a general loop:

1.  **Task Reception & Understanding:**
    *   Receives a task from the user (e.g., a natural language string).
    *   **Internal LLM Call:** Uses its own LLM (`gpt-3.5-turbo`) to:
        *   Understand the user's intent.
        *   Identify the primary files/modules involved.
        *   Break down the high-level task into a potential sequence of `open-codex` operations (the "flow"). This is a critical planning step.
    *   Example Output: A structured plan, like a list of steps:
        ```json
        [
            {"operation": "read_file", "params": {"file_path": "utils.py"}, "id": "step1"},
            {"operation": "refactor_function", "params": {"file_path": "utils.py", "function_name": "calculate_metrics", "instructions": "improve readability, add div zero error handling"}, "depends_on": "step1", "id": "step2"},
            {"operation": "write_file", "params": {"file_path": "utils.py", "content_from_step": "step2"}, "depends_on": "step2", "id": "step3"},
            {"operation": "generate_summary", "params": {"changes_from_step": "step2"}, "id": "step4"}
        ]
        ```

2.  **Flow Execution (`open-codex-flow`):**
    *   Iterates through the planned steps.
    *   For each step:
        *   **Prepare `open_codex_lib` Invocation:**
            *   Create a dedicated temporary subdirectory within the `/workspace/<orchestrator_task_id>/` for this specific `open-codex` operation (e.g., `/workspace/task123/step2_refactor/`).
            *   Prepare input files (e.g., copy `utils.py` into the temp subdir).
            *   Create an `open_codex_instructions.md` file in the temp subdir with specific instructions for `open_codex_lib` based on the current step's operation and parameters.
        *   **Invoke `open_codex_lib`:**
            *   The Orchestrator Agent calls a function within the `open_codex_lib` (e.g., `result = open_codex_lib.execute_operation(instruction_file_path, llm_config)`).
            *   `llm_config` would pass the user's LLM endpoint, API key, and preferred model for this specific code generation/modification task.
            *   This call is blocking for the Orchestrator until `open_codex_lib` completes that operation.
        *   **Retrieve & Process Output:**
            *   `open_codex_lib` writes its output (e.g., modified files, logs, status) to its designated output area within its temp subdirectory.
            *   The Orchestrator Agent reads this output.
            *   If the current step depends on output from a previous step (e.g., `content_from_step`), the Orchestrator ensures this data is correctly passed.
        *   **Handle Errors:** If `open_codex_lib` reports an error for a step, the Orchestrator decides on a course of action (retry, skip, modify plan, report to user). This may involve another LLM call for diagnosis/correction strategy.

3.  **State Management:**
    *   The Orchestrator Agent maintains the state of the overall "flow" (e.g., which steps are pending, in-progress, completed, failed).
    *   This state could be stored in a JSON file within the `/workspace/<orchestrator_task_id>/` directory (e.g., `flow_status.json`).

4.  **Context Passing Between `open-codex` Operations:**
    *   Primarily file-based: The output files from one `open-codex` operation (e.g., a modified `utils.py`) become the input files for a subsequent operation. The Orchestrator manages this staging of files between temp subdirectories for each operation.
    *   Structured data (like a list of identified issues from an analysis step) can be passed by writing it to a JSON/text file that the next operation reads.

5.  **Result Aggregation & Presentation:**
    *   Once all steps in the flow are complete (or if the flow is halted due to errors):
        *   The Orchestrator Agent aggregates the final results (e.g., paths to modified files, a summary generated by a final `open_codex_lib` operation).
        *   It may use an LLM call to generate a user-friendly summary of what was done.
        *   Presents this summary and any key artifacts back to the user via the `OpenHands` interface.

## 5. `open_codex_lib` Interface (Conceptual)

The Orchestrator Agent expects `open_codex_lib` (available in the preconfigured workspace) to provide an interface like:

```python
# Conceptual interface for open_codex_lib
class OpenCodexLib:
    def execute_operation(self, instruction_file_path: str, llm_config: dict) -> dict:
        """
        Executes a single open-codex operation based on an instruction file.
        Args:
            instruction_file_path (str): Path to an .md file detailing the goal,
                                         input files, output expectations for this operation.
            llm_config (dict): Contains LLM endpoint, API key, model name.
        Returns:
            dict: A status dictionary, e.g.,
                  {"status": "success/failure", "output_files": ["path1", "path2"], "message": "..."}
        """
        # 1. Parse instruction_file_path
        # 2. Perform file operations (read inputs)
        # 3. Make LLM calls (using llm_config) for code gen/modification/analysis
        # 4. Apply changes (write outputs)
        # 5. Return status
        pass
```

## 6. Prompt Engineering for the Orchestrator Agent's LLM

The Orchestrator Agent's own LLM calls are primarily for planning and summarizing.

*   **Task Decomposition Prompt:**
    *   "You are an expert software development project manager. The user wants to achieve the following high-level task: '[USER TASK]'. The relevant files are initially [list of files, if any mentioned by user]. Break this down into a sequence of atomic operations that can be performed by an `open-codex` like tool. The available operations are: `read_file(file_path)`, `write_file(file_path, content)`, `modify_code(file_path, instructions_for_llm)`, `execute_shell_command(command)`, `analyze_code(file_path, analysis_query)`. For each operation, specify parameters and any dependencies on previous operations. Output as a JSON list of operation objects."
*   **Error Handling Prompt:**
    *   "An `open-codex` operation in a sequence failed. Step: [failed step details]. Error: [error message]. Previous steps: [summary]. Remaining steps: [summary]. What is a good strategy? Options: 1. Retry step. 2. Try an alternative operation. 3. Abort and report to user. 4. Suggest a modification to the failed step's instructions. Provide your recommendation and reasoning."
*   **Summarization Prompt:**
    *   "The following sequence of `open-codex` operations was completed: [log of operations and their outcomes]. Please provide a concise summary for the user explaining what was achieved and listing any key modified files."

## 7. Error Handling by Orchestrator

*   **`open_codex_lib` Operation Failure:**
    *   Log the error.
    *   Use LLM to diagnose or suggest a recovery strategy (see prompt above).
    *   Implement retry logic for transient errors.
    *   If unrecoverable, halt the flow for that task and report detailed error to the user.
*   **LLM Call Failures (Orchestrator's own calls):** Standard retry/error reporting.
*   **File I/O Errors within Orchestrator:** Report and halt.

## 8. Example Simple Flow: "Add a greeting to a file"

1.  **User Task:** "Create a file named `hello.py` and add a Python function called `greet` that prints 'Hello, OpenHands Orchestrator!'"
2.  **Orchestrator LLM (Planning):**
    ```json
    [
        {"operation": "write_file", "params": {"file_path": "hello.py", "content": "def greet():\n    print(\"Hello, OpenHands Orchestrator!\")\n"}, "id": "step1"},
        {"operation": "generate_summary", "params": {"message": "Created hello.py with greet function."}, "id": "step2"}
    ]
    ```
3.  **Orchestrator - Execute Step 1:**
    *   Creates `/workspace/<task_id>/step1_write/`
    *   Writes `open_codex_instructions.md`: "Goal: Create/overwrite `output/hello.py` with the following content: [content from plan]." (Simplified: `open_codex_lib` needs a specific way to get content for `write_file`).
    *   Calls `open_codex_lib.execute_operation(instruction_file_path, llm_config)` (LLM might not be strictly needed by `open_codex_lib` for a simple `write_file`).
    *   `open_codex_lib` creates `/workspace/<task_id>/step1_write/output/hello.py`.
    *   Orchestrator verifies, copies `/workspace/<task_id>/step1_write/output/hello.py` to `/workspace/<task_id>/final_output/hello.py`.
4.  **Orchestrator - Execute Step 2:**
    *   Calls `open_codex_lib` with instructions to generate a summary (this step might also be a simple string format by the orchestrator itself if the message is static).
5.  **Orchestrator - Report to User:** "Successfully created `hello.py` with a `greet` function."

## 9. Dependencies

*   **`OpenHands` Platform:** As the execution environment and user interface.
*   **Preconfigured Workspace:** Must contain `open_codex_lib` and all its dependencies.
*   **`LLMInterface`:** Configured within `OpenHands` for the user's LLM.
*   **`open_codex_lib`:** The Python library providing the core `open-codex` functionalities.

This design provides a starting point for the `OpenHands` Orchestrator Agent. The complexity will lie in the robustness of the task decomposition LLM prompts and the error handling strategies.
