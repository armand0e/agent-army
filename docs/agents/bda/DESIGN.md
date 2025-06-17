# DESIGN DOCUMENT: Bug Detection & Debugging Agent (BDA)

## 1. Overview

The Bug Detection & Debugging Agent (BDA) is a specialized component within the multi-agent SaaS development system. Its primary objective is to automate the process of identifying, diagnosing, and suggesting (or even implementing and validating) fixes for bugs found in the codebase. The BDA works in close collaboration with the Feature Development Agent (FDA) and the Quality Assurance & Testing Agent (QATA) to improve code quality and reduce development friction.

It leverages Large Language Models (e.g., `devstral-small` via `LocalAI`) for sophisticated analysis of error messages, code context, and test failures. It also utilizes sandboxed execution environments (via `OpenHands` and `open-codex` principles) to safely test potential fixes.

## 2. Role & Responsibilities

*   **Bug Report Ingestion:** Receive and parse bug reports from QATA (e.g., failing test cases, stack traces) or issues flagged by FDA during development (e.g., persistent compilation errors).
*   **Root Cause Analysis (RCA):** Analyze the provided bug information (code, error messages, test outputs, execution logs) to determine the underlying cause of the defect.
*   **Fix Suggestion/Generation:** Propose potential code modifications to fix the identified bug. This can range from suggesting specific lines of code to generating complete diffs or patched code blocks.
*   **Fix Application (Optional/Supervised):** Apply generated patches or code modifications to a temporary/branched version of the codebase.
*   **Fix Validation:** Test the applied fix in a sandboxed environment to ensure it resolves the original bug without introducing regressions. This involves re-running the failing test case(s) and potentially a broader set of related tests.
*   **Feedback to FDA/QATA:** Communicate the outcome of the debugging process:
    *   If successful, provide the patched code and validation results to FDA.
    *   If unsuccessful or if multiple potential fixes exist, provide diagnostic insights and suggestions to FDA.
*   **Knowledge Base Contribution:** Log common bug patterns, their resolutions, and diagnostic steps to the Shared Knowledge Base (SKB) to aid future debugging efforts and potentially train specialized bug detection models.
*   **Learning from Errors:** As per its description in the guiding document, analyze previous mistakes in its own diagnostic process to develop more robust strategies.

## 3. Core Logic & Operations

### 3.1. Workflow (per bug report):

1.  **Bug Report Reception:** Receives a bug report. This report (a structured data object) should contain:
    *   Reference to the affected code file(s) and version.
    *   Failing test case(s) (input, expected output, actual output).
    *   Error messages, stack traces.
    *   Logs from QATA's execution.
2.  **Contextual Information Gathering:**
    *   Retrieves the specified version of the affected code from the VCS (via `OpenHands`).
    *   Fetches relevant documentation, API specifications, or design notes from the SKB that might pertain to the buggy module.
3.  **Root Cause Analysis (LLM-driven):**
    *   Constructs a detailed prompt for `devstral-small` including:
        *   The bug report details.
        *   The relevant code snippet(s).
        *   (Optionally) Execution history or state just before the error.
    *   The prompt will ask the LLM to:
        *   Explain the likely cause of the error.
        *   Identify the specific lines of code responsible.
        *   Suggest a debugging approach or hypothesis.
    *   May involve multiple LLM calls, potentially using CoT or ToT prompting to explore different diagnostic paths.
4.  **Fix Generation (LLM-driven):**
    *   Based on the RCA, prompts the LLM to generate a code patch or modified code block to fix the bug.
    *   The prompt should emphasize minimizing side effects and adhering to existing coding style.
    *   May request the fix in a specific format (e.g., a diff).
5.  **Fix Application & Sandboxed Testing (OpenHands & Open Codex Principle):**
    *   Creates a temporary branch or isolated copy of the code.
    *   Applies the generated patch/fix using file manipulation tools (via `OpenHands`).
    *   Re-runs the originally failing test case(s) within the sandboxed environment.
    *   (Optionally) Runs a small suite of related regression tests.
