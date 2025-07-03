from pydantic import BaseModel
from prefect import task, get_run_logger
from infrahub_sdk import InfrahubClient
from f5_as3_sdk.connector import AS3Applications
import os, json

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

@task(retries=3)
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

@task(retries=3)
def get_infrahub_client(address: str = None) -> InfrahubClient:
    """
    Returns an Infrahub client instance.
    This function should be implemented to return a valid Infrahub client.
    """
    logger = get_run_logger()
    logger.info("Creating Infrahub client...")
    client = InfrahubClient(address = address if address else os.getenv("INFRAHUB_API_URL"))
    logger.info(client.get_version())
    return client

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