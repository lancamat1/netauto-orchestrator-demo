# Prefect Deployment Strategy for NetAuto Orchestrator

## Overview

This plan outlines the optimal Prefect 3.0 deployment architecture for your NetAuto orchestrator, focusing on a single Docker executor with Git-based code synchronization for maximum flexibility and maintainability.

## Deployment Architecture

### Recommended Pattern: Git-Based Storage with Single Docker Worker

Based on your requirements, the optimal approach is:

1. **Single Docker Worker Pool**: One Docker work pool running a persistent worker
2. **Git-Based Code Storage**: Flow code stored in this repository, pulled at runtime
3. **Custom Base Image**: Single Docker image with all dependencies, but not flow code
4. **Event-Driven Execution**: Webhook receiver triggers deployments via Prefect API

## Detailed Implementation Plan

### 1. Docker Infrastructure Setup

#### 1.1 Repository Structure and Responsibilities

Given you have a separate webhook handler repository, here's the recommended structure:

**This Repository (netauto-orchestrator):**
- Flow code and Prefect worker Dockerfile
- Prefect deployment configurations
- Flow-specific dependencies and libraries

**Webhook Handler Repository:**
- FastAPI webhook receiver
- Webhook routing and validation logic
- Integration with Prefect API for flow triggering

**Infrastructure Repository (Recommended):**
- Docker Compose for entire solution
- Environment configurations
- Secrets management
- Deployment scripts

#### 1.2 Prefect Worker Dockerfile (Place in THIS repository)
```dockerfile
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
```

#### 1.3 Docker Work Pool Configuration
```yaml
# docker-work-pool.yaml
name: netauto-docker-pool
type: docker
base_job_template:
  job_configuration:
    # Use your custom base image
    image: "your-registry/netauto-base:latest"
    image_pull_policy: "Always"
    
    # Environment variables
    env:
      INFRAHUB_API_URL: "{{ infrahub_api_url }}"
      INFRAHUB_API_TOKEN: "{{ infrahub_api_token }}"
      PREFECT_LOGGING_LEVEL: "INFO"
    
    # Resource limits
    cpu_limit: 1.0
    memory_limit: "2Gi"
    cpu_request: 0.5
    memory_request: "1Gi"
    
    # Network configuration for webhook access
    networks:
      - netauto-network

  variables:
    # Templated variables for different environments
    infrahub_api_url:
      default: "http://infrahub.netauto.alef.dc"
    infrahub_api_token:
      default: "{{ prefect.blocks.secret.infrahub-token }}"
```

### 2. Flow Organization Strategy

#### 2.1 Repository Structure
```
netauto-orchestrator/
├── flows/
│   ├── __init__.py
│   ├── common/
│   │   ├── __init__.py
│   │   ├── blocks.py          # Prefect blocks
│   │   ├── models.py          # Data models
│   │   ├── utils.py           # Shared utilities
│   │   └── webhooks.py        # Webhook handling
│   │
│   ├── f5/
│   │   ├── __init__.py
│   │   ├── deploy_as3.py      # F5 AS3 deployments
│   │   ├── deploy_ltm.py      # F5 LTM configurations
│   │   └── deploy_certs.py    # Certificate management
│   │
│   ├── sync/
│   │   ├── __init__.py
│   │   ├── inventory.py       # Device inventory sync
│   │   ├── configs.py         # Configuration backup
│   │   └── validation.py      # Validation results
│   │
│   └── events/
│       ├── __init__.py
│       ├── webhook_handler.py # Infrahub webhook processor
│       └── notifications.py  # Event notifications
│
├── deployments/
│   ├── production.py         # Production deployment script
│   ├── staging.py            # Staging deployment script
│   └── dev.py               # Development deployment script
│
├── docker/
│   ├── Dockerfile.base       # Base image with dependencies
│   ├── docker-compose.yml    # Local development
│   └── worker-config.yaml    # Worker configuration
│
└── webhook/
    ├── __init__.py
    ├── receiver.py           # FastAPI webhook receiver
    └── dispatcher.py         # Flow dispatch logic
```

