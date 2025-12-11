"""
Flow to handle NetautoServiceNowTicket created events.

This flow is triggered when a new ticket is created in Infrahub (synced from ServiceNow).
Based on the ticket category (cat_item), it creates a branch and implements the request.
"""
import asyncio
from typing import Any

from prefect import flow, task, get_run_logger
from prefect.cache_policies import NONE

from blocks.blocks import InfrahubClientBlock
from flows.models import WebhookPayload

from infrahub_sdk.protocols import CoreProposedChange


@task
async def get_infrahub_client():
    """Load Infrahub client from Prefect block."""
    logger = get_run_logger()
    block = await InfrahubClientBlock.load("infrahub-netauto-alef-dc")
    client = block.get_client()
    version = await client.get_version()
    logger.info(f"Connected to Infrahub: {version}")
    return client

@task
async def get_snow_client():
    """Load ServiceNow client from Prefect block."""
    # TODO: Implement ServiceNow client block and loading
    pass

@task(cache_policy=NONE)
async def create_ticket_branch(client, ticket_id: str, ritm: str) -> str:
    """Create a new branch for implementing the ticket."""
    logger = get_run_logger()
    branch_name = f"ticket/{ritm}"
    logger.info(f"Creating branch: {branch_name}")

    # Create branch in Infrahub if it does not exist
    existing_branch = await client.branch.get(branch_name=branch_name)
    if existing_branch:
        logger.info(f"Branch already exists: {existing_branch.name}")
        return existing_branch.name

    branch = await client.branch.create(
        branch_name=branch_name,
        description=f"Implementation branch for ticket {ritm}",
        sync_with_git=False,
    )
    logger.info(f"Branch created: {branch.name}")
    return branch.name


@task(cache_policy=NONE)
async def fetch_ticket_details(client, ritm: str) -> dict[str, Any]:
    """Fetch full ticket details from SNOW."""
    # Placeholder implementation - replace with actual SNOW API calls
    # Return static segment data for now
    ticket_details = {
        "entity": await client.get(kind="OrganizationEntity", name__value="Bank"),
        "pillar": await client.get(kind="NetautoPillar", name__value="Prod"),
        "firewall_device": await client.get(kind="InfraDevice", name__value="cz-fw-1"),
        "country": await client.get(kind="LocationCountry", shortname__value="CZ"),
        "network_category": "production",
        "filtering_profile": "X",
        "network_zone": "perimeter",
        "purpose": "Business critical application",
        "ritm": ritm,
    }

    return ticket_details


@task(cache_policy=NONE)
async def implement_segment_service(client, ticket_details: dict[str, Any], branch: str, ritm: str):
    """
    Implement a segment service request on the given branch.
    """
    logger = get_run_logger()
    logger.info(f"Implementing segment service for ticket {ritm} on branch {branch}")

    service = await client.create(
        kind="NetautoSegmentService",
        data=ticket_details,
        branch=branch,
    )
    await service.save(allow_upsert=True)

    logger.info(f"Creating proposed change for segment service ticket {ritm}")
    proposed_change_dict: dict = {
        "name": f"Segment service for ticket {ritm}",
        "source_branch": branch,
        "destination_branch": "main",
    }
    proposed_change = await client.create(
        kind=CoreProposedChange,
        data=proposed_change_dict,
        branch=branch,
    )
    await proposed_change.save(allow_upsert=True)

    logger.info(f"Segment service for ticket {ritm} created successfully on branch {branch}")


@task(cache_policy=NONE)
async def implement_application_service(client, ticket: dict[str, Any], branch: str):
    """
    Implement an application (F5) service request on the given branch.

    TODO: Implementation steps:
    1. Parse ticket short_description to extract application details
    2. Determine application type (Flex, L4, mTLS) from ticket details
    3. Create appropriate NetautoApplication object on the branch
    4. Configure virtual server, pool, monitors, etc.
    5. Create proposed change from branch to main
    """
    logger = get_run_logger()
    logger.info(f"Implementing application service for ticket {ticket['ritm']} on branch {branch}")

    # TODO: Parse application details from ticket
    # app_name = parse_app_name(ticket['short_description'])
    # app_type = determine_app_type(ticket)

    # TODO: Create application object based on type
    # if app_type == "flex":
    #     app = await client.create(kind="NetautoFlexApplication", ...)
    # elif app_type == "l4":
    #     app = await client.create(kind="NetautoL4Application", ...)
    # elif app_type == "mtls":
    #     app = await client.create(kind="NetautoMtlsApplication", ...)

    # TODO: Create proposed change
    # proposed_change = await client.create(...)

    logger.info(f"Application service implementation placeholder complete for {ticket['ritm']}")


@flow(name="handle-ticket-created")
async def handle_ticket_created(payload: WebhookPayload) -> dict[str, Any]:
    """
    Main flow to handle ticket created events.

    Routes to appropriate implementation based on cat_item:
    - segment: Create segment service with VLAN/Prefix allocation
    - application: Create F5 application configuration
    """
    logger = get_run_logger()

    ritm = payload.ritm or "unknown"
    cat_item = payload.cat_item or "unknown"
    short_desc = payload.short_description or ""
    node_id = payload.data.node_id

    logger.info(f"Processing ticket created event: {ritm}")
    logger.info(f"Category: {cat_item}")
    logger.info(f"Description: {short_desc}")

    # Connect to Infrahub
    client = await get_infrahub_client()

    # Create branch for this ticket
    branch = await create_ticket_branch(client, node_id, ritm)

    # Fetch full ticket details
    ticket_details = await fetch_ticket_details(client, ritm)

    # Route to appropriate implementation based on category
    if cat_item == "segment":
        await implement_segment_service(client, ticket_details, branch, ritm)
    elif cat_item == "application":
        await implement_application_service(client, ticket_details, branch)
    else:
        logger.warning(f"Unknown cat_item: {cat_item}, skipping implementation")

    return {
        "status": "processed",
        "ritm": ritm,
        "cat_item": cat_item,
        "branch": branch,
    }


if __name__ == "__main__":
    from flows.models import WebhookPayload

    # Test with sample payload
    sample_payload_dict = {
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
    payload = WebhookPayload.model_validate(sample_payload_dict)
    asyncio.run(handle_ticket_created(payload))
