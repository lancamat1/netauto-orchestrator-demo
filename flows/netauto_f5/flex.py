from prefect import flow, get_run_logger
from common import *
from typing import Dict
import asyncio
from blocks import InfrahubClientBlock


@flow()
async def process_flex_application(webhook_data: Dict):
    logger = get_run_logger()
    logger.info("Processing Flex Application webhook data...")

    # Validate the incoming webhook data
    webhook_data = validate_webhook_data(webhook_data)

    # Initialize Infrahub client
    infc_block = await InfrahubClientBlock.load("infrahub-netauto-alef-dc")
    infc = infc_block.get_client()
    logger.info(await infc.get_version())

    # Set the target application status
    set_node_deployment_status(infc, webhook_data.data.target_kind, webhook_data.data.target_id, "running")

    # Fetch target cluster management IP and entity for target application
    application = await infc.get(kind=webhook_data.data.target_kind, id=webhook_data.data.target_id)
    await application.cluster.fetch()
    await application.cluster.peer.primary_address.fetch()
    cluster_ip = str(application.cluster.peer.primary_address.peer.address.value.ip)
    await application.entity.fetch()
    entity = application.entity.peer.name.value

    # Fetch the payload for the Flex Application
    payload = fetch_infrahub_artifact(infc, webhook_data.data.storage_id)

    # Initialize AS3 client
    f5c = get_as3_client(cluster_ip)

    # Post the application to F5 AS3
    f5c.post_app(entity, payload)


@process_flex_application.on_failure
async def process_flex_application_failed(flow, flow_run, state):
    logger = get_run_logger()
    logger.info(f"Flow {flow.name} failed with state: {state}")
    logger.info(f"Flow run parameters: {flow_run.parameters}")
    block = await InfrahubClientBlock.load("infrahub-netauto-alef-dc")
    client = block.get_client()
    webhook_data = validate_webhook_data(flow_run.parameters.get("webhook_data", {}))
    set_node_deployment_status(client, webhook_data.data.target_kind, webhook_data.data.target_id, DeploymentStatus.failed)
    
if __name__ == "__main__":

    mock_webhook_data = {
    "data": {
        "node_id": "1848f31f-5047-96cc-e08e-c517391206b1",
        "checksum": "2eb53dcae84223f64d3069f6928ce89e",
        "target_id": "1849e6ed-5dfa-4dc6-ef50-c512c7386160",
        "storage_id": "1849e709-0b06-d7a1-ef5d-c5116547caa7",
        "target_kind": "NetautoFlexApplication",
        "checksum_previous": "1083e399061bbe4fddc3478492c87225",
        "storage_id_previous": "18498531-6594-cd12-e08a-c5146b746b62",
        "artifact_definition_id": "1848f2c5-9701-8d43-e081-c51332fa2bc8"
    },
    "id": "0b550602-4a3c-446b-ad11-9c3d7575c497",
    "branch": "main",
    "account_id": "1848f278-8904-6350-e08f-c516602d870a",
    "occured_at": "2025-06-16 12:38:15.177969+00:00",
    "event": "infrahub.artifact.updated"
    }
    asyncio.run(process_flex_application(mock_webhook_data))
