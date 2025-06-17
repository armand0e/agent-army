# Test Walkthrough: Dev Container Setup & Basic Orchestrator Interaction

## 1. Purpose

This document provides a conceptual walkthrough to test the VS Code Dev Container setup for the Agentic SaaS Factory project. It guides a developer through the process of launching the dev container, verifying its contents, and running the `OpenHands` orchestrator script to interact with a basic example flow.

This is a conceptual test: it describes the actions a human would perform and the expected outcomes.

## 2. Prerequisites

*   All prerequisites listed in `docs/development/DEV_CONTAINER_SETUP.md` must be met by the user on their host machine (Docker installed, VS Code installed, "Remote - Containers" extension in VS Code).
*   The project repository cloned to the local machine.

## 3. Test Steps & Expected Outcomes

### Step 1: Open Project in Dev Container

1.  **Action:** Open the cloned project folder in VS Code.
2.  **Expected VS Code Behavior:**
    *   A notification should appear: "Folder contains a Dev Container configuration file. Reopen in Container?"
3.  **Action:** Click "Reopen in Container".
    *   (Alternatively, use Command Palette: "Remote-Containers: Reopen in Container").
4.  **Expected VS Code Behavior:**
    *   VS Code starts building the dev container image as defined in `.devcontainer/Dockerfile` (this may take time on first run).
    *   Once built, the container starts, and VS Code connects to it.
    *   The VS Code window should reload, and the file explorer should show files at `/workspace`.
    *   The integrated terminal should now be a shell *inside* the dev container (e.g., `vscode@<container_hostname>:/workspace$`).

### Step 2: Verify Tools and Environment in Dev Container Terminal

