# Running the OpenHands Orchestrator Agent

This guide explains how to launch and interact with the `OpenHands` instance configured to act as an Orchestrator Agent for `open-codex-flow` operations.

## Prerequisites

1.  **Docker Installed:** Ensure Docker is installed and running on your system.
2.  **API Credentials (Optional but Recommended):** While the script has default credentials for the user-provided LLM endpoint, it's best to set them as environment variables for security:
    *   `export OH_USER_LLM_BASE_URL="https://lm.armand0e.online/v1"`
    *   `export OH_USER_LLM_API_KEY="sk-291923902182902-kd"`
    The script will use these environment variables if set; otherwise, it falls back to the hardcoded defaults (which should be changed for actual use).
3.  **Script Executable:** Make sure the launch script is executable:
    ```bash
    chmod +x scripts/launch_openhands_orchestrator.sh
    ```

## Launching the Orchestrator Agent

1.  Navigate to the `scripts` directory in your terminal:
    ```bash
    cd scripts
    ```
2.  Run the launch script:
    ```bash
    ./launch_openhands_orchestrator.sh
    ```
3.  The script will:
    *   Clean up any previous instances of the `OpenHands` container.
    *   Prepare a settings file (`~/.openhands-orchestrator-state/settings.json`) configured with the LLM details and the custom instructions that make the `OpenHands` agent behave as our orchestrator.
    *   Pull the necessary `OpenHands` Docker images.
    *   Launch the `OpenHands` container in detached mode.
4.  On successful launch, the script will output:
    *   The URL to access the `OpenHands` Web UI (usually `http://localhost:3000`).
    *   Commands to view logs (`docker logs -f openhands-orchestrator-instance`) and stop the container (`docker stop openhands-orchestrator-instance`).

## Interacting with the Orchestrator Agent

1.  Open your web browser and navigate to `http://localhost:3000` (or the port specified by the script).
2.  You should be greeted by the `OpenHands` interface. The agent running here is now primed with the "Orchestrator Agent" instructions.
3.  Provide a high-level task that involves code or file manipulation. Refer to the example below.

## Testing with the Simple Flow Example

A conceptual test case is documented in `docs/examples/SIMPLE_FLOW_EXAMPLE.md`. To try this:

1.  **After launching `OpenHands` as described above, you need to manually create the `input.txt` file within the `OpenHands` workspace.**
    *   How you do this depends on how you've configured `OpenHands` workspace access. If you haven't mapped a host directory to `/workspace` in the launch script (the default for the current script), you might need to use the `OpenHands` UI itself to create `/workspace/input.txt` and add content to it, or use `docker exec` to get into the container.
    *   A simpler approach for testing would be to modify `scripts/launch_openhands_orchestrator.sh` to mount a local directory to `/workspace`. For example, create `./orchestrator_workspace` in your project root, put `input.txt` there, and uncomment/modify the `WORKSPACE_MOUNT_CMD` in the script:
        ```bash
        # HOST_WORKSPACE_DIR="$PWD/../orchestrator_workspace" # Assuming script is run from scripts/
        # CONTAINER_WORKSPACE_DIR="/workspace"
        # WORKSPACE_MOUNT_CMD="-v "$HOST_WORKSPACE_DIR":"$CONTAINER_WORKSPACE_DIR""
        ```
        Then, before running the script, create `orchestrator_workspace/input.txt` with:
        ```
        apple
        banana
        cherry
        date
        ```
2.  **Provide the Task:** In the `OpenHands` UI chat input, give the agent the task:
    ```
    I have a file named `input.txt` in the root of the workspace. It contains a list of fruits, one per line. Please create a new file named `output.txt` in the root of the workspace, containing the same fruits but all in uppercase.
    ```
3.  **Observe Behavior:**
    *   The Orchestrator Agent should (as per its custom instructions and the example flow):
        *   Potentially use its LLM to understand and plan the task (e.g., into steps: read input, transform content, write output, summarize).
        *   It might present this plan to you for confirmation.
        *   It will then attempt to execute these steps using its built-in capabilities (file I/O, LLM calls to simulate transformations, as `open_codex_lib` is not yet a concrete, callable library within the sandbox).
        *   It should create `/workspace/output.txt` with the uppercased content.
        *   Finally, it should report completion.

## Important Considerations

*   **`open_codex_lib` Simulation:** The current `custom_instructions` for the Orchestrator Agent describe how it should *conceptually* use an `open_codex_lib`. Since this library is not yet implemented and integrated into the sandbox, the agent will use its own LLM and `OpenHands`'s native tools (file system access, command execution) to achieve the sub-steps of its plan. The effectiveness will depend on the base `OpenHands` agent's ability to interpret these parts of the instructions.
*   **LLM Capabilities:** The success of the planning and execution heavily relies on the `devstral-small` model (accessed via the `gpt-3.5-turbo` alias on your server) to understand the orchestration instructions and perform the decomposition and sub-task reasoning.
*   **Workspace Access:** Be mindful of how files are being accessed and written. If you map a local host directory to `/workspace`, changes made by the agent will be reflected on your host system.

This setup provides a testbed for the concept of using `OpenHands` as an orchestrator for more granular, `open-codex`-like operations.
