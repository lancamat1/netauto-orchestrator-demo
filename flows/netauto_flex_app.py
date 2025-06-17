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
def process_netauto_flex_application(webhook_data: Dict):
    logger = get_run_logger()
    payload = WebhookPayload(**webhook_data)
    logger.info(f"Processing NetautoFlexApplication: {payload.data.target_id}")
    # Your flow logic here
    return {"status": "success", "target_id": payload.data.target_id}

if __name__ == "__main__":
    # Example usage
    example_data = {
    "data": {
        "node_id": "1848f31f-5047-96cc-e08e-c517391206b1",
        "checksum": "2eb53dcae84223f64d3069f6928ce89e",
        "target_id": "1848f2fc-f58a-75e4-e089-c5153d37e211",
        "storage_id": "18498635-9f1c-71c3-e083-c514d2500e91",
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
    flow_run = flow.from_source(
        "https://github.com/lancamat1/netauto-orchestrator-demo.git",
        entrypoint="flows/netauto_flex_app.py:process_netauto_flex_application"
    ).deploy(
        name="Netauto Flex Application Processing",
        parameters={"webhook_data": example_data},
        work_pool_name="my-docker-pool",
        build=False
    )