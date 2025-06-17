# DESIGN DOCUMENT: Preconfigured Workspace for `open-codex-flow`

## 1. Overview

For the `OpenHands` Orchestrator Agent to effectively manage and execute `open-codex`-like operations (referred to as "open-codex-flow"), the sandboxed workspace provided by `OpenHands` must be preconfigured with the necessary tools, libraries, and a defined structure. This document outlines the components and setup of this preconfigured workspace.

The primary method for achieving this preconfiguration will be through a custom Docker image specified as the `SANDBOX_RUNTIME_CONTAINER_IMAGE` in the `OpenHands` configuration.

## 2. Purpose

*   **Enable `open-codex` Operations:** Provide the runtime environment required for `open-codex`-like agents/tools to function.
*   **Standardization:** Ensure that every `open-codex-flow` task orchestrated by the `OpenHands` agent runs in a consistent and predictable environment.
*   **Dependency Management:** Encapsulate all necessary software dependencies within the workspace image.
*   **Facilitate Orchestration:** Make it easier for the `OpenHands` Orchestrator Agent to manage inputs, outputs, and context for `open-codex` operations.

## 3. Workspace Components

The preconfigured workspace will include:

### 3.1. Base Environment:
*   **Operating System:** A lightweight Linux distribution (e.g., Debian Slim, Alpine with Python).
*   **Python:** A specific version (e.g., Python 3.10+) with `pip`.
*   **Node.js:** (Optional, include if JavaScript-based tooling related to `open-codex` or code manipulation is anticipated).

### 3.2. Core `open-codex` Logic/Tooling:
The preferred approach is to integrate the `open-codex` functionalities as a Python library.
*   **`open_codex_lib` (Python Library):**
    *   This library will encapsulate the core logic adapted from `ymichael/open-codex` or similar principles:
        *   Constructing prompts for code-related tasks (generation, explanation, modification, diffing).
        *   Interacting with an LLM endpoint (via a shared `LLMInterface` or its own).
        *   Parsing LLM responses containing code or diffs.
        *   Applying code changes or diffs to files.
        *   Performing file system I/O operations (read, write, create directory).
        *   (Potentially) A more granular sandboxing for executing specific code snippets if OpenHands' main sandbox is too broad for certain checks.
    *   This library will be installed via `pip` from a local package or a Git repository within the Docker image build process.

### 3.3. LLM Interaction:
*   **`httpx`:** For asynchronous HTTP requests to the LLM API.
*   The workspace will rely on the `OpenHands` Orchestrator Agent to provide the LLM endpoint URL and API key, likely via environment variables or passed arguments when invoking `open_codex_lib` functions.

### 3.4. Version Control:
*   **`git` CLI:** Full Git client installation for cloning repositories, checking out branches/commits, staging, committing, and applying diffs if necessary.

### 3.5. Common System Utilities:
*   **`patch`:** For applying diff files.
*   Standard Linux core utilities for file and text manipulation (though Python alternatives within `open_codex_lib` are preferred for complex operations).

### 3.6. Python Libraries (to be included in `requirements.txt` for the sandbox):
*   `httpx` (for LLM interface)
*   `pydantic` (for data models if `open_codex_lib` uses them for structured input/output)
*   The `open_codex_lib` itself.
*   Any other libraries required by `open_codex_lib`.

## 4. Workspace Structure (Convention within OpenHands Sandbox)

While `OpenHands` provides the root `/workspace/`, the Orchestrator Agent will manage tasks by creating temporary subdirectories for each distinct `open-codex-flow` operation or a sequence of related operations. A typical structure might be:

```
/workspace/  (Managed by OpenHands)
├── <orchestrator_task_id>/  (Created by Orchestrator Agent)
│   ├── input/                  # Input files, code snippets for the open-codex op
│   │   └── main_code.py
│   │   └── context_data.json
│   ├── output/                 # Output files, modified code from the open-codex op
│   │   └── main_code_modified.py
│   │   └── summary.txt
│   ├── open_codex_instructions.md # Specific instructions for this op
│   ├── execution_log.txt       # Log of the open-codex op
│   └── status.json             # Status of the open-codex op
```
The Orchestrator Agent will be responsible for populating the `input/` and `open_codex_instructions.md`, invoking the `open_codex_lib` function to process these, and then retrieving results from `output/` and `status.json`.

## 5. Context Provisioning

*   The `OpenHands` Orchestrator Agent will dynamically create context for each `open-codex` operation.
*   This typically involves writing an `open_codex_instructions.md` file within the task-specific directory, detailing:
    *   The precise goal of the operation (e.g., "Refactor the function 'calculate_total' in 'input/main_code.py' to improve efficiency").
    *   Paths to input files within the task directory.
    *   Expected output paths and formats.
    *   Any constraints, style guides, or specific LLM prompting guidance.

## 6. Dockerfile for `SANDBOX_RUNTIME_CONTAINER_IMAGE`

A `Dockerfile` will be created to build the custom sandbox image. Example sketch:

```dockerfile
# Start from a Python base image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    patch \
    # Other essential utilities \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install the open_codex_lib (assuming it's a local package)
# This step needs to be adapted based on how open_codex_lib is structured
# COPY ./path_to_open_codex_lib /app/open_codex_lib
# RUN pip install --no-cache-dir /app/open_codex_lib

# Or, if open_codex_lib is installable from a requirements file that includes it:
COPY requirements_sandbox.txt .
RUN pip install --no-cache-dir -r requirements_sandbox.txt

# Ensure OpenHands agent execution mechanisms can operate in this environment.
# This might involve setting up a non-root user or specific entrypoints
# if required by OpenHands' sandbox security model. For now, assume OpenHands handles this.

# Default command (might be overridden by OpenHands)
# CMD ["/bin/bash"]
```
The `requirements_sandbox.txt` would list `httpx`, `pydantic`, and any other direct Python dependencies for the `open_codex_lib` and its operation.

## 7. Summary

The preconfigured workspace is foundational for enabling the `OpenHands` Orchestrator Agent to delegate code-related micro-tasks to a standardized, `open-codex`-like functionality. It ensures consistency, manages dependencies, and provides a structured environment for these operations. The custom Docker image is the key delivery mechanism for this preconfiguration.