1.  **Action:** Open a new integrated terminal in VS Code (if one isn't already open).
2.  **Action:** Run the following commands and check their outputs:
    *   `python --version`
        *   **Expected Outcome:** Shows Python 3.11.x (or the version specified in the Dockerfile).
    *   `pip --version`
        *   **Expected Outcome:** Shows pip version associated with the container's Python.
    *   `pip list`
        *   **Expected Outcome:** Lists installed packages, including `pydantic` and `httpx`.
    *   `git --version`
        *   **Expected Outcome:** Shows Git version.
    *   `docker --version`
        *   **Expected Outcome:** Shows Docker client version (should match or be compatible with host Docker daemon). This confirms Docker CLI is installed and in PATH.
    *   `node --version` (if Node.js was installed in Dockerfile)
        *   **Expected Outcome:** Shows Node.js LTS version.
    *   `npm --version` (if Node.js was installed)
        *   **Expected Outcome:** Shows npm version.
    *   `whoami`
        *   **Expected Outcome:** Shows `vscode` (or the non-root username defined).
    *   `pwd`
        *   **Expected Outcome:** Shows `/workspace`.
    *   `ls -la /var/run/docker.sock`
        *   **Expected Outcome:** Shows the Docker socket file, indicating it's mounted. Permissions might vary, but its presence is key. The `postCreateCommand` (`sudo chown vscode /var/run/docker.sock`) attempts to ensure the `vscode` user can access it. If there are permission errors later when running Docker commands, this is an area to check on the host.
    *   `echo $PYTHONPATH`
        *   **Expected Outcome:** Includes `/workspace/src`.

### Step 3: Prepare for and Run `launch_openhands_orchestrator.sh`

1.  **Action:** In the dev container terminal, navigate to the scripts directory:
    ```bash
    cd /workspace/scripts
    ```
2.  **Action:** Set the required environment variables for the LLM API (as described in `docs/usage/RUNNING_ORCHESTRATOR.md`):
    ```bash
    export OH_USER_LLM_BASE_URL="https://lm.armand0e.online/v1"
    export OH_USER_LLM_API_KEY="sk-291923902182902-kd"
    # Note: The user should use their actual key.
    ```
3.  **Action:** Run the launch script:
    ```bash
    ./launch_openhands_orchestrator.sh
    ```
4.  **Expected Outcome:**
    *   The script outputs INFO messages about cleaning old instances (if any), preparing settings, and pulling/launching the `OpenHands` Docker container.
    *   No `docker: command not found` errors.
    *   No immediate permission errors related to `/var/run/docker.sock` (if so, see troubleshooting in `DEV_CONTAINER_SETUP.md`).
    *   The script should successfully start an `OpenHands` container on the **host's Docker daemon**.
    *   The script outputs "SUCCESS: OpenHands Orchestrator instance 'openhands-orchestrator-instance' should be starting."
    *   It provides the URL: `http://localhost:3000`.

### Step 4: Verify `OpenHands` Instance and Configuration

1.  **Action:** On the **host machine's** web browser, navigate to `http://localhost:3000`.
2.  **Expected Outcome:**
    *   The `OpenHands` web UI loads.
3.  **Action:** (If possible within OpenHands UI, or by inspecting `~/.openhands-orchestrator-state/settings.json` on the host, which was mounted from `/home/vscode/.openhands-orchestrator-state` inside the dev container where the script created it).
    *   Verify that `OpenHands` is configured with:
        *   LLM Base URL: `https://lm.armand0e.online/v1`
        *   LLM Model: `gpt-3.5-turbo` (or the alias for `devstral-small`)
        *   The extensive `custom_instructions` for the orchestrator agent should be part of its system prompt (this might be visible in logs or agent configuration sections of the UI if available).
4.  **Action (Host Terminal):** Check that the `OpenHands` container is running on the host:
    ```bash
    docker ps --filter "name=openhands-orchestrator-instance"
    ```
5.  **Expected Outcome:** The container `openhands-orchestrator-instance` should be listed as running.

### Step 5: Conceptually Test the "Uppercase Fruits" Example

This follows `docs/examples/SIMPLE_FLOW_EXAMPLE.md`.

1.  **Action (Prepare Input File):**
    *   As per `docs/usage/RUNNING_ORCHESTRATOR.md`, the easiest way is to have pre-mounted a host directory to `/workspace` inside the *OpenHands container itself* (this is different from the dev container's workspace mount). The current `launch_openhands_orchestrator.sh` doesn't do this by default.
    *   **Alternative for this test:** Use the `OpenHands` UI to manually create a file `/workspace/input.txt` and populate it with:
        ```
        apple
        banana
        cherry
        date
        ```
    *   *(If direct file creation via UI is hard, this step highlights a potential usability improvement for OpenHands or a need for the Orchestrator agent to handle file uploads/creation from user prompts).*
2.  **Action (Provide Task to Agent):** In the `OpenHands` UI chat input (connected to `http://localhost:3000`), provide the task to the agent:
    ```
    I have a file named `input.txt` in the root of the workspace. It contains a list of fruits, one per line. Please create a new file named `output.txt` in the root of the workspace, containing the same fruits but all in uppercase.
    ```
3.  **Expected Orchestrator Agent Behavior (Conceptual, based on its `custom_instructions`):**
    *   The agent acknowledges the task.
    *   It uses its LLM to create a plan (sequence of conceptual `open-codex-lib` operations: read `input.txt`, transform content to uppercase, write to `output.txt`, summarize).
    *   It may present this plan to the user for confirmation (as per its instructions).
    *   It then proceeds to execute the plan, using its internal tools (which simulate `open_codex_lib`):
        *   Reads `/workspace/input.txt` (using OpenHands file read capability).
        *   Sends the content to its LLM with a prompt to uppercase it.
        *   Writes the LLM's uppercased response to `/workspace/output.txt` (using OpenHands file write capability).
    *   It provides a summary message to the user in the chat.
4.  **Action (Verify Output):**
    *   Using the `OpenHands` UI (if it allows browsing `/workspace`) or by using `docker exec openhands-orchestrator-instance cat /workspace/output.txt` on the host, check the content of `output.txt`.
5.  **Expected Outcome:** `/workspace/output.txt` contains:
    ```
    APPLE
    BANANA
    CHERRY
    DATE
    ```

### Step 6: Cleanup

1.  **Action (Dev Container Terminal):** Stop the `OpenHands` instance:
    ```bash
    # (If you still have the launch_openhands_orchestrator.sh terminal active, it might show a stop command)
    # Or, from any dev container terminal:
    docker stop openhands-orchestrator-instance
    ```
    *(Note: The script launches it with `--rm` so it should be removed when stopped. If not, `docker rm openhands-orchestrator-instance` can be used after stopping).*
2.  **Action (VS Code):** Close the VS Code window or use "Remote-Containers: Close Remote Connection".
3.  **Expected Outcome:** The dev container stops (as per `shutdownAction: "stopContainer"` in `devcontainer.json`).

## 4. Test Result Criteria

*   **PASS:** All expected outcomes in Steps 1-5 are met. The dev container launches correctly, tools are verified, the `OpenHands` orchestrator script successfully launches and configures `OpenHands` using the host Docker, and the conceptual "Uppercase Fruits" example can be walked through with the agent producing the correct `output.txt`.
*   **FAIL:** Any of the expected outcomes are not met, particularly if the dev container fails to build/start, tools are missing/misconfigured, the launch script fails, `OpenHands` doesn't start or isn't configured correctly, or the agent fails to process the example task as expected.

This conceptual walkthrough provides a basis for manually verifying the dev container setup and the initial functionality of the `OpenHands` Orchestrator agent.
