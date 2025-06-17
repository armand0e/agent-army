# DESIGN DOCUMENT: Orchestration Logic

## 1. Overview and Purpose

The Orchestrator is the central nervous system of the multi-agent SaaS development system. It is responsible for managing the end-to-end workflow, from interpreting the initial `ProjectBrief` (once prepared by UIBA and stored in SKB) to coordinating the activities of all specialized AI agents (MPA, FDA, BDA, DMA, IDA, QATA, ERA) until a deployable SaaS application is produced.

This document outlines the design for the Orchestrator, focusing on its architecture, core responsibilities, workflow management, and interaction with other system components. The design is heavily influenced by Section 7 ("Orchestration Logic and Integration") of the system's guiding research document and aims to adapt principles from frameworks like `ruvnet/claude-code-flow`.

## 2. Role and Importance

*   **Workflow Management:** Directs the overall flow of tasks and information throughout the system.
*   **Task Coordination:** Decomposes high-level goals into manageable sub-tasks and assigns them to appropriate specialized agents.
*   **Agent Management:** (Potentially) Manages the lifecycle of agent instances, especially if dynamic scaling of agent types is implemented. For now, assumes agents are available services.
*   **State Tracking:** Maintains the state of the overall project and individual high-level tasks.
*   **Context Management:** Ensures agents receive necessary context for their tasks, primarily by pointing them to relevant information in the Shared Knowledge Base (SKB).
*   **Error Handling & Recovery:** Manages system-level errors, retries, and escalations if agents fail or produce unexpected results.
*   **Decision Making:** Makes decisions on workflow progression based on agent outputs and system state (e.g., deciding to move from development to QA, or from QA to deployment).

## 3. Core Responsibilities

*   **Project Initiation:** Monitors the SKB or receives notifications (e.g., from UIBA via the event bus) for new `ProjectBrief` documents.
*   **Master Planner Activation:** Activates the MPA to process a new `ProjectBrief` and generate the technical plans.
*   **Task Distribution:**
    *   Once MPA generates the `TaskList`, the Orchestrator takes these tasks.
    *   Assigns tasks to available and appropriate agent types (FDA, BDA, DMA, IDA, QATA) via the Inter-Agent Communication (IAC) message bus.
    *   Manages dependencies between tasks (e.g., ensuring backend API is implemented before frontend tries to use it).
*   **Workflow Sequencing:** Manages the sequence of operations, e.g., UIBA -> MPA -> (FDA <-> BDA <-> QATA loop) -> IDA -> QATA (integration) -> DMA. The ERA can be triggered at various points.
*   **Monitoring Agent Progress:** Receives `STATUS_UPDATE` messages from agents via the IAC. Tracks which tasks are in progress, completed, or failed.
*   **Result Aggregation & Handoff:** When an agent completes a task that produces an artifact for another agent (e.g., FDA produces code for QATA), the Orchestrator ensures the consuming agent is notified or the artifact is correctly referenced in the SKB for pickup.
*   **Loop Management:** Manages iterative loops, such as the development-test-debug cycle between FDA, QATA, and BDA, or refinement cycles triggered by ERA.
*   **Resource Management (High-Level):** While `OpenHands` handles individual agent execution environments, the Orchestrator might make high-level decisions about prioritizing tasks if agent resources are constrained (future).
*   **System-Level Error Handling:** If an agent fails catastrophically or a critical error occurs that individual agents cannot handle, the Orchestrator attempts recovery actions (e.g., retrying a task with a different agent instance if applicable, or escalating to a human operator).

## 4. Proposed Architecture

An **event-driven, state-machine-based architecture** is proposed for the Orchestrator.

*   **State Machine:** The overall SaaS development lifecycle for a given project can be modeled as a state machine (e.g., `NEW_BRIEF`, `PLANNING_IN_PROGRESS`, `DEVELOPMENT_IN_PROGRESS`, `QA_IN_PROGRESS`, `INTEGRATION_PHASE`, `READY_FOR_DEPLOYMENT`, `DEPLOYMENT_IN_PROGRESS`, `MONITORING_ACTIVE`, `COMPLETED`, `ERROR_STATE`).
*   **Event-Driven:** The Orchestrator reacts to events published on the Inter-Agent Communication (IAC) event bus. These events include:
    *   `NewProjectBriefAvailable` (from UIBA/SKB)
    *   `PlanningComplete` (from MPA)
    *   `TaskCompleted` (from any agent)
    *   `TaskFailed` (from any agent)
    *   `BugReported` (from QATA)
    *   `FixValidated` (from BDA/QATA)
    *   `DeploymentSuccessful` (from DMA)
    *   `CriticalAlert` (from DMA)
    *   `RefinementSuggested` (from ERA)
