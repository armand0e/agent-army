# Development Container Setup Guide

This guide explains how to set up and use the development container for the Agentic SaaS Factory project. Using the dev container provides a consistent, pre-configured environment with all necessary tools and dependencies for development and testing.

## Prerequisites

1.  **Docker Desktop / Docker Engine:** Ensure Docker is installed and running on your host machine.
    *   Windows/macOS: Install Docker Desktop.
    *   Linux: Install Docker Engine and ensure the Docker daemon is active. Your user should typically be part of the `docker` group to manage Docker without `sudo` for every command.
2.  **Visual Studio Code:** While not strictly required if you build and run the dev container manually, these instructions focus on using VS Code.
3.  **VS Code "Remote - Containers" Extension:** Install the `ms-vscode-remote.remote-containers` extension in VS Code. This extension allows you to open project folders inside a Docker container.

## Opening the Project in the Dev Container

1.  Clone this repository to your local machine.
2.  Open the cloned project folder in VS Code.
3.  VS Code should automatically detect the `.devcontainer/devcontainer.json` file and show a notification in the bottom-right corner: "Folder contains a Dev Container configuration file. Reopen in Container?"
    *   Click **"Reopen in Container"**.
4.  If you don't see the notification, you can open the Command Palette (Ctrl+Shift+P or Cmd+Shift+P) and search for/select **"Remote-Containers: Reopen in Container"** or **"Remote-Containers: Open Folder in Container..."**.
5.  VS Code will now build the Docker image defined in `.devcontainer/Dockerfile` (if it's the first time or the configuration has changed) and then start the dev container. This might take a few minutes on the first run.
6.  Once the container is built and started, VS Code will connect to it, and your project files will be available at `/workspace`. You'll have a terminal within VS Code that is inside the dev container.

## What's Included in the Dev Container?

The dev container comes pre-configured with:
*   **Python (3.11):** And project dependencies from `requirements.txt` (e.g., `pydantic`, `httpx`).
*   **Git:** For version control.
*   **Docker CLI:** Configured to communicate with your host machine's Docker daemon (Docker-outside-of-Docker). This allows you to run `docker` commands inside the dev container that affect your host's Docker.
*   **Node.js (LTS version via nvm):** For general JavaScript/TypeScript tooling if needed.
*   **Common Linux Utilities:** `jq`, `curl`, `sudo` (for the `vscode` user), etc.
*   **VS Code Extensions:** Pre-installed for Python development, Docker, Markdown, etc., as defined in `devcontainer.json`.
*   **Environment:** Your project code is mounted at `/workspace`. The `PYTHONPATH` is set up to include `/workspace/src`.

## Running the `OpenHands` Orchestrator

Once you are inside the dev container (e.g., you have a VS Code terminal open that's running inside it):

1.  **Navigate to the scripts directory:**
    ```bash
    cd /workspace/scripts
    ```
2.  **Ensure the launch script is executable (should be by default due to git permissions, but can re-run):**
    ```bash
    chmod +x launch_openhands_orchestrator.sh
    ```
3.  **Set API Credentials (Recommended):**
    The `launch_openhands_orchestrator.sh` script will use environment variables `OH_USER_LLM_BASE_URL` and `OH_USER_LLM_API_KEY` if they are set. You can set these in the dev container's terminal for your current session:
    ```bash
    export OH_USER_LLM_BASE_URL="https://lm.armand0e.online/v1"
    export OH_USER_LLM_API_KEY="sk-291923902182902-kd"
    ```
    For persistence across dev container sessions, you can add these exports to `/home/vscode/.bashrc` or `/home/vscode/.profile` inside the dev container. Alternatively, VS Code's `devcontainer.json` can be configured to load them from a local `.env` file (not implemented in current `devcontainer.json` to avoid committing `.env`).
4.  **Run the launch script:**
    ```bash
    ./launch_openhands_orchestrator.sh
    ```
    This script will now use the Docker CLI *inside* the dev container to start the `OpenHands` Docker container *on your host machine's Docker daemon*.
5.  Follow the output from the script to access the `OpenHands` UI (typically `http://localhost:3000`).

## Troubleshooting

### Docker Socket Permissions (Linux Hosts)

When using the Docker-outside-of-Docker approach (mounting `/var/run/docker.sock`), you might encounter permission errors if the `vscode` user inside the dev container (UID 1000 by default) doesn't have permission to access the Docker socket on the host.

*   **Ensure Host User is in `docker` group:** The user running VS Code on the host machine should be part of the `docker` group. This often grants necessary permissions to the socket.
*   **Socket GID Matching:** A more robust solution is to ensure the `vscode` user inside the container shares a group ID (GID) with the `docker` group on the host that owns the socket. The `devcontainer.json`'s `postCreateCommand` attempts `sudo chown vscode /var/run/docker.sock`, but this might not always be effective or desirable.
    *   You can find the GID of `docker.sock` on your host: `stat -c '%g' /var/run/docker.sock`.
    *   Then, you can try to add the `vscode` user in the container to a group with this GID, or modify the `USER_GID` argument in the `Dockerfile` and rebuild the dev container (advanced).
*   **VS Code "Remote - Containers" settings:** Sometimes, specific settings in VS Code might be needed if it tries to manage the socket permissions itself.

If you see "permission denied" errors when the script tries to run `docker` commands, this is the most likely area to investigate.

## Developing the Code

*   You can now edit the project files (Python code, Markdown documents, scripts) directly in VS Code. Changes are reflected in your local file system due to the workspace mount.
*   Use the integrated terminal in VS Code (which is inside the dev container) to run Python scripts, git commands, etc.

This dev container setup aims to streamline the development and testing process for this project.
