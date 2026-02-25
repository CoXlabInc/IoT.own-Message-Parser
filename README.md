# IoT.own Message Parser

> **Note:** This message parser is only applicable to **IoT.own legacy (v4)**.

This directory contains the Docker build environment and source code for the IoT.own Message Parser. This component is designed to be built independently and may not always be managed as a submodule.

## Build Instructions

Build the Docker image using standard Docker commands. These commands should be executed from within the `pp` directory.

### 1. Standard Build (Local Architecture)
To build the image for your current machine's architecture:

```bash
docker build -t iotown-message-parser:latest .
```

### 2. Multi-Platform Build
To build for a specific target architecture (e.g., for deployment on different hardware), use `docker buildx`:

*   **For ARM64 (e.g., Raspberry Pi):**
    ```bash
    docker buildx build --platform linux/arm64 -t iotown-message-parser:latest .
    ```

*   **For AMD64 (Standard x86_64):**
    ```bash
    docker buildx build --platform linux/amd64 -t iotown-message-parser:latest .
    ```

## Exporting and Importing the Image

### 1. Export to File
To save the built image as a compressed archive for distribution:

```bash
docker save iotown-message-parser:latest | gzip > iotown-message-parser_latest.tar.gz
```

### 2. Import from File
To load the image from an existing archive file:

```bash
docker load -i iotown-message-parser_latest.tar.gz
```

## Directory Structure
- `Dockerfile`: Defines the Docker image build process for the message parser.
- `parser/`: Contains the core logic and scripts for message parsing.
- `docker-compose.yml`: Docker Compose configuration for local testing.

---
Assisted by Google Gemini
