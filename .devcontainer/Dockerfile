# Use a Microsoft-provided base image for VS Code dev containers for Python.
# These images come with many common tools pre-installed and are optimized for dev container usage.
# You can find more options here: https://mcr.microsoft.com/en-us/product/devcontainers/python/tags
# We'll pick one with Python 3.11 and Debian.
FROM mcr.microsoft.com/devcontainers/python:0-3.11-bullseye

# Define arguments for non-root user creation (VS Code standard)
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Install system dependencies:
# - git: For version control
# - docker-ce-cli: To allow the container to talk to the host's Docker daemon (Docker-outside-of-Docker)
# - sudo: So the vscode user can install global node packages if needed, or other minor admin tasks
# - gnupg, apt-transport-https, ca-certificates, curl, lsb-release: For adding Docker repository
# - Other useful utilities: jq (for JSON processing in shell), procps (for `ps` command etc.)
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends     git     sudo     gnupg     apt-transport-https     ca-certificates     curl     lsb-release     jq     procps \
    # Install Docker CE CLI
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo       "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian       $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    # Clean up
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Create the non-root user and grant sudo無password access
# This is a common pattern for VS Code dev containers
RUN if id "$USERNAME" &>/dev/null; then         echo "$USERNAME user exists"     ;else         groupadd --gid $USER_GID $USERNAME \
        && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
        && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
        && chmod 0440 /etc/sudoers.d/$USERNAME     ;fi

# Optional: Install Node.js (LTS version) using nvm for flexibility
# This allows developers to use Node.js based tools or work on potential JS parts of the project
ENV NVM_DIR=/home/$USERNAME/.nvm
ENV NODE_VERSION=--lts
RUN mkdir -p $NVM_DIR && chown -R $USERNAME:$USERNAME $NVM_DIR \
    && su $USERNAME -c "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash" \
    && su $USERNAME -c "source $NVM_DIR/nvm.sh && nvm install $NODE_VERSION && nvm alias default $NODE_VERSION && nvm use default"

# Set ENV for Node.js so it's available in terminals
ENV PATH=$NVM_DIR/versions/node/$(su $USERNAME -c "source $NVM_DIR/nvm.sh && nvm current")/bin:$PATH

# Copy project requirements file and install Python dependencies
# This assumes requirements.txt is in the root of the project (context of the Docker build)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# [Optional] If you have other specific Python tools for development (e.g., linters, formatters)
# you can install them here globally in the container's Python environment:
# RUN pip install --no-cache-dir flake8 black isort

# Application-specific settings or setup can go here
# For example, setting a working directory
WORKDIR /workspace

# Ensure the workspace directory exists and set permissions for the non-root user
# The actual mounting of the project code into /workspace will be handled by devcontainer.json or docker-compose
RUN mkdir -p /workspace && chown -R $USERNAME:$USERNAME /workspace

# Switch to non-root user
USER $USERNAME

# Any default command can be overridden by devcontainer.json or docker-compose
CMD ["/bin/bash"]
