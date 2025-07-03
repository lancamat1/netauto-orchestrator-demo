from pydantic import BaseModel
from prefect import task, get_run_logger
from infrahub_sdk import InfrahubClient
from enum import Enum
from f5_as3_sdk.connector import AS3Applications
from blocks import InfrahubClientBlock
from flex import process_flex_application
from l4 import process_l4_application
from mtls import process_mtls_application
import os, json

class DeploymentStatus(str, Enum):
    failed = "failed"
    crashed = "crashed"
    deployed = "deployed"
    running = "running"
    pending = "pending"
    unknown = "unknown"

class WebhookData(BaseModel):
    node_id: str
    checksum: str
    target_id: str
    storage_id: str
    target_kind: str
    checksum_previous: str
    storage_id_previous: str
    artifact_definition_id: str

class WebhookPayload(BaseModel):
    data: WebhookData
    id: str
    branch: str
    account_id: str
    occured_at: str
    event: str

@process_flex_application.on_failure
@process_l4_application.on_failure
@process_mtls_application.on_failure
async def node_deployment_status_failed(flow, flow_run, state):
    logger = get_run_logger()
    logger.error(f"Flow {flow.name} failed with state: {state}")
    logger.error(f"Flow run parameters: {flow_run.parameters}")
    block = await InfrahubClientBlock.load("infrahub-netauto-alef-dc")
    client = block.get_client()
    webhook_data = flow_run.parameters.get("webhook_data", {})
    node_kind = webhook_data.get("data", {}).get("target_kind")
    node_id = webhook_data.get("data", {}).get("target_id")
    set_node_deployment_status(client, node_kind, node_id, DeploymentStatus.failed)

@task()
def validate_webhook_data(webhook_data: dict) -> WebhookPayload:
    """
    Validates the incoming webhook data against the WebhookPayload model.
    Raises a ValueError if validation fails.
    """
    logger = get_run_logger()
    logger.info("Validating webhook data...")
    logger.info(f"Webhook data: {webhook_data}")
    try:
        return WebhookPayload(**webhook_data)
    except Exception as e:
        raise ValueError(f"Invalid webhook data: {e}") from e

def get_as3_client(address: str = None, username: str = None, password: str = None) -> AS3Applications:
    """
    Returns an AS3 client instance.
    This function should be implemented to return a valid AS3 client.
    """
    logger = get_run_logger()
    logger.info("Creating AS3 client...")
    client = AS3Applications(address, 
                             username if username else "admin", 
                             password if password else "1234Qwer")
    logger.info(client.__get(uri="/mgmt/shared/appsvcs/info"))
    return client

# @task(retries=3)
# def get_infrahub_client(address: str = None) -> InfrahubClient:
#     """
#     Returns an Infrahub client instance.
#     This function should be implemented to return a valid Infrahub client.
#     """
#     logger = get_run_logger()
#     logger.info("Creating Infrahub client...")
#     client = InfrahubClient(address = address if address else os.getenv("INFRAHUB_API_URL"))
#     logger.info(client.get_version())
#     return client

@task()
def fetch_infrahub_artifact(infrahub_client: InfrahubClient, storage_id: str) -> dict:
    """
    Fetches an artifact from Infrahub using the provided storage ID.
    Returns the artifact as a dictionary.
    """
    logger = get_run_logger()
    logger.info(f"Fetching artifact with storage_id: {storage_id}")
    payload_str = infrahub_client.object_store.get(identifier=storage_id)
    if not payload_str:
        raise ValueError(f"No payload found for storage_id {storage_id}")
    
    try:
        return json.loads(payload_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing payload for storage_id {storage_id}: {e}") from e

@task()
async def set_node_deployment_status(infrahub_client: InfrahubClient, target_kind: str, target_id: str, status: DeploymentStatus):
    """
    Sets the status of the target application in Infrahub.
    This function should be implemented to update the application status.
    """
    # status choices are failed crashed deployed running pending unknown
    logger = get_run_logger()
    node = await infrahub_client.get(kind=target_kind, id=target_id)
    node.deployment_status.value = status
    await node.save(allow_upsert=True)
    logger.info(f"Status for target node {target_id} set to {status}")

