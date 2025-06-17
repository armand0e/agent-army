# Host System Prerequisites for LocalAI with AMD ROCm GPU

This document outlines the necessary checks to ensure your host system is ready to run LocalAI with AMD GPU acceleration (specifically for ROCm-compatible GPUs like the AMD 6900XT).

Please verify the following on your host machine:

1.  **Supported Linux Distribution:**
    *   **Verification:** Check that your Linux distribution and version are officially supported by the AMD ROCm software stack.
    *   **Command (example):** `cat /etc/os-release` or `lsb_release -a`
    *   **Reference:** [AMD ROCm OS Support](https://rocm.docs.amd.com/en/latest/release/gpu_os_support.html)

2.  **AMD GPU Drivers & ROCm Stack Installation:**
    *   **Verification:** Ensure that the correct AMD GPU drivers and a compatible version of the ROCm stack are installed. Your GPU (e.g., AMD 6900XT - Navi 21/gfx1030) must be supported by the installed ROCm version.
    *   **Commands (if ROCm is installed):**
        *   `rocminfo` (should display GPU details and ROCm version)
        *   `rocm-smi` (should display GPU status)
    *   **Action (if not installed/incompatible):** Follow the official AMD ROCm installation guide for your Linux distribution.
    *   **Reference:** [AMD ROCm Installation Guide](https://rocm.docs.amd.com/en/latest/deploy/linux/index.html)
    *   **Note:** The host ROCm version should ideally align with the ROCm version used in the LocalAI Docker images for AMD GPUs.

3.  **Docker Installation & Configuration:**
    *   **Verification:** Docker Engine must be installed, and the Docker daemon should be running.
    *   **Commands:**
        *   `docker --version`
        *   `sudo systemctl status docker` (or equivalent)
    *   **User Group:** It's highly recommended that your user account is part of the `docker` group to run Docker commands without `sudo`.
    *   **Action (if not installed):** Follow the official Docker installation guide.
    *   **Reference:** [Docker Engine Installation](https://docs.docker.com/engine/install/)

4.  **System Updates:**
    *   **Verification:** Ensure your system, particularly the kernel, is reasonably up-to-date.
    *   **Command (example for Ubuntu):** `sudo apt update && sudo apt list --upgradable && sudo apt upgrade`
    *   **Note:** A reboot may be required after kernel updates.

5.  **GPU Device Files:**
    *   **Verification:** Confirm the existence of necessary GPU device files in `/dev`. These typically include `/dev/kfd` and DRI render nodes like `/dev/dri/renderD128`.
    *   **Note:** These are usually created automatically upon successful ROCm driver installation. The LocalAI Docker command for AMD GPUs relies on mapping these devices (e.g., `--device=/dev/kfd --device=/dev/dri`).

Verifying these prerequisites is crucial before attempting to run LocalAI with GPU acceleration.
