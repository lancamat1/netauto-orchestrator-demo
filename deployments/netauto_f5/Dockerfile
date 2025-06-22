FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set the working directory
WORKDIR /app

# Set environment variables
ENV UV_SYSTEM_PYTHON=1
ENV PATH="/root/.local/bin:$PATH"

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker cache
COPY ./deployments/netauto_f5/requirements.txt ./requirements.txt

RUN uv pip install prefect

# Install dependencies
RUN uv pip install -r requirements.txt
