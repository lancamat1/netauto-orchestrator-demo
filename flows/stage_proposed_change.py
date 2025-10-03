from prefect import flow, get_run_logger
from tasks.common import *
from typing import Dict
import asyncio
from blocks.blocks import InfrahubClientBlock


@flow()
async def stage_proposed_change(webhook_data: Dict):
    logger = get_run_logger()
    logger.info("Staging proposed change from webhook data...")

    # Validate the incoming webhook data
    webhook_data = validate_webhook_data(webhook_data)

    # Initialize Infrahub client
    infc_block = await InfrahubClientBlock.load("infrahub-netauto-alef-dc")
    infc = infc_block.get_client()
    logger.info(await infc.get_version())

    # TODO: Implement proposed change staging logic based on event type
    # This could handle different event types such as:
    # - infrahub.node.created
    # - infrahub.node.updated
    # - infrahub.node.deleted
    # - infrahub.branch.created
    # - infrahub.branch.merged
    # etc.
    
    event_type = webhook_data.event
    target_kind = webhook_data.data.target_kind
    target_id = webhook_data.data.target_id
    
    logger.info(f"Processing event: {event_type} for {target_kind}:{target_id}")
    
    # Example staging logic - customize based on your needs
    if "node" in event_type:
        await _handle_node_event(infc, webhook_data)
    elif "branch" in event_type:
        await _handle_branch_event(infc, webhook_data)
    else:
        logger.info(f"Event type {event_type} not handled by staging flow")

    logger.info("Proposed change staged successfully")


async def _handle_node_event(infc, webhook_data):
    logger = get_run_logger()
    logger.info("Handling node event...")
    # TODO: Implement node-specific staging logic


async def _handle_branch_event(infc, webhook_data):
    logger = get_run_logger()
    logger.info("Handling branch event...")
    # TODO: Implement branch-specific staging logic


@stage_proposed_change.on_failure
async def stage_proposed_change_failed(flow, flow_run, state):
    logger = get_run_logger()
    logger.error(f"Proposed change staging failed with state: {state}")
    logger.info(f"Flow run parameters: {flow_run.parameters}")
    # TODO: Add rollback or notification logic here


if __name__ == "__main__":
    mock_webhook_data = {
        "data": {
            "node_id": "1848f31f-5047-96cc-e08e-c517391206b1",
            "checksum": "2eb53dcae84223f64d3069f6928ce89e",
            "target_id": "1849e6ed-5dfa-4dc6-ef50-c512c7386160",
            "storage_id": "1849e709-0b06-d7a1-ef5d-c5116547caa7",
            "target_kind": "NetautoConfiguration",
            "checksum_previous": "1083e399061bbe4fddc3478492c87225",
            "storage_id_previous": "18498531-6594-cd12-e08a-c5146b746b62",
            "artifact_definition_id": "1848f2c5-9701-8d43-e081-c51332fa2bc8"
        },
        "id": "0b550602-4a3c-446b-ad11-9c3d7575c497",
        "branch": "staging",
        "account_id": "1848f278-8904-6350-e08f-c516602d870a",
        "occured_at": "2025-06-16 12:38:15.177969+00:00",
        "event": "infrahub.node.updated"
    }
    asyncio.run(stage_proposed_change(mock_webhook_data))