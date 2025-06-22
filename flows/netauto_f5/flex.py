from prefect import flow
from common import validate_webhook_data
from typing import Dict

@flow(log_prints=True)
def process_flex_application(webhook_data: Dict):
    print("Processing Netauto Flex Application...")
    webhook_data = validate_webhook_data(webhook_data)
    