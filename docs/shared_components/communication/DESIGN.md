# DESIGN DOCUMENT: Inter-Agent Communication (IAC)

## 1. Overview and Purpose

Effective Inter-Agent Communication (IAC) is the backbone of the multi-agent SaaS development system, enabling specialized AI agents to collaborate, share information, coordinate actions, and work cohesively towards the common goal of generating and deploying SaaS applications. This document outlines the proposed protocols, message structures, and mechanisms for IAC.

The design draws heavily from established principles in multi-agent systems (MAS) and the specific insights from Section 5 ("Inter-Agent Communication Protocols") of the system's guiding research document, aiming for a robust, scalable, and flexible communication framework.

## 2. Importance of Standardized Communication

*   **Collaboration:** Enables agents with different specializations to work together on complex tasks that no single agent could accomplish alone.
*   **Coordination:** Allows the Orchestrator and individual agents to manage dependencies, sequences of actions, and resource allocation.
*   **Information Sharing:** Facilitates the exchange of data, status updates, results, and context necessary for informed decision-making by each agent.
*   **Reduced Complexity:** Standardized protocols simplify the development of individual agents, as they can rely on a common way to interact.
*   **Interoperability:** Lays the groundwork for potential future integration with external agents or systems if a widely adopted standard (or a well-defined internal one) is used.

## 3. Proposed Communication Paradigm

A hybrid approach is proposed, combining direct message passing (facilitated by the Orchestrator) for command-and-control interactions and task assignments, with an event-driven model for status updates and broader notifications. The Shared Knowledge Base (SKB) will also serve as an indirect communication mechanism for persistent data sharing.

### 3.1. Core Principles:

*   **Asynchronous Communication:** Most interactions should be asynchronous to prevent blocking and allow agents to work in parallel.
*   **Message-Based:** Interactions will primarily occur through structured messages.
*   **Centralized Orchestration for Key Workflows:** The main Orchestrator will manage critical workflows, task assignments to specific agent types, and monitor overall progress. Agents will report status back to the Orchestrator.
*   **Service Discovery:** Agents (or their hosting containers/services) will need to be discoverable, likely managed by the Orchestrator or a service registry integrated with the deployment environment (e.g., Kubernetes DNS).

### 3.2. Protocol Considerations (Inspired by Guiding Document Section 5):

While implementing a full FIPA-ACL or NLIP stack might be overly complex for an initial internal system, their principles will be adopted:

*   **Performatives/Communicative Acts:** Messages will have a clear "intent" or "performative" (e.g., `REQUEST_TASK`, `TASK_ASSIGNMENT`, `STATUS_UPDATE`, `QUERY_SKB`, `PROVIDE_DATA`, `ERROR_REPORT`). This helps the receiving agent understand the purpose of the message.
*   **Structured Messages:** Messages will be structured (likely JSON) with common headers and a payload specific to the performative.
    *   **Common Headers:** `message_id`, `sender_agent_id`, `receiver_agent_id` (or `topic` for pub/sub), `performative`, `timestamp`, `conversation_id` (to track related messages).
*   **Content Language & Ontology:** The "content" of messages will often be structured data (e.g., a `TaskDefinition` Pydantic model serialized to JSON). While not a full formal ontology initially, data models defined in `data_models.py` (for UIBA) and similar models for other agents and shared objects will serve as a de-facto shared vocabulary. The SKB's ontology will further formalize this.
*   **NLIP Inspiration for Flexibility:** For more complex data or instructions within payloads where extreme structure is cumbersome, agents might embed natural language descriptions that the receiving LLM-powered agent can interpret, alongside structured fields. This offers some of the "hot-extensibility" benefits described for NLIP.

## 4. Communication Mechanisms

1.  **Orchestrator-Mediated Message Bus (Primary for Tasks & Control):**
    *   **Mechanism:** A central message bus (e.g., implemented with Redis Streams, RabbitMQ, or a custom solution built into the Orchestrator) managed by the Orchestrator.
    *   **Usage:**
        *   Orchestrator assigns tasks to specific agent *types* or instances by publishing messages to dedicated agent queues/topics.
        *   Agents subscribe to their relevant queues/topics.
        *   Agents send status updates, results, or requests for new tasks back to the Orchestrator via its dedicated input queue/topic.
    *   **Benefits:** Decouples agents, allows for load balancing if multiple instances of an agent type exist, centralized monitoring of task flow by the Orchestrator.
2.  **Event Bus (for System-Wide Notifications):**
    *   **Mechanism:** A publish-subscribe system (could be the same message bus technology but used differently).
    *   **Usage:**
        *   Agents publish significant events (e.g., `UIBA:ProjectBriefStored`, `FDA:FeatureBranchCommitted`, `QATA:CriticalBugFound`, `DMA:DeploymentSucceeded`).
        *   Other interested agents (especially ERA, Orchestrator, UIBA for user updates) subscribe to these events.
    *   **Benefits:** Allows for reactive behavior and awareness across the system without direct coupling.
3.  **Shared Knowledge Base (SKB) for Indirect Communication:**
    *   **Mechanism:** Agents write and read structured documents and artifacts to/from the SKB.
    *   **Usage:**
        *   UIBA stores `ProjectBrief`; MPA reads it.
        *   MPA stores `ArchitectureDocument`, `TaskList`; FDA/other agents read them.
        *   QATA stores `TestExecutionReport`; BDA/FDA/ERA read it.
    *   **Benefits:** Persistent storage of information, ideal for larger data/artifacts that don't fit well in messages, asynchronous access.
    *   **Note:** Changes to SKB documents might also trigger events on the Event Bus (e.g., "SKB:DocumentUpdated").
