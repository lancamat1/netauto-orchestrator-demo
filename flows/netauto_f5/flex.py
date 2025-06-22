from prefect import flow
from common import validate_webhook_data
from typing import Dict
# from f5_as3_sdk.connector import AS3Applications
from infrahub_sdk import InfrahubClient

@flow(log_prints=True)
def process_flex_application(webhook_data: Dict):
    print("Processing Netauto Flex Application...")
    webhook_data = validate_webhook_data(webhook_data)

    # Fetch target cluster management IP from infrahub
    infc = InfrahubClient()
    print(infc.get_version())

    # f5 = AS3Applications(
    #     ""
    # )
    

# {
#   "data": {
#     "node_id": "1848f31f-5047-96cc-e08e-c517391206b1",
#     "checksum": "2eb53dcae84223f64d3069f6928ce89e",
#     "target_id": "1848f2fc-f58a-75e4-e089-c5153d37e211",
#     "storage_id": "18498635-9f1c-71c3-e083-c514d2500e91",
#     "target_kind": "NetautoFlexApplication",
#     "checksum_previous": "1083e399061bbe4fddc3478492c87225",
#     "storage_id_previous": "18498531-6594-cd12-e08a-c5146b746b62",
#     "artifact_definition_id": "1848f2c5-9701-8d43-e081-c51332fa2bc8"
#   },
#   "id": "0b550602-4a3c-446b-ad11-9c3d7575c497",
#   "branch": "main",
#   "account_id": "1848f278-8904-6350-e08f-c516602d870a",
#   "occured_at": "2025-06-16 12:38:15.177969+00:00",
#   "event": "infrahub.artifact.updated"
# }