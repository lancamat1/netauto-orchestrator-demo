# Dockerfile - Prefect worker image for flows
FROM prefecthq/prefect:3-latest

# Install system dependencies needed for network automation
RUN apt-get update && apt-get install -y \
    git \
    ssh \
    iputils-ping \
    telnet \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/prefect

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN pip install uv && uv sync --frozen --no-dev

# Create directories for runtime code
RUN mkdir -p /opt/prefect/flows

# Set environment variables
ENV PYTHONPATH=/opt/prefect
ENV PREFECT_LOGGING_LEVEL=INFO

# Do NOT copy flow code - it will be pulled from Git at runtime
# The worker will clone code into /opt/prefect/flows at runtime

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD prefect config view || exit 1

# Default command - can be overridden
CMD ["prefect", "worker", "start", "--pool", "netauto-docker-pool"]