#### 2.2 Git-Based Deployment Configuration

Each deployment will use `from_source` to pull code from this repository:

```python
# deployments/production.py
from prefect import flow
from prefect.client.schemas.schedules import CronSchedule

# F5 AS3 Deployment (Event-driven)
f5_as3_deployment = flow.from_source(
    source="https://github.com/your-org/netauto-orchestrator.git",
    entrypoint="flows/f5/deploy_as3.py:deploy_f5_as3_application"
).to_deployment(
    name="f5-as3-production",
    work_pool_name="netauto-docker-pool",
    description="Deploy F5 AS3 applications triggered by Infrahub events",
    tags=["f5", "as3", "production", "event-driven"],
    parameters={"environment": "production"},
    # No schedule - triggered by webhooks
)

# Scheduled Inventory Sync
inventory_sync_deployment = flow.from_source(
    source="https://github.com/your-org/netauto-orchestrator.git",
    entrypoint="flows/sync/inventory.py:sync_network_inventory"
).to_deployment(
    name="inventory-sync-production",
    work_pool_name="netauto-docker-pool",
    description="Scheduled network inventory synchronization",
    tags=["sync", "inventory", "production", "scheduled"],
    schedule=CronSchedule(cron="0 */6 * * *"),  # Every 6 hours
    parameters={"environment": "production"}
)

# Config Backup Sync
config_sync_deployment = flow.from_source(
    source="https://github.com/your-org/netauto-orchestrator.git", 
    entrypoint="flows/sync/configs.py:backup_device_configs"
).to_deployment(
    name="config-backup-production",
    work_pool_name="netauto-docker-pool",
    description="Daily configuration backup and sync",
    tags=["sync", "backup", "production", "scheduled"],
    schedule=CronSchedule(cron="0 2 * * *"),  # Daily at 2 AM
    parameters={"environment": "production"}
)

if __name__ == "__main__":
    # Deploy all flows
    deploy(
        f5_as3_deployment,
        inventory_sync_deployment,
        config_sync_deployment,
        work_pool_name="netauto-docker-pool"
    )
```

### 3. Webhook Integration Architecture

#### 3.1 Webhook Handler Integration (In your existing webhook repository)

Since you already have a webhook handler repository, you'll need to add Prefect integration:

```python
# In your webhook handler repository
# webhook_handlers/prefect_dispatcher.py
from prefect.client.orchestration import PrefectClient
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PrefectFlowDispatcher:
    """Dispatches Infrahub events to appropriate Prefect flows."""
    
    def __init__(self, prefect_api_url: str, prefect_api_key: Optional[str] = None):
        self.client = PrefectClient(
            api=prefect_api_url,
            api_key=prefect_api_key
        )
        
        # Mapping of Infrahub events to Prefect deployments
        self.deployment_mapping = {
            "infrahub.artifact.updated": {
                "NetautoFlexApplication": "f5-as3-production",
                "NetautoLTMConfig": "f5-ltm-production", 
                "NetautoCertificate": "f5-cert-production",
                "NetautoRoutingConfig": "routing-deploy-production"
            },
            "infrahub.node.created": {
                "NetworkDevice": "inventory-sync-production"
            },
            "infrahub.validation.completed": {
                "*": "validation-processor-production"
            }
        }
    
    async def dispatch_flow(self, event_type: str, target_kind: str, payload: Dict) -> str:
        """
        Dispatch appropriate Prefect flow based on event and target type.
        
        Returns:
            Flow run ID if successful
        """
        # Get deployment name
        deployments = self.deployment_mapping.get(event_type, {})
        deployment_name = deployments.get(target_kind) or deployments.get("*")
        
        if not deployment_name:
            logger.warning(f"No deployment mapping for {event_type}:{target_kind}")
            return None
        
        try:
            # Create flow run
            flow_run = await self.client.create_flow_run_from_deployment(
                deployment_name=deployment_name,
                parameters={"webhook_data": payload}
            )
            
            logger.info(f"Dispatched flow run {flow_run.id} for {deployment_name}")
            return flow_run.id
            
        except Exception as e:
            logger.error(f"Failed to dispatch flow {deployment_name}: {e}")
            raise

# Integration with your existing webhook handler
async def handle_infrahub_event(event_data: dict):
    """Add this to your existing webhook processing logic."""
    dispatcher = PrefectFlowDispatcher(
        prefect_api_url=os.getenv("PREFECT_API_URL"),
        prefect_api_key=os.getenv("PREFECT_API_KEY")
    )
    
    flow_run_id = await dispatcher.dispatch_flow(
        event_data["event"],
        event_data["data"]["target_kind"],
        event_data
    )
    
    return {"flow_run_id": flow_run_id, "status": "dispatched"}
```

