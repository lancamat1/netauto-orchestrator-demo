import os

from infrahub_sdk import Config, InfrahubClient


def get_infrahub_client() -> InfrahubClient:
    return InfrahubClient(
        address=os.environ["INFRAHUB_API_URL"],
        config=Config(api_token=os.environ["INFRAHUB_API_TOKEN"]),
    )
