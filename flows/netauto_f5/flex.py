from prefect import flow
from common import validate_webhook_data, WebhookPayload
from typing import Dict
from f5_as3_sdk.connector import AS3Applications
from infrahub_sdk import InfrahubClient
import asyncio
import os
import json

@flow(log_prints=True)
async def process_flex_application(webhook_data: Dict):
    print("Processing Netauto Flex Application...")
    webhook_data = validate_webhook_data(webhook_data)

    infc = InfrahubClient(address=os.getenv("INFRAHUB_API_URL", "http://infrahub.netauto.alef.dc"))

    # Fetch target cluster management IP from infrahub
    application = await infc.get(kind=webhook_data.data.target_kind, id=webhook_data.data.target_id)
    await application.cluster.fetch()
    await application.cluster.peer.primary_address.fetch()
    cluster_ip = str(application.cluster.peer.primary_address.peer.address.value.ip)
    await application.entity.fetch()
    entity = application.entity.peer.name.value
    print(f"Cluster IP: {cluster_ip}, Entity: {entity}")
    # Fetch artifact from infrahub
    payload_str = await infc.object_store.get(identifier=webhook_data.data.storage_id)
    if not payload_str:
        print(f"No payload found for storage_id {webhook_data.data.storage_id}")
    try:
        payload = json.loads(payload_str)
    except Exception as e:
        print(f"Error parsing payload for storage_id {webhook_data.data.storage_id}: {e}")

    f5c = AS3Applications(cluster_ip, "admin", "1234Qwer")
    f5c.post_app(entity, payload)

    
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
