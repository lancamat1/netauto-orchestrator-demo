"""
Webhook handler flow that receives events from Infrahub via the webhook-trigger-service.

This flow serves as the entry point for all webhook events and routes them
to appropriate handlers based on the event type.
"""
import json
from typing import Any

from prefect import flow, get_run_logger


@flow(name="webhook-handler")
async def webhook_handler(webhook_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Main webhook handler that receives all Infrahub events.

    The payload structure from Infrahub typically includes:
    - event: The event type (e.g., "infrahub.node.created")
    - branch: The branch where the event occurred
    - data: Event-specific data
    - id: Event ID
    - account_id: Account that triggered the event
    - occured_at: Timestamp
    """
    logger = get_run_logger()

    logger.info("=" * 60)
    logger.info("RECEIVED WEBHOOK PAYLOAD")
    logger.info("=" * 60)
    logger.info(json.dumps(webhook_payload, indent=2, default=str))
    logger.info("=" * 60)

    event_type = webhook_payload.get("event", "unknown")
    branch = webhook_payload.get("branch", "unknown")
    data = webhook_payload.get("data", {})

    logger.info(f"Event Type: {event_type}")
    logger.info(f"Branch: {branch}")
    logger.info(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")

    # TODO: Route to specific handlers based on event type
    # For now, just log and return success
    return {
        "status": "received",
        "event_type": event_type,
        "branch": branch,
    }


if __name__ == "__main__":
    import asyncio

    # Test with mock payload
    mock_payload = {
        "event": "infrahub.node.created",
        "branch": "main",
        "data": {"kind": "NetautoServiceNowTicket", "node_id": "test-123"},
        "id": "test-event-id",
        "account_id": "test-account",
        "occured_at": "2025-12-11T12:00:00Z",
    }
    asyncio.run(webhook_handler(mock_payload))
