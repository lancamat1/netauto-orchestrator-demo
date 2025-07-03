from prefect.blocks.core import Block
from pydantic import SecretStr
from infrahub_sdk import InfrahubClient, Config
import os

# This block defines a Prefect block for InfraHubClient configuration.
class InfrahubClientBlock(Block):
    """
    Block storing configuration for InfraHubClient.
    """
    api_url: str
    api_key: SecretStr

    _block_type_name = "InfraHub Client"

    def get_client(self) -> InfrahubClient:
        return InfrahubClient(
            address=os.getenv("PREFECT_API_URL", self.api_url),
            config=Config(api_token=os.getenv("PREFECT_API_TOKEN", self.api_key.get_secret_value()))
        )

InfrahubClientBlock.register_type_and_schema()


# Run this: prefect block register -f flows/netauto_f5/blocks.py