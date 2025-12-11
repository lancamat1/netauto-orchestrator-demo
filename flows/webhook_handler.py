"""
Webhook handler flow that receives events from Infrahub via the webhook-trigger-service.

This flow serves as the entry point for all webhook events and routes them
to appropriate handlers based on the event type.
"""
import json
from typing import Any

from pydantic import ValidationError
from prefect import flow, get_run_logger

from flows.models import WebhookPayload
from flows.handle_ticket_created import handle_ticket_created


@flow(name="webhook-handler")
async def webhook_handler(webhook_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Main webhook handler that receives all Infrahub events.

    Validates the payload using Pydantic models and routes to appropriate handlers.
    """
    logger = get_run_logger()

    logger.info("=" * 60)
    logger.info("RECEIVED WEBHOOK PAYLOAD")
    logger.info("=" * 60)
    logger.info(json.dumps(webhook_payload, indent=2, default=str))
    logger.info("=" * 60)

    # Parse and validate payload
    try:
        payload = WebhookPayload.model_validate(webhook_payload)
    except ValidationError as e:
        logger.error(f"Invalid webhook payload: {e}")
        return {"status": "error", "message": "Invalid payload", "errors": e.errors()}

    logger.info(
        f"Event: {payload.event} | Kind: {payload.data.kind} | "
        f"Action: {payload.data.action} | Branch: {payload.branch}"
    )

    # Route to specific handlers based on event type and kind
    if payload.is_ticket_created():
        logger.info(f"Routing to handle_ticket_created: {payload.ritm}")
        result = await handle_ticket_created(payload)
        return result

    # TODO: Add more event handlers here
    # elif payload.event == "infrahub.artifact.created":
    #     ...

    logger.info(f"No handler for event: {payload.event} kind: {payload.data.kind}")
    return {
        "status": "received",
        "event": payload.event,
        "kind": payload.data.kind,
        "branch": payload.branch,
        "handled": False,
    }


if __name__ == "__main__":
    import asyncio

    # Test with ticket created payload
    mock_payload = {
        "id": "27e24228-9dba-458a-a468-04827be43678",
        "data": {
            "kind": "NetautoServiceNowTicket",
            "action": "created",
            "node_id": "188038c6-1248-81d3-e385-c51a12f89fdd",
            "changelog": {
                "node_id": "188038c6-1248-81d3-e385-c51a12f89fdd",
                "node_kind": "NetautoServiceNowTicket",
                "display_label": "RITM0000045",
                "attributes": {
                    "ritm": {
                        "kind": "Text",
                        "name": "ritm",
                        "value": "RITM0000045",
                        "value_previous": None,
                        "value_update_status": "added",
                    },
                    "cat_item": {
                        "kind": "Dropdown",
                        "name": "cat_item",
                        "value": "segment",
                        "value_previous": None,
                        "value_update_status": "added",
                    },
                    "short_description": {
                        "kind": "Text",
                        "name": "short_description",
                        "value": "Segment Service Request (NEW) - test",
                        "value_previous": None,
                        "value_update_status": "added",
                    },
                },
                "relationships": {},
            },
        },
        "event": "infrahub.node.created",
        "branch": "main",
        "account_id": "test-account",
        "occured_at": "2025-12-11T12:00:00Z",
    }
    asyncio.run(webhook_handler(mock_payload))
