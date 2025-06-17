# DESIGN DOCUMENT: Quality Assurance & Testing Agent (QATA)

## 1. Overview

The Quality Assurance & Testing Agent (QATA) is a vital component of the multi-agent SaaS development system, dedicated to ensuring the quality, reliability, and correctness of the software being developed. QATA automates various aspects of the testing lifecycle, including test planning, test case generation, test script creation, test execution, and results analysis.

It works closely with the Feature Development Agent (FDA) by testing its code outputs, with the Bug Detection & Debugging Agent (BDA) by providing detailed bug reports, and with the Deployment & Monitoring Agent (DMA) by validating builds before deployment. QATA leverages Large Language Models (e.g., `devstral-small` via `LocalAI`) for generating test cases and scripts, and principles from `OpenAlpha_Evolve` for rigorous program evaluation within the `OpenHands` sandboxed environment.

## 2. Role & Responsibilities

*   **Test Planning:** Based on requirements from the `ProjectBrief` and `APISpecification` (from MPA/SKB), develop a high-level test plan outlining the scope, types of tests (unit, integration, E2E, performance, security), and environments.
*   **Test Case Generation:** Generate detailed test cases for:
    *   **Unit Tests:** For individual functions, methods, or components developed by FDA.
    *   **Integration Tests:** For interactions between modules/services as defined by IDA and MPA.
    *   **End-to-End (E2E) Tests:** For user workflows and complete feature validation.
    *   (Future) Performance Tests, Security Test stubs.
*   **Test Script Creation:** Convert generated test cases into executable test scripts using appropriate testing frameworks (e.g., PyTest for Python backend, Jest/Playwright for frontend).
*   **Test Execution:** Run test scripts in a controlled, sandboxed environment (provided by `OpenHands`).
*   **Results Analysis & Reporting:** Analyze test execution results, identify failures, and generate comprehensive test reports including pass/fail status, logs, screenshots (for UI tests), and coverage metrics.
*   **Bug Reporting:** Create structured bug reports for failing tests, providing all necessary details for BDA and FDA to reproduce and diagnose the issue.
*   **Regression Testing:** Maintain and execute regression test suites to ensure new changes do not break existing functionality.
*   **Requirements Verification:** Validate that the implemented software meets the functional and non-functional requirements outlined in the `ProjectBrief`.
*   **Feedback Loop:** Provide feedback to FDA on code quality and testability, and to MPA/IDA if specifications are untestable or ambiguous.

## 3. Core Logic & Operations

### 3.1. Workflow (per feature/build to be tested):

1.  **Test Task Acquisition:**
    *   Receives a testing task from the Orchestrator when FDA completes a feature, IDA defines an integration point, or DMA prepares a build for deployment.
    *   Task includes references to the code version (commit hash/branch), relevant specifications (`ProjectBrief`, `APISpecification`), and type of testing required.
2.  **Context Gathering (from SKB):**
    *   Retrieves feature specifications, API contracts, data models, and user stories.
    *   Accesses existing test plans and regression suites.
3.  **Test Case & Script Generation (LLM-driven):**
    *   For each requirement/functionality:
        *   Prompts `devstral-small` to generate positive and negative test cases, edge cases, and boundary conditions.
        *   Prompts `devstral-small` to convert these test cases into executable test scripts in the relevant testing framework (e.g., "Generate PyTest unit tests for this Python function...", "Generate Playwright E2E test script for this login workflow...").
        *   Leverages principles from `OpenAlpha_Evolve`'s automated program evaluation for syntax checking and functional testing against examples/specs.
4.  **Test Environment Setup (via `OpenHands` & DMA):**
    *   Ensures the correct version of the application is deployed in a clean, sandboxed test environment. This might involve coordination with DMA if a dedicated test environment needs provisioning.
5.  **Test Execution (via `OpenHands`):**
    *   Executes the generated test scripts using appropriate test runners (e.g., `pytest`, `npm test`, `npx playwright test`).
    *   Captures all outputs: stdout, stderr, exit codes, test runner reports, browser console logs, screenshots/videos for UI tests.
