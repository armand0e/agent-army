# Agentic SaaS Factory - Design & Development Environment

This repository contains the design documents, initial structural outlines, and development environment setup for an Agentic SaaS Factory – a multi-agent AI system envisioned to automate the software development lifecycle.

## Project Status

This project is currently in the design and early conceptual implementation phase. The primary focus has been on:
1.  Designing the overall multi-agent architecture.
2.  Detailing the roles and responsibilities of individual specialized AI agents.
3.  Setting up a development environment using VS Code Dev Containers.
4.  Designing and conceptually testing a component where `OpenHands` acts as a user-facing orchestrator for `open-codex`-like workflows.

## Key Architectural Components (Designs)

Detailed design documents for each component can be found in the `docs/` directory:

*   **Specialized AI Agents (`docs/agents/`):**
    *   UIBA (User Interaction & Briefing Agent)
    *   MPA (Module & API Design Agent)
    *   FDA (Feature Development Agent)
    *   BDA (Bug Detection & Debugging Agent)
    *   DMA (Deployment & Monitoring Agent)
    *   IDA (Integration & Data Flow Agent)
    *   QATA (Quality Assurance & Testing Agent)
    *   ERA (Evolutionary Refinement Agent)
*   **Shared Components (`docs/shared_components/`):**
    *   Shared Knowledge Base (SKB)
    *   Inter-Agent Communication (IAC)
    *   Preconfigured Workspace (for `open-codex-flow` within OpenHands)
    *   Inter-`open-codex`-Operation Context Sharing
*   **Orchestration Logic:**
    *   Overall System Orchestrator (`docs/orchestrator/DESIGN.md`)
    *   `OpenHands` as an Orchestrator Agent (`docs/orchestrator/OPENHANDS_ORCHESTRATOR_DESIGN.md`)

## Development Environment Setup (Dev Container)

To ensure a consistent and easy-to-set-up development environment, this project uses VS Code Dev Containers.

*   **Setup Guide:** Please refer to **[Development Container Setup Guide](./development/DEV_CONTAINER_SETUP.md)** for detailed instructions on how to get started.
*   **Prerequisites:** Docker Desktop / Docker Engine, VS Code, and the "Remote - Containers" VS Code extension.

## Current Focus: `OpenHands` Orchestrator Component

The most recent work involves a component where `OpenHands` is configured to act as an orchestrator for `open-codex`-like workflows, using a user-provided LLM endpoint.

*   **Launch Script:** `scripts/launch_openhands_orchestrator.sh` (run from within the dev container or a similarly configured environment).
*   **Usage Guide for this component:** `docs/usage/RUNNING_ORCHESTRATOR.md`.
*   **Conceptual Example Flow:** `docs/examples/SIMPLE_FLOW_EXAMPLE.md`.

## Repository Structure

*   `.devcontainer/`: Configuration files (`Dockerfile`, `devcontainer.json`) for the VS Code Dev Container.
*   `src/`: Source code for agents and shared components (currently contains an initial outline for the UIBA agent).
*   `docs/`: All design documents, usage guides, and examples.
*   `configs/`: Configuration templates (e.g., for OpenHands settings).
*   `scripts/`: Utility and launch scripts.
*   `requirements.txt`: Root Python dependencies for the dev container and project.

## Next Steps (Conceptual)

Following the setup of the dev environment and the design phase:
1.  Validate the `OpenHands` orchestrator proof-of-concept by manually running the example flow.
2.  Implement the `open_codex_lib` as a Python library within the preconfigured workspace.
3.  Refine the `OpenHands` Orchestrator Agent logic to robustly use `open_codex_lib`.
4.  Iteratively develop and test more complex `open-codex-flow` examples.
5.  Begin phased implementation of other specialized agents (e.g., UIBA, MPA) and the main system orchestrator, integrating them with the Shared Knowledge Base and Inter-Agent Communication framework.

Refer to the individual `DESIGN.md` files for detailed information on each component.