#### 3.2 Environment Configuration for Webhook Handler

Add these to your webhook handler's environment configuration:

```bash
# Prefect integration
PREFECT_API_URL=https://your-prefect-server/api
PREFECT_API_KEY=your-prefect-api-key

# Flow dispatch configuration
NETAUTO_FLOW_DISPATCH_ENABLED=true
NETAUTO_FLOW_TIMEOUT=300
```

### 4. Block and Configuration Strategy

#### 4.1 Environment-Specific Blocks
```python
# flows/common/blocks.py
from prefect.blocks.core import Block
from pydantic import SecretStr

class NetAutoConfig(Block):
    """Environment-specific configuration block."""
    
    environment: str
    infrahub_url: str
    infrahub_token: SecretStr
    f5_credentials: dict
    notification_settings: dict
    
    _block_type_name = "NetAuto Config"
    _block_type_slug = "netauto-config"
    
    class Config:
        # Block configurations per environment
        schema_extra = {
            "examples": [
                {
                    "environment": "production",
                    "infrahub_url": "https://infrahub.netauto.alef.dc",
                    "infrahub_token": "prod-token-here",
                    "f5_credentials": {
                        "default_username": "admin",
                        "default_password": "secret"
                    }
                }
            ]
        }
```

#### 4.2 Dynamic Block Loading
```python
# flows/common/utils.py
async def get_environment_config(environment: str = "production"):
    """Load environment-specific configuration."""
    try:
        config = await NetAutoConfig.load(f"netauto-config-{environment}")
        return config
    except Exception:
        # Fallback to default config
        return await NetAutoConfig.load("netauto-config-default")
```

### 5. Deployment Workflow

#### 5.1 CI/CD Pipeline Integration
```yaml
# .github/workflows/deploy.yml
name: Deploy NetAuto Flows

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"
          
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
          
      - name: Deploy to Production
        run: |
          python deployments/production.py
        env:
          PREFECT_API_URL: ${{ secrets.PREFECT_API_URL }}
          PREFECT_API_KEY: ${{ secrets.PREFECT_API_KEY }}
```

#### 5.2 Docker Compose Placement Strategy

**Recommended: Create a separate infrastructure repository** for the complete solution:

```
netauto-infrastructure/
├── docker-compose.yml              # Complete solution stack
├── docker-compose.dev.yml          # Development overrides
├── docker-compose.prod.yml         # Production overrides
├── .env.example                    # Environment template
├── configs/
│   ├── prefect/                    # Prefect server config
│   ├── infrahub/                   # Infrahub configuration
│   └── traefik/                    # Load balancer config
├── scripts/
│   ├── setup.sh                    # Environment setup
│   ├── deploy.sh                   # Deployment script
│   └── backup.sh                   # Backup utilities
└── kubernetes/                     # K8s manifests (if using K8s)
    ├── namespace.yaml
    ├── prefect-worker.yaml
    └── webhook-handler.yaml
```

#### 5.3 Complete Docker Compose Solution

**Place this in your infrastructure repository:**