6.  **Results Processing & Analysis:**
    *   Parses test runner outputs to determine pass/fail status for each test case.
    *   Calculates summary metrics (total tests, passed, failed, skipped, coverage if available).
7.  **Bug Reporting (if failures):**
    *   For each failed test, creates a structured `BugReport` (as defined for BDA) including:
        *   Test case details, expected vs. actual results.
        *   Error messages, stack traces.
        *   Relevant logs, screenshots.
        *   Link to the failing code version.
    *   Stores `BugReport` in SKB and notifies BDA/Orchestrator.
8.  **Report Generation & Storage:**
    *   Generates a comprehensive `TestExecutionReport`.
    *   Stores the report in the SKB, linked to the tested code version and features.
    *   Notifies Orchestrator/relevant agents of testing completion and overall status.
9.  **Regression Suite Update:**
    *   Successful new test cases are considered for addition to the regression suite.

### 3.2. Key Internal Components:

*   **`QATAgent` Class (e.g., `qata_core.py` - to be created):** Manages the testing workflow.
*   **`LLMInterface` (shared):** For generating test cases and test scripts.
*   **Test Framework Adapters (Conceptual):** Modules to interact with different test runners (PyTest, Jest, Playwright, etc.) and parse their outputs.
*   **`OpenHands` Environment:** For executing tests and interacting with the application under test.

## 4. Data Structures

*   **Input:**
    *   `TestingTask`: `(code_version_ref: str, test_scope: str (e.g., "feature_X_unit", "api_Y_integration", "full_regression"), relevant_specs: List[SKBDocumentLink])`
    *   `ProjectBrief`, `APISpecification`, `FeatureDescription` (from SKB).
    *   Source code files.
*   **Internal State:**
    *   Current test plan.
    *   Generated test cases and scripts.
    *   Test execution environment configuration.
*   **Output (stored in SKB and/or sent to Orchestrator/other agents):**
    *   **`TestPlanDocument`**: Outlines testing strategy, scope, resources.
    *   **`TestCaseCollection`**: Set of generated test cases (could be structured YAML/JSON or embedded in scripts).
    *   **`TestScriptFiles`**: Executable test scripts.
    *   **`TestExecutionReport`**:
        *   `report_id: str`
        *   `tested_code_version: str`
        *   `summary: Dict[str, int]` (total, passed, failed, skipped)
        *   `coverage_metrics: Optional[Dict[str, float]]`
        *   `detailed_results: List[SingleTestResult(test_case_id, status, duration, logs, error_message, screenshot_path)]`
    *   **`BugReport`** (for each failure, passed to BDA).

## 5. API and Interaction Points

*   **FDA (Feature Development Agent) / IDA (Integration & Data Flow Agent):**
    *   Receives code/integrations to be tested (typically via Orchestrator after FDA/IDA signals completion).
    *   Sends `TestExecutionReport` and `BugReport`s back (via Orchestrator/SKB).
*   **BDA (Bug Detection & Debugging Agent):**
    *   Sends detailed `BugReport`s to BDA when tests fail.
    *   May receive notifications from BDA when a fix is ready for re-testing.
*   **DMA (Deployment & Monitoring Agent):**
    *   Requests DMA to set up specific test environments if needed.
    *   Provides validated builds (test pass confirmation) to DMA for deployment to staging/production.
*   **Shared Knowledge Base (SKB):**
    *   **Reads:** `ProjectBrief`, `APISpecification`, `FeatureDescription`, existing test plans, regression suites.
    *   **Writes:** `TestPlanDocument`, `TestExecutionReport`, `BugReport`s, generated test cases/scripts.
*   **LLM Service (`devstral-small` via `LLMInterface`):**
    *   For generating test plans, test cases, and test scripts.
    *   Potentially for analyzing test failures to provide initial diagnostic hints for bug reports.