6.  **Iterative Refinement (if fix fails):**
    *   If the fix doesn't work or introduces new errors:
        *   Collects the new error information.
        *   Feeds this back to the LLM (similar to `openevolve`'s Artifacts Channel) along with the previous fix attempt.
        *   Requests a revised fix.
        *   Repeats step 5. This loop continues for a configured number of attempts.
7.  **Reporting Results:**
    *   **Success:** If the fix is validated, the BDA:
        *   Commits the fix to a specific bugfix branch.
        *   Notifies FDA/Orchestrator with the branch name and details of the fix.
        *   Updates the bug report status in the SKB or issue tracker.
    *   **Failure/Requires Human Intervention:** If BDA cannot find a fix after several attempts, or if the bug is too complex:
        *   Compiles a diagnostic report including:
            *   Summary of hypotheses tested.
            *   Fixes attempted and their outcomes.
            *   Relevant logs and code snippets.
            *   LLM's final assessment or areas of confusion.
        *   Stores this report in the SKB and notifies FDA/Orchestrator that manual intervention is likely needed.

### 3.2. Key Internal Components:

*   **`BDAgent` Class (e.g., `bda_core.py` - to be created):** Orchestrates the debugging workflow.
*   **`LLMInterface` (shared):** For diagnostic reasoning and fix generation.
*   **Code Analysis Tools (Conceptual):** Could potentially integrate static analyzers or symbolic execution tools if available and beneficial, though primary reliance is on LLM.
*   **Test Execution Module (via `OpenHands` or QATA interface):** To run specific tests.
*   **VCS Interaction Module (via `OpenHands`):** To manage code branches and apply patches.

## 4. Data Structures

*   **Input:**
    *   `BugReport` (structured data from QATA/FDA):
        *   `report_id: str`
        *   `source_agent_id: str` (e.g., QATA-123)
        *   `affected_code_references: List[CodeFileReference(file_path, commit_hash_or_branch)]`
        *   `failing_tests: List[TestResult(test_name, input, expected_output, actual_output, error_message, stack_trace)]`
        *   `additional_logs: Optional[List[str]]`
        *   `severity: Optional[str]`
*   **Internal State:**
    *   Current diagnostic hypotheses.
    *   Attempted fixes and their results.
    *   Conversation history with LLM for the current bug.
*   **Output:**
    *   `FixConfirmationReport`:
        *   `bug_report_id: str`
        *   `status: str` (e.g., "FIXED", "PARTIALLY_FIXED", "NOT_FIXED", "NEEDS_HUMAN_REVIEW")
        *   `applied_fix_diff: Optional[str]`
        *   `validation_test_results: List[TestResult]`
        *   `fix_commit_hash: Optional[str]`
        *   `diagnostic_summary: str`
    *   Patched code files (committed to VCS).

## 5. API and Interaction Points

*   **QATA / FDA (via Orchestrator & SKB/Message Bus):**
    *   **Receives:** `BugReport` objects.
    *   **Sends:** `FixConfirmationReport`, requests for re-testing, or notifications for manual review.
*   **Shared Knowledge Base (SKB):**
    *   **Reads:** `BugReport` details, source code, design documents, past similar issues and resolutions.
    *   **Writes:** `FixConfirmationReport`, diagnostic summaries, learned bug patterns.
*   **LLM Service (`devstral-small` via `LLMInterface`):**
    *   Sends prompts for root cause analysis, code explanation, fix generation.
    *   Receives textual explanations, code snippets, diffs.
*   **Version Control System (via `OpenHands`):**
    *   Checks out code, creates branches, applies patches, commits fixes.
*   **OpenHands Environment:**
    *   For executing tests in a sandbox, running code snippets, file system operations.

## 6. Prompt Engineering Strategies for Debugging

Based on Section 4 of the user-provided comprehensive document:

*   **System Prompts:** "You are an expert software debugger. Given the following code, error message, and failing test, explain the root cause of the bug and suggest a fix."
*   **Chain-of-Thought (CoT):**
    *   "Let's analyze this bug step-by-step. First, what does the error message mean? Second, which part of the code is implicated by the stack trace? Third, how does the failing test's input relate to this code section? ..."
*   **Decomposition Prompting:** Break down complex debugging into:
    1.  Understand the error.
    2.  Localize the fault.
    3.  Hypothesize causes.
    4.  Suggest code changes for a hypothesis.
*   **Few-Shot Examples:** Provide examples of similar bugs and their fixes, or common debugging patterns for the specific language/framework.
*   **Reflexion Prompting:**
    *   After LLM suggests a fix: "Review this proposed fix. Does it address the root cause? Could it introduce any side effects? Is there a simpler or more robust solution?"
    *   After a fix attempt fails: "The previous fix did not work and resulted in [new error/same error]. Analyze why the fix failed and propose an alternative approach."
*   **Contextual Information:** Provide as much relevant context as possible:
    *   The exact error message and stack trace.
    *   The failing test code and its input/output.
    *   The source code snippet where the error likely occurs (and surrounding lines).
    *   Relevant data structures or API definitions.

## 7. Error Handling & Edge Cases

*   **Non-Reproducible Bugs:** If the BDA cannot reproduce the bug in its sandboxed environment, it should report this back.
*   **Intermittent Bugs:** These are very hard for automated systems. BDA might need to run tests multiple times or suggest adding more logging.
*   **Bugs in External Dependencies/Environment:** BDA should try to differentiate these from bugs in the application code. May require specific prompting or tools.
*   **LLM Cannot Diagnose or Fix:** After a set number of retries or if the LLM consistently provides unhelpful suggestions, escalate for human review with a full diagnostic report.
*   **Fix Causes Regressions:** If the applied fix makes other tests fail, it should be reverted, and the new failure information should be used to refine the next fix attempt.

## 8. Dependencies

*   **Internal:**
    *   QATA/FDA: For providing bug reports.
    *   `LLMInterface`: For LLM communication.
    *   `SharedKnowledgeBaseClient`: For accessing bug details, code, and storing reports.
    *   Orchestrator: For task assignment and status reporting.
    *   `OpenHands` environment: For sandboxed execution, VCS, file system.
    *   (Conceptual) `open-codex` logic: For controlled code application and execution.
*   **External:**
    *   `LocalAI` server with `devstral-small`.
    *   Version Control System (e.g., Git).
    *   Test execution frameworks relevant to the project's tech stack.

## 9. Future Considerations / Enhancements

*   **Predictive Bug Detection:** Analyze code changes proactively (before QATA testing) to predict potential bugs.
*   **Automated Test Case Generation for Debugging:** If a bug is hard to pinpoint, BDA could ask an LLM to generate new, more specific test cases to isolate the issue.
*   **Learning Common Bug Patterns:** Maintain a database of bug types and successful fix strategies for the specific codebase/domain, and use this to improve LLM prompts for future debugging.
*   **Integration with Static/Dynamic Analysis Tools:** Use outputs from advanced analysis tools as further input for LLM diagnosis.
*   **Explainable Fixes:** Ensure that when BDA suggests or applies a fix, it also provides a clear explanation of why the fix works, for human developers to understand.

This document provides the design for the BDA, an essential agent for maintaining code quality through automated debugging.
