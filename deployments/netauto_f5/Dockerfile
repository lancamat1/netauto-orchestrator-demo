FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set the working directory
WORKDIR /app

# Set environment variables
ENV UV_SYSTEM_PYTHON=1
ENV PATH="/root/.local/bin:$PATH"

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN uv pip install prefect

COPY ./deployments/netauto_f5/requirements.txt ./requirements.txt

# Install dependencies
RUN uv pip install -r requirements.txt

# Install the F5 AS3 SDK
COPY ./deployments/netauto_f5/f5_as3_sdk ./f5_as3_sdk
RUN uv pip install ./f5_as3_sdk

