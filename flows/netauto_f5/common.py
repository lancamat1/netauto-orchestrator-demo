from pydantic import BaseModel
from prefect import task, get_run_logger

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