*   **OpenHands Environment:**
    *   Executes test scripts.
    *   Interacts with the application under test (e.g., making API calls, interacting with UI via Playwright).
    *   Manages test files and artifacts.
*   **Version Control System (via `OpenHands`):**
    *   Checks out specific code versions for testing.
    *   Stores generated test scripts.

## 6. Prompt Engineering Strategies for Testing

Based on Section 4 of the user-provided comprehensive document:

*   **System Prompts:** "You are an expert QA engineer. Based on the following function specification [or user story], generate comprehensive [unit/integration/E2E] test cases."
*   **For Test Case Generation:**
    *   Provide function signatures, API endpoint definitions, user story acceptance criteria.
    *   Instruct LLM to cover positive paths, negative paths, boundary values, error conditions, and common security vulnerabilities (e.g., basic SQL injection, XSS for web).
    *   Request test cases in a structured format (e.g., Gherkin for BDD, or specific fields like: ID, Description, Preconditions, Steps, Expected Result).
*   **For Test Script Generation:**
    *   Provide the generated test cases and the target testing framework (PyTest, Jest, Playwright).
    *   "Generate a PyTest script for the following test cases against this Python function: [code snippet]."
    *   Include examples of existing test scripts to guide style and common setup/teardown patterns.
*   **Chain-of-Thought (CoT):** "To test user login: 1. Test with valid credentials. 2. Test with invalid username. 3. Test with invalid password. 4. Test with empty username. 5. Test with empty password. 6. Test for SQL injection in username field..."
*   **Decomposition:** Break down testing for a complex feature into smaller testable units or user flows.
*   **Reflexion (Conceptual):** "Review these generated test cases. Are they comprehensive? Do they cover critical edge cases? Is there any redundancy?"

## 7. Error Handling & Edge Cases

*   **Flaky Tests:** Identify and flag tests that produce inconsistent results. May require multiple runs or analysis by BDA/FDA.
*   **Test Environment Issues:** Differentiate failures due to the application vs. failures due to the test environment (e.g., database down, service unavailable). Report environment issues to DMA/Orchestrator.
*   **Incomplete/Untestable Specifications:** If requirements are too vague to generate meaningful tests, QATA should flag this and request clarification from MPA.
*   **Test Data Management:** Ensuring appropriate and consistent test data is available for test execution.
*   **Long Test Execution Times:** Identify and report long-running tests; may need optimization or parallelization strategies.

## 8. Dependencies

*   **Internal:**
    *   FDA/IDA: Provide code and integrations for testing.
    *   BDA: Receives bug reports.
    *   DMA: For test environment setup and receiving validated builds.
    *   `LLMInterface`: For LLM communication.
    *   `SharedKnowledgeBaseClient`: For specifications, test plans, reports.
    *   Orchestrator: For task assignment and status reporting.
    *   `OpenHands` environment: For test execution.
*   **External:**
    *   `LocalAI` server with `devstral-small`.
    *   Relevant testing frameworks and libraries (PyTest, Jest, Playwright, Selenium, etc.) available in the `OpenHands` execution sandbox.
    *   Version Control System.

## 9. Future Considerations / Enhancements

*   **AI-Driven Test Data Generation:** Use LLMs to generate realistic and diverse test data.
*   **Visual Regression Testing:** For UIs, integrate tools to compare screenshots and detect visual changes (potentially using `magistral-small` for analysis).
*   **Performance Testing Automation:** Generate and execute performance test scripts (e.g., k6, Locust).
*   **Security Testing Automation:** Generate stubs or configurations for security scanning tools (SAST, DAST).
*   **Test Maintenance Automation:** When code changes, QATA could attempt to automatically update affected test scripts using LLMs.
*   **Exploratory Testing Simulation:** Design agents that can perform more exploratory, less scripted testing to find unexpected bugs.
*   **Coverage Analysis Integration:** Directly parse and report code coverage metrics from test runs.

This document details the design for QATA, the guardian of quality in the agent-driven SDLC.
