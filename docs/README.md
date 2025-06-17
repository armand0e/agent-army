# Agentic SaaS Factory - Design Phase

This repository contains the design documents and initial structural outlines for an Agentic SaaS Factory – a multi-agent AI system envisioned to automate the software development lifecycle.

## Overview

The system is designed around a collection of specialized AI agents that collaborate to perform tasks ranging from requirements gathering to deployment and monitoring. This project is currently in the design and conceptualization phase.

Key components and concepts include:
*   **Specialized AI Agents:** UIBA, MPA, FDA, BDA, DMA, IDA, QATA, ERA. Design documents for each are located in `docs/agents/`.
*   **Shared Knowledge Base (SKB):** A central repository for all project information, agent knowledge, and artifacts. Design: `docs/shared_components/knowledge_base/DESIGN.md`.
*   **Inter-Agent Communication (IAC):** Protocols and mechanisms for agents to collaborate. Design: `docs/shared_components/communication/DESIGN.md`.
*   **Orchestration Logic:** The central brain managing workflows and agent coordination. Design: `docs/orchestrator/DESIGN.md`.
*   **Local LLM Serving:** Intended use of `mudler/LocalAI` to serve models like `devstral-small` (though current testing uses a user-provided public API). Setup prerequisites: `docs/SETUP_PREREQUISITES.md`.
*   **OpenHands for Orchestration:** A component designed to use `OpenHands` as a user-facing orchestrator for `open-codex`-like operations.

## Current Focus: OpenHands Orchestrator Component

A recent development focus has been on designing a system where `OpenHands` acts as an orchestrator for `open-codex`-like workflows.

*   **Launch Script:** `scripts/launch_openhands_orchestrator.sh`
*   **Usage Guide:** `docs/usage/RUNNING_ORCHESTRATOR.md`
*   **Conceptual Example:** `docs/examples/SIMPLE_FLOW_EXAMPLE.md`
*   **Design - OpenHands Orchestrator Agent Logic:** `docs/orchestrator/OPENHANDS_ORCHESTRATOR_DESIGN.md`
*   **Design - Preconfigured Workspace for `open-codex-flow`:** `docs/shared_components/preconfigured_workspace/DESIGN.md`
*   **Design - Inter-`open-codex`-Operation Context Sharing:** `docs/shared_components/context_sharing/OPEN_CODEX_OPERATION_CONTEXT.md`

## Repository Structure

*   `src/`: Source code for agents and shared components (currently contains UIBA outline).
*   `docs/`: All design documents and user guides.
*   `configs/`: Configuration templates and files.
*   `scripts/`: Utility and launch scripts.
*   `tests/`: Placeholder for future tests.

## Next Steps (Conceptual)

Following this design phase, next steps would involve:
1.  Setting up and validating the LLM environment (LocalAI or continued use of public API).
2.  Implementing the `open_codex_lib`.
3.  Implementing the `OpenHands` Orchestrator Agent's ability to use `open_codex_lib`.
4.  Iteratively developing and testing the full `open-codex-flow` with more complex examples.
5.  Gradually implementing the other specialized agents and the main orchestrator.

Refer to the individual `DESIGN.md` files in the `docs` directory for detailed information on each component.