```yaml
# docker-compose.yml - Complete NetAuto solution
version: '3.8'

networks:
  netauto:
    driver: bridge

volumes:
  prefect_data:
  postgres_data:
  infrahub_data:

services:
  # PostgreSQL for Prefect
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: prefect
      POSTGRES_USER: prefect
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - netauto
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U prefect"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Prefect Server
  prefect-server:
    image: prefecthq/prefect:3-latest
    command: prefect server start --host 0.0.0.0
    environment:
      PREFECT_API_DATABASE_CONNECTION_URL: postgresql+asyncpg://prefect:${POSTGRES_PASSWORD}@postgres:5432/prefect
      PREFECT_SERVER_API_HOST: 0.0.0.0
    ports:
      - "4200:4200"
    networks:
      - netauto
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - prefect_data:/opt/prefect

  # NetAuto Prefect Worker
  netauto-worker:
    build:
      context: https://github.com/your-org/netauto-orchestrator.git
      dockerfile: Dockerfile
    environment:
      PREFECT_API_URL: http://prefect-server:4200/api
      INFRAHUB_API_URL: ${INFRAHUB_API_URL}
      INFRAHUB_API_TOKEN: ${INFRAHUB_API_TOKEN}
      F5_DEFAULT_USERNAME: ${F5_DEFAULT_USERNAME}
      F5_DEFAULT_PASSWORD: ${F5_DEFAULT_PASSWORD}
      NETAUTO_ENVIRONMENT: ${ENVIRONMENT:-development}
    networks:
      - netauto
    depends_on:
      - prefect-server
    restart: unless-stopped
    deploy:
      replicas: 1  # Scale as needed

  # Webhook Handler (from your existing repository)
  webhook-handler:
    build:
      context: https://github.com/your-org/webhook-handler.git
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      PREFECT_API_URL: http://prefect-server:4200/api
      PREFECT_API_KEY: ${PREFECT_API_KEY}
      INFRAHUB_API_URL: ${INFRAHUB_API_URL}
      WEBHOOK_SECRET_KEY: ${WEBHOOK_SECRET_KEY}
    networks:
      - netauto
    depends_on:
      - prefect-server
    restart: unless-stopped

  # Infrahub (if running locally)
  infrahub:
    image: opsmill/infrahub:latest
    ports:
      - "8080:8000"
    environment:
      INFRAHUB_DB_TYPE: sqlite
      INFRAHUB_SECURITY_SECRET_KEY: ${INFRAHUB_SECRET_KEY}
    volumes:
      - infrahub_data:/opt/infrahub/data
    networks:
      - netauto
    restart: unless-stopped

  # Optional: Traefik for load balancing
  traefik:
    image: traefik:v3.0
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
      - "8081:8080"  # Traefik dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - netauto
    labels:
      - "traefik.enable=false"
```

#### 5.4 Development Override

```yaml
# docker-compose.dev.yml - Development overrides
version: '3.8'

services:
  netauto-worker:
    # Use local build for development
    build:
      context: ../netauto-orchestrator  # Relative path to local repo
      dockerfile: Dockerfile
    volumes:
      # Mount local code for hot reload during development
      - ../netauto-orchestrator:/opt/prefect/flows:ro
    environment:
      PREFECT_LOGGING_LEVEL: DEBUG
      
  webhook-handler:
    build:
      context: ../webhook-handler      # Relative path to local repo
    volumes:
      - ../webhook-handler:/app:ro     # Mount local code
    environment:
      DEBUG: "true"
      RELOAD: "true"
```

#### 5.5 Usage Commands

```bash
# Development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production environment  
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale workers
docker-compose up --scale netauto-worker=3

# View logs
docker-compose logs -f netauto-worker
```

### 6. Advantages of This Architecture

#### 6.1 Code Management Benefits
- **No Code Rebuilds**: Flow updates don't require Docker image rebuilds
- **Version Control**: Git tags/branches control which code version runs
- **Hot Deployments**: New code available immediately after Git push
- **Rollback Capability**: Easy rollback to previous Git commits

