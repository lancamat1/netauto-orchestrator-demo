# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a network automation orchestrator built with Prefect that processes F5 BIG-IP application deployments. It receives webhook events from Infrahub and orchestrates the deployment of network applications (Flex, L4, mTLS) to F5 load balancers using AS3 (Application Services 3 Extension).

## Key Dependencies

- **Prefect**: Workflow orchestration framework (v3.0+)
- **infrahub-sdk**: Client for Infrahub API integration
- **f5_as3_sdk**: Custom internal library for F5 AS3 API communication (located in `deployments/netauto_f5/f5_as3_sdk/`)
- **FastAPI/uvicorn**: Web framework for webhook endpoints
- **Python 3.12+**: Runtime requirement

## Common Commands

### Development
```bash
# Install dependencies
uv sync

# Run individual flow (development testing)
python flows/netauto_f5/flex.py
python flows/netauto_f5/l4.py
python flows/netauto_f5/mtls.py

# Register Prefect blocks
prefect block register -f flows/netauto_f5/blocks.py
```

### Deployment
```bash
# Build Docker image for F5 orchestrator
prefect deploy --name netauto-flex
prefect deploy --name netauto-l4
prefect deploy --name netauto-mtls

# Deploy all flows defined in prefect.yaml
prefect deploy --all
```

## Architecture

### Core Components

1. **Flow Modules** (`flows/netauto_f5/`):
   - `flex.py`: Processes Flex application deployments (fully implemented)
   - `l4.py`: Processes L4 application deployments (stub implementation)
   - `mtls.py`: Processes mTLS application deployments (stub implementation)
   - `common.py`: Shared utilities, data models, and helper functions
   - `blocks.py`: Prefect block definitions for Infrahub client configuration

2. **F5 AS3 SDK** (`deployments/netauto_f5/f5_as3_sdk/`):
   - Custom library for F5 BIG-IP AS3 API interactions
   - Handles authentication, application deployment, and certificate management
   - `connector.py`: Main AS3Applications class for API communication

3. **Configuration**:
   - `prefect.yaml`: Defines Prefect deployments, work pools, and Docker build configuration
   - `infrahubctl.toml`: Infrahub API configuration
   - `pyproject.toml`: Python project dependencies

### Workflow Pattern

1. Webhook received from Infrahub with application deployment data
2. Validate webhook payload using Pydantic models
3. Initialize Infrahub client to fetch application details and artifacts
4. Create F5 AS3 client connection to target cluster
5. Deploy application configuration to F5 using AS3 API
6. Update deployment status in Infrahub

### Key Data Models

- `WebhookPayload` / `WebhookData`: Infrahub webhook event structure
- `DeploymentStatus`: Enum for tracking application deployment states
- `InfrahubClientBlock`: Prefect block for Infrahub API configuration

## Development Notes

- Mock webhook data is available in `flex.py` for testing
- The `flex.py` flow is the reference implementation for the deployment pattern
- L4 and mTLS flows are currently stubs that need implementation
- F5 credentials are hardcoded in `common.py:57` (admin/1234Qwer) for development
- Infrahub API tokens are stored in configuration files (should be secured in production)