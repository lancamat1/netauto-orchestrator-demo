from prefect import flow
import requests

@flow(log_prints=True)
def process_flex_application():
    print("Processing Netauto Flex Application...")