#### 6.2 Operational Benefits
- **Single Worker**: One Docker container handles all flows
- **Resource Efficiency**: Shared dependencies and base image
- **Simplified Monitoring**: One worker to monitor and manage
- **Easy Scaling**: Scale worker replicas without code duplication

#### 6.3 Development Benefits
- **Local Testing**: Same flows run locally and in production
- **Environment Parity**: Consistent execution environment
- **Rapid Iteration**: Code changes immediately available
- **Debugging**: Easy to debug with local Git repository

### 7. Implementation Steps

#### Phase 1: Infrastructure Setup
1. Create base Docker image with all dependencies
2. Set up Docker work pool in Prefect
3. Configure webhook receiver service
4. Set up CI/CD pipeline

#### Phase 2: Flow Migration  
1. Migrate existing F5 flows to new structure
2. Create Git-based deployment configurations
3. Test webhook integration
4. Set up monitoring and logging

#### Phase 3: Production Deployment
1. Deploy worker to production environment
2. Configure Infrahub webhooks to point to receiver
3. Deploy all flows using Git-based deployments
4. Monitor and optimize performance

### 8. Configuration Examples

#### 8.1 Environment Variables
```bash
# Production environment
PREFECT_API_URL=https://prefect.netauto.alef.dc/api
PREFECT_API_KEY=your-prefect-api-key
INFRAHUB_API_URL=https://infrahub.netauto.alef.dc
INFRAHUB_API_TOKEN=your-infrahub-token
NETAUTO_ENVIRONMENT=production
```

#### 8.2 Work Pool Job Variables
```yaml
# Production work pool variables
job_variables:
  image: "your-registry/netauto-base:latest"
  env:
    NETAUTO_ENVIRONMENT: "production"
    INFRAHUB_API_URL: "https://infrahub.netauto.alef.dc"
  cpu_request: "500m"
  cpu_limit: "2000m"
  memory_request: "1Gi"
  memory_limit: "4Gi"
```

## Repository Responsibilities Summary

### 📁 **This Repository (netauto-orchestrator)**
- ✅ **Dockerfile** for Prefect worker (place here)
- ✅ **Flow code** and shared libraries
- ✅ **Deployment configurations** 
- ✅ **Dependencies** (pyproject.toml)
- ✅ **CI/CD** for flow deployments

### 📁 **Your Webhook Handler Repository**
- ✅ **Webhook receiver** FastAPI service
- ✅ **Prefect client integration** (dispatcher code provided above)
- ✅ **Dockerfile** for webhook service
- ✅ **Routing and validation** logic

### 📁 **Infrastructure Repository (Recommended New Repo)**
- ✅ **Docker Compose** for complete solution
- ✅ **Environment configurations** (.env files)
- ✅ **Deployment scripts** and utilities
- ✅ **Kubernetes manifests** (if using K8s)
- ✅ **Monitoring and backup** configurations

## Prefect Native Image Building

Prefect 3.0 provides native Docker image building through:

```python
# In this repository - deployments/production.py
from prefect.docker import DockerImage

# Prefect will build and push the image automatically
my_deployment = flow.from_source(
    source="https://github.com/your-org/netauto-orchestrator.git",
    entrypoint="flows/f5/deploy_as3.py:deploy_f5_as3_application"
).to_deployment(
    name="f5-as3-production",
    work_pool_name="netauto-docker-pool",
    # Prefect builds this image automatically when deploying
    image=DockerImage(
        name="netauto-worker",
        tag="latest",
        dockerfile="Dockerfile"  # From this repo
    )
)
```

## Final Architecture Summary

This approach provides:
- ✅ **Single Docker executor** running all flows
- ✅ **Git-based code synchronization** for easy updates
- ✅ **Separation of concerns** across repositories
- ✅ **Event-driven deployments** via existing webhook handler
- ✅ **Scheduled synchronization** flows
- ✅ **Environment-specific configurations**
- ✅ **Scalable and maintainable structure**
- ✅ **Native Prefect image building**

The approach leverages Prefect 3.0's `from_source` capabilities while maintaining clear repository boundaries and operational simplicity.