#!/bin/bash

# Script to launch and configure OpenHands for orchestration tasks

# --- Configuration ---
# User's LLM API details (ideally use environment variables for sensitive data)
USER_LLM_BASE_URL="${OH_USER_LLM_BASE_URL:-https://lm.armand0e.online/v1}"
USER_LLM_API_KEY="${OH_USER_LLM_API_KEY:-sk-291923902182902-kd}" # Be cautious with hardcoding keys
# Model alias for devstral-small on the user's endpoint
ORCHESTRATOR_MODEL_NAME="gpt-3.5-turbo"

# OpenHands Docker image and container name
OPENHANDS_IMAGE_NAME="docker.all-hands.dev/all-hands-ai/openhands:0.43" # Use a recent version
# IMPORTANT: For the "Preconfigured Workspace", this would be our custom image, e.g., "agentic_saas_factory/openhands-sandbox-codex:latest"
# For now, we'll use the standard image and rely on the custom_instructions.
SANDBOX_IMAGE_NAME="docker.all-hands.dev/all-hands-ai/runtime:0.43-nikolaik" # Standard sandbox
OPENHANDS_CONTAINER_NAME="openhands-orchestrator-instance"
OPENHANDS_PORT="3000" # Default OpenHands UI port
SANDBOX_VOLUMES="/home/armand0e/dev:/workspace:rw"
# Path to OpenHands state directory (on the host)
# This will store settings.json and other state
HOST_OPENHANDS_STATE_DIR="$HOME/.openhands-orchestrator-state"
CONTAINER_OPENHANDS_STATE_DIR="/.openhands-state" # Mount point inside the OpenHands container

# Path to the settings template
SETTINGS_TEMPLATE_PATH="../configs/openhands_templates/settings.template.json"
SETTINGS_JSON_PATH="$HOST_OPENHANDS_STATE_DIR/settings.json"

# Workspace mapping (optional, maps a local directory into OpenHands' /workspace)
# HOST_WORKSPACE_DIR="$PWD/orchestrator_workspace" # Example: current_dir/orchestrator_workspace
# CONTAINER_WORKSPACE_DIR="/workspace"

# --- Script Functions ---
cleanup_old_instance() {
  echo "INFO: Checking for existing OpenHands container named '$OPENHANDS_CONTAINER_NAME'..."
  if [ "$(docker ps -q -f name=$OPENHANDS_CONTAINER_NAME)" ]; then
    echo "INFO: Stopping existing container '$OPENHANDS_CONTAINER_NAME'..."
    docker stop $OPENHANDS_CONTAINER_NAME
  fi
  if [ "$(docker ps -aq -f name=$OPENHANDS_CONTAINER_NAME)" ]; then
    echo "INFO: Removing existing container '$OPENHANDS_CONTAINER_NAME'..."
    docker rm $OPENHANDS_CONTAINER_NAME
  fi
}

prepare_settings() {
  echo "INFO: Preparing OpenHands state directory at '$HOST_OPENHANDS_STATE_DIR'..."
  mkdir -p "$HOST_OPENHANDS_STATE_DIR"

  if [ ! -f "$SETTINGS_TEMPLATE_PATH" ]; then
    echo "ERROR: Settings template not found at '$SETTINGS_TEMPLATE_PATH'"
    exit 1
  fi

  echo "INFO: Creating/Updating OpenHands settings file at '$SETTINGS_JSON_PATH'..."

  # Replace placeholders in the template
  # Using awk for simple JSON manipulation to avoid jq dependency for this script
  awk \
    -v model="$ORCHESTRATOR_MODEL_NAME" \
    -v key="$USER_LLM_API_KEY" \
    -v url="$USER_LLM_BASE_URL" \
    '{
      # For llm_api_key and llm_base_url, we need to match the literal string
      # and then replace it, ensuring quotes are handled correctly for JSON.
      # For llm_model, we replace its default value "gpt-3.5-turbo" with the ORCHESTRATOR_MODEL_NAME.
      # The custom_instructions are long and contain quotes, so direct gsub might be tricky.
      # It is safer if the template has distinct placeholders for these.
      # Assuming the template has "YOUR_API_KEY_HERE", "YOUR_LLM_BASE_URL_HERE", and "gpt-3.5-turbo" for model.

      sub("\"llm_api_key\": \".*\"", "\"llm_api_key\": \"" key "\"");
      sub("\"llm_base_url\": \".*\"", "\"llm_base_url\": \"" url "\"");
      sub("\"llm_model\": \"gpt-3.5-turbo\"", "\"llm_model\": \"" model "\"");
      print;
    }' "$SETTINGS_TEMPLATE_PATH" > "$SETTINGS_JSON_PATH"


  if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create settings.json."
    exit 1
  fi
  echo "INFO: settings.json configured successfully:"
  echo "  LLM Base URL: $USER_LLM_BASE_URL"
  echo "  LLM Model: $ORCHESTRATOR_MODEL_NAME"
  echo "  (API key is set but not displayed)"
}

launch_openhands() {
  echo "INFO: Pulling latest OpenHands image '$OPENHANDS_IMAGE_NAME' (if needed)..."
  docker pull "$OPENHANDS_IMAGE_NAME"
  echo "INFO: Pulling latest OpenHands sandbox image '$SANDBOX_IMAGE_NAME' (if needed)..."
  docker pull "$SANDBOX_IMAGE_NAME"

  echo "INFO: Launching OpenHands container '$OPENHANDS_CONTAINER_NAME'..."

  # Workspace mount command part - uncomment and adjust HOST_WORKSPACE_DIR if needed
  # WORKSPACE_MOUNT_CMD="-v "$HOST_WORKSPACE_DIR":"$CONTAINER_WORKSPACE_DIR""

  # Note: The --add-host host.docker.internal:host-gateway is for the sandbox to reach the host if needed.
  # If your LLM is also running in Docker on the same machine, network settings might need adjustment
  # or use host.docker.internal as the LLM URL if OpenHands/sandbox can resolve it.
  # For an external LLM URL (like the user provided), this should be fine.

  docker run -d --rm \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE="$SANDBOX_IMAGE_NAME" \
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=$SANDBOX_VOLUMES \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$HOST_OPENHANDS_STATE_DIR":"$CONTAINER_OPENHANDS_STATE_DIR" \
    $WORKSPACE_MOUNT_CMD \
    -p "$OPENHANDS_PORT":8001 \
    --add-host host.docker.internal:host-gateway \
    --name "$OPENHANDS_CONTAINER_NAME" \
    "$OPENHANDS_IMAGE_NAME"

  if [ $? -ne 0 ]; then
    echo "ERROR: Failed to launch OpenHands container."
    echo "Please check Docker logs for '$OPENHANDS_CONTAINER_NAME'."
    exit 1
  fi

  echo ""
  echo "SUCCESS: OpenHands Orchestrator instance '$OPENHANDS_CONTAINER_NAME' should be starting."
  echo "Access the UI at: http://localhost:$OPENHANDS_PORT"
  echo "It is configured to use your LLM for orchestration tasks."
  echo "Default Agent Instructions (System Prompt) set for Orchestration behavior."
  echo "To see logs: docker logs -f $OPENHANDS_CONTAINER_NAME"
  echo "To stop: docker stop $OPENHANDS_CONTAINER_NAME"
}

# --- Main Execution ---
cleanup_old_instance
prepare_settings
launch_openhands

exit 0
