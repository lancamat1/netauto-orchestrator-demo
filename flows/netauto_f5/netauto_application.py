from prefect import flow, get_run_logger
from pydantic import BaseModel
from typing import Dict

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

@flow
def process_netauto_application(webhook_data: Dict):
    logger = get_run_logger()
    payload = WebhookPayload(**webhook_data)
    logger.info(f"Processing NetautoFlexApplication: {payload.data.target_id}")
    # Your flow logic here
    return {"status": "success", "target_id": payload.data.target_id}

if __name__ == "__main__":
    # Create a deployment for the flow

    flow_run = flow.from_source(
        "https://github.com/lancamat1/netauto-orchestrator-demo.git",
        entrypoint="flows/netauto_flex_app.py:process_netauto_flex_application"
    ).deploy(
        name="Netauto Flex Application Processing",
        work_pool_name="k8s-alef-dc",
        build=False
    )