4.  **Direct API Calls (Limited Use):**
    *   For tightly coupled, synchronous interactions where immediate response is needed and a message bus introduces unnecessary overhead. This should be used sparingly to maintain loose coupling.
    *   Example: An agent needing a quick, specific configuration detail from a central `ConfigService` (if one exists outside the file-based config).

## 5. Message Structures (Examples)

All messages will be JSON objects.

**Common Message Envelope:**
```json
{
  "message_id": "uuid_string",
  "conversation_id": "uuid_string_or_task_id",
  "sender_agent_id": "agent_type:instance_id",
  "receiver_agent_id": "agent_type:instance_id_or_topic",
  "timestamp": "iso_datetime_string",
  "performative": "PERFORMATIVE_TYPE",
  "payload_version": "1.0",
  "payload": {
    // Specific to the performative
  }
}
```

**Example Performatives & Payloads:**

*   **`TASK_ASSIGNMENT` (Orchestrator to Agent):**
    ```json
    // payload for TASK_ASSIGNMENT
    {
      "task_id": "task_uuid",
      "task_type": "specific_task_enum_or_string", // e.g., "IMPLEMENT_API_ENDPOINT", "GENERATE_TEST_CASES"
      "task_specification_skb_id": "skb_document_id_for_full_spec", // Link to detailed spec in SKB
      "priority": "high/medium/low",
      "deadline_hint": "iso_datetime_string_optional"
    }
    ```
*   **`STATUS_UPDATE` (Agent to Orchestrator/Topic):**
    ```json
    // payload for STATUS_UPDATE
    {
      "task_id": "task_uuid_optional",
      "status": "in_progress/completed/failed/blocked",
      "progress_percentage": 75, // Optional
      "message": "Brief text update",
      "details_skb_id": "skb_document_id_for_full_report_optional" // e.g., link to TestExecutionReport
    }
    ```
*   **`DATA_REQUEST` (Agent A to Agent B or Service):**
    ```json
    // payload for DATA_REQUEST
    {
      "query_skb_id": "skb_document_id_containing_query_details", // or inline query
      "data_schema_expected_skb_id": "skb_document_id_for_response_schema" // Optional
    }
    ```
*   **`DATA_RESPONSE` (Agent B to Agent A):**
    ```json
    // payload for DATA_RESPONSE
    {
      "request_message_id": "original_message_id",
      "status": "success/error",
      "data_skb_id": "skb_document_id_containing_data", // or inline data if small
      "error_message": "string_if_status_is_error"
    }
    ```

## 6. Integration with `ruvnet/claude-code-flow` (MCP)

`ruvnet/claude-code-flow` mentions Model Context Protocol (MCP) integration. If adapting `claude-code-flow`'s orchestration logic, we should investigate MCP further.
*   If MCP provides a standardized way for agents (or the orchestrator) to interact with tools or external services (including other agents acting as services), it could be adopted or adapted for some interactions.
*   The key is how MCP messages are structured and if they align with or can encapsulate the performative-based JSON messages proposed above.
*   If MCP is primarily for tool use by a single agent instance, then our IAC mechanisms (message bus, event bus) would still be needed for higher-level coordination between distinct agent instances/types.

## 7. Addressing Challenges (from Guiding Document Section 5.4)

*   **Lack of Standardized Protocols:** Addressed by defining clear internal message structures and performatives.
*   **Ambiguity and Misinterpretation:** Minimized by using structured JSON payloads with references to well-defined data models (from SKB or code) and clear performatives. LLM-to-LLM communication still carries some risk, which needs careful prompt engineering for interpreting message payloads.
*   **Latency:** Asynchronous design helps. Choice of message bus technology will be important (e.g., Redis is fast, Kafka for high throughput). Direct API calls are an option for latency-sensitive needs.
*   **Security and Privacy:**
    *   Message bus should be secured (authentication, authorization for topics/queues).
    *   Encryption of message payloads if they contain sensitive data not already protected by transport layer security (e.g., TLS for HTTP calls to message bus API).
    *   Agents should only be subscribed to topics/queues relevant to their role.
*   **Scalability:** Message bus/event bus architectures are generally scalable. The SKB and Orchestrator become key scaling points for the overall system.
*   **Adaptability:** A message-based system with defined performatives allows for adding new agents or modifying agent capabilities with less impact, as long as they adhere to the message contracts.

## 8. Dependencies

*   **Orchestrator:** Central to managing the message bus and routing many types of messages.
*   **Shared Knowledge Base (SKB):** Many messages will contain IDs referencing documents in the SKB. The SKB itself needs to be accessible and performant.
*   **Individual Agents:** Must implement client logic to connect to the message/event bus, serialize/deserialize messages, and handle defined performatives.
*   **Network Infrastructure:** Reliable network for message passing.
*   **Message Broker Technology (e.g., RabbitMQ, Redis Streams, Kafka, NATS):** If a dedicated broker is used.

## 9. Future Considerations

*   **Formal Agent Communication Language (ACL) Adoption:** For broader interoperability, consider more formal adoption/mapping to FIPA-ACL or NLIP if the system needs to interact with external, standardized agents.
*   **Dynamic Conversation Management:** More sophisticated mechanisms for managing complex, multi-turn conversations or negotiations between agents.
*   **QoS Guarantees:** Implementing Quality of Service levels for messages (e.g., guaranteed delivery, priority queues).
*   **Visual Monitoring of Communication Flow:** Tools to visualize message flow and agent interactions for debugging and analysis.

This document outlines the foundational communication framework for the multi-agent system, emphasizing structured, asynchronous messaging.