*   **Core Components:**
    1.  **Event Listener:** Subscribes to relevant topics on the IAC event bus.
    2.  **Workflow Engine:** Contains the logic for the state machine and defines transitions based on events and current state. This is where orchestration patterns are implemented.
    3.  **Task Manager:** Maintains a queue of pending tasks (from MPA's `TaskList`), their dependencies, and current status. Assigns tasks to agents.
    4.  **State Repository (within SKB or dedicated):** Persists the current state of each ongoing project/workflow to allow for recovery and long-running processes.
    5.  **Agent Interaction Module:** Handles sending messages (e.g., `TASK_ASSIGNMENT`) to agents via the IAC message bus and receiving direct responses if needed.

### 4.1. Orchestration Patterns (from Guiding Document Section 7.3):

The Orchestrator will dynamically apply different patterns:

*   **Linear Orchestrator Pattern:** Used for well-defined sequences where tasks must be executed in a specific order.
    *   Example: UIBA (Briefing) -> MPA (Planning). After MPA planning, initial tasks for FDA might be linear.
    *   Involves Planning Phase (analyzing MPA's task list), Assignment, Sequential Execution, Synthesis (Orchestrator confirms all parts of a phase are done before moving to next).
*   **Adaptive Orchestrator Pattern:** Used for more dynamic phases, especially where iteration or conditional logic is required.
    *   Example: The develop-test-debug cycle (FDA -> QATA -> BDA -> FDA). The Orchestrator dynamically routes tasks based on test outcomes (e.g., if tests pass, move to next feature; if fail, assign bug to BDA).
    *   Example: ERA suggests a refinement. Orchestrator might trigger FDA to generate new code, then QATA to test, then decide if refinement is successful.
    *   Features flexible routing, context-aware processing, and dynamic agent selection (if multiple instances of an agent type are available).

### 4.2. Best Practices for Effective Orchestration (from Guiding Document Section 7.4):

*   **Structure Agent Decisions:** The Orchestrator receives structured status updates and requests from agents, rather than just natural language. It uses this structured data to make control flow decisions.
*   **Scope Agent Memory/Context:** When assigning a task, the Orchestrator provides the agent with specific pointers to necessary information in the SKB (e.g., `task_specification_skb_id`), rather than giving agents broad access to all project data.
*   **Stop Loop Drift:** The Task Manager component will track each task's turn (who ran what, what was returned, success/failure) to prevent redundant work, especially in iterative loops.
*   **Return Structured Outputs (from Agents to Orchestrator):** Agents use defined `STATUS_UPDATE` messages or specific result messages.
*   **Track Task Progress:** The Task Manager maintains the overall state of tasks (pending, in-progress, completed, failed), distinct from individual agent memory.

## 5. Integration with OpenHands

*   The Orchestrator itself might not run *within* an OpenHands sandbox in the same way individual task-performing agents do. It's a higher-level control process.
*   However, it *manages* agents that are expected to run within `OpenHands` (or similar sandboxed environments if an agent type doesn't fit OpenHands, though the goal is to use OpenHands as the primary agent execution platform).
*   When the Orchestrator assigns a task to an agent like FDA, it effectively triggers an `OpenHands` session for that FDA instance to perform its work (file I/O, code execution, tool usage) related to that task.
*   The Orchestrator needs to know the status of these `OpenHands`-based agent tasks.

## 6. Interaction with IAC and SKB

*   **Inter-Agent Communication (IAC):**
    *   **Receives:** Events from the event bus, status updates from agents via the message bus.
    *   **Sends:** `TASK_ASSIGNMENT` messages to agents via the message bus, potentially commands or queries.
*   **Shared Knowledge Base (SKB):**
    *   **Reads:** `ProjectBrief` to initiate workflow, `TaskList` from MPA, agent status details, configuration files.
    *   **Writes:** Overall project status, logs of orchestration decisions, potentially aggregated performance metrics of the development process itself.

## 7. Scalability and Resilience

*   **Scalability:**
    *   The event-driven nature allows for distributed processing of events.
    *   The Orchestrator's Task Manager and Workflow Engine could be designed to handle multiple concurrent projects.
    *   If using a robust message broker, it can handle many messages.
    *   State persistence allows the Orchestrator to be restarted and resume workflows.
*   **Resilience:**
    *   Persistent state ensures that if the Orchestrator crashes, it can recover ongoing workflows.
    *   Clear error handling and retry mechanisms for failed agent tasks.
    *   Decoupling via message bus means if one agent type is temporarily unavailable, other unrelated tasks can continue.

## 8. Dependencies

*   **Internal:**
    *   All specialized agents (UIBA, MPA, FDA, etc.): As entities to be managed and coordinated.
    *   Inter-Agent Communication Framework: For sending/receiving messages and events.
    *   Shared Knowledge Base: For accessing project data, task lists, and storing orchestration state.
    *   `OpenHands` (as the execution environment for the agents it orchestrates).
*   **External:**
    *   Message Broker technology (if used, e.g., RabbitMQ, Redis Streams, Kafka).
    *   Database for persisting Orchestrator state (could be part of SKB infrastructure or separate).
    *   Python (or chosen implementation language) runtime and libraries.

## 9. Future Considerations

*   **Dynamic Agent Scaling:** Orchestrator could spin up/down agent instances based on workload (requires integration with an agent deployment/management system).
*   **Advanced Resource Allocation:** More sophisticated algorithms for allocating tasks based on agent capabilities, current load, and task priority.
*   **Human-in-the-Loop Escalation:** Formal workflows for escalating issues that agents or the orchestrator cannot resolve to human operators, including providing rich context.
*   **Learnable Orchestration Strategies:** The Orchestrator itself could have components that learn and optimize workflow management or agent assignment strategies over time, possibly guided by the ERA.
*   **Multi-Project Orchestration:** Explicit features for managing and prioritizing tasks across many concurrent SaaS development projects.
*   **Visual Workflow Monitoring Interface:** A dashboard for human operators to see the status of all ongoing projects, agent activities, and task queues managed by the Orchestrator.

This document provides the design for the Orchestrator, the conductor of the entire multi-agent SaaS development symphony.
