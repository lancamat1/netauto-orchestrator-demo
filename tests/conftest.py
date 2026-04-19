"""Pytest fixtures for flow tests."""
import pytest


@pytest.fixture
def ticket_created_payload() -> dict:
    """Sample payload for NetautoServiceNowTicket created event."""
    return {
        "id": "27e24228-9dba-458a-a468-04827be43678",
        "data": {
            "kind": "NetautoServiceNowTicket",
            "action": "created",
            "node_id": "188038c6-1248-81d3-e385-c51a12f89fdd",
            "fields": [
                "entity",
                "human_friendly_id",
                "display_label",
                "short_description",
                "sys_id",
                "link",
                "ritm",
                "status",
                "cat_item",
            ],
            "changelog": {
                "node_id": "188038c6-1248-81d3-e385-c51a12f89fdd",
                "node_kind": "NetautoServiceNowTicket",
                "display_label": "RITM0000045",
                "attributes": {
                    "link": {
                        "kind": "URL",
                        "name": "link",
                        "value": "https://example.service-now.com/sc_task.do?sys_id=abc123",
                        "value_previous": None,
                        "value_update_status": "added",
                        "properties": {},
                    },
                    "ritm": {
                        "kind": "Text",
                        "name": "ritm",
                        "value": "RITM0000045",
                        "value_previous": None,
                        "value_update_status": "added",
                        "properties": {},
                    },
                    "status": {
                        "kind": "Dropdown",
                        "name": "status",
                        "value": "new",
                        "value_previous": None,
                        "value_update_status": "added",
                        "properties": {},
                    },
                    "sys_id": {
                        "kind": "Text",
                        "name": "sys_id",
                        "value": "3a1c2b89c39746108f9637da05013201",
                        "value_previous": None,
                        "value_update_status": "added",
                        "properties": {},
                    },
                    "cat_item": {
                        "kind": "Dropdown",
                        "name": "cat_item",
                        "value": "segment",
                        "value_previous": None,
                        "value_update_status": "added",
                        "properties": {},
                    },
                    "display_label": {
                        "kind": "Text",
                        "name": "display_label",
                        "value": "RITM0000045",
                        "value_previous": None,
                        "value_update_status": "added",
                        "properties": {},
                    },
                    "short_description": {
                        "kind": "Text",
                        "name": "short_description",
                        "value": "Segment Service Request (NEW) - test-segment",
                        "value_previous": None,
                        "value_update_status": "added",
                        "properties": {},
                    },
                },
                "relationships": {
                    "entity": {
                        "name": "entity",
                        "peer_id": "188023d7-2863-82d3-e382-c510c64aa04a",
                        "peer_kind": "OrganizationEntity",
                        "peer_id_previous": None,
                        "peer_kind_previous": None,
                        "peer_status": "added",
                        "cardinality": "one",
                        "properties": {},
                    }
                },
            },
        },
        "event": "infrahub.node.created",
        "branch": "main",
        "account_id": "187fa738-41b5-6286-e388-c5193123a338",
        "occured_at": "2025-12-11T17:17:57.353436+00:00",
    }


@pytest.fixture
def ticket_created_application_payload(ticket_created_payload: dict) -> dict:
    """Sample payload for application ticket created event."""
    payload = ticket_created_payload.copy()
    payload["data"] = ticket_created_payload["data"].copy()
    payload["data"]["changelog"] = ticket_created_payload["data"]["changelog"].copy()
    payload["data"]["changelog"]["attributes"] = ticket_created_payload["data"]["changelog"][
        "attributes"
    ].copy()
    payload["data"]["changelog"]["attributes"]["cat_item"] = {
        "kind": "Dropdown",
        "name": "cat_item",
        "value": "application",
        "value_previous": None,
        "value_update_status": "added",
        "properties": {},
    }
    payload["data"]["changelog"]["attributes"]["short_description"] = {
        "kind": "Text",
        "name": "short_description",
        "value": "Loadbalancing Service Request (NEW) - myapp.example.com",
        "value_previous": None,
        "value_update_status": "added",
        "properties": {},
    }
    return payload


@pytest.fixture
def generic_webhook_payload() -> dict:
    """Sample generic webhook payload (not a ticket)."""
    return {
        "id": "test-event-id",
        "data": {
            "kind": "SomeOtherKind",
            "action": "updated",
            "node_id": "test-node-id",
            "changelog": {
                "node_id": "test-node-id",
                "node_kind": "SomeOtherKind",
                "display_label": "Test",
                "attributes": {},
                "relationships": {},
            },
        },
        "event": "infrahub.node.updated",
        "branch": "main",
        "account_id": "test-account",
        "occured_at": "2025-12-11T12:00:00Z",
    }
