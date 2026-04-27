from prefect import flow, get_run_logger
from typing import Dict
import asyncio
import json
import os
import sys
import urllib3
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks.common import validate_webhook_data, fetch_infrahub_artifact, set_node_deployment_status, DeploymentStatus
from blocks.blocks import get_infrahub_client

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _f5_login(cluster_ip: str, username: str, password: str, timeout: int = 30) -> str:
    r = requests.post(
        f"https://{cluster_ip}/mgmt/shared/authn/login",
        json={"username": username, "password": password, "loginProviderName": "tmos"},
        auth=(username, password),
        verify=False,
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()["token"]["token"]


def _ensure_per_app(cluster_ip: str, headers: dict, timeout: int = 30) -> None:
    settings_url = f"https://{cluster_ip}/mgmt/shared/appsvcs/settings"
    r = requests.get(settings_url, headers=headers, verify=False, timeout=timeout)
    r.raise_for_status()
    if not r.json().get("perAppDeploymentAllowed"):
        r = requests.post(
            settings_url,
            headers=headers,
            json={"perAppDeploymentAllowed": True},
            verify=False,
            timeout=timeout,
        )
        r.raise_for_status()


def _post_app(cluster_ip: str, headers: dict, tenant: str, payload: dict, timeout: int = 120) -> dict:
    r = requests.post(
        f"https://{cluster_ip}/mgmt/shared/appsvcs/declare/{tenant}/applications",
        headers=headers,
        json=payload,
        verify=False,
        timeout=timeout,
    )
    if not r.ok:
        try:
            detail = r.json()
        except ValueError:
            detail = r.text
        raise RuntimeError(f"AS3 deploy failed ({r.status_code}): {detail}")
    try:
        return r.json()
    except ValueError:
        return {}


def deploy_as3(cluster_ip: str, tenant: str, payload: dict) -> dict:
    username = os.getenv("F5_USERNAME")
    password = os.getenv("F5_PASSWORD")
    token = _f5_login(cluster_ip, username, password)
    headers = {"Content-Type": "application/json", "X-F5-Auth-Token": token}
    _ensure_per_app(cluster_ip, headers)
    return _post_app(cluster_ip, headers, tenant, payload)


@flow()
async def deploy_as3_application(webhook_data: Dict):
    logger = get_run_logger()
    logger.info("Processing AS3 Application webhook data...")

    # Validate the incoming webhook data
    webhook_data = validate_webhook_data(webhook_data)

    infc = get_infrahub_client()
    logger.info(await infc.get_version())

    set_node_deployment_status(infc, webhook_data.data.target_kind, webhook_data.data.target_id, DeploymentStatus.running)

    # Fetch target cluster management IP and entity for target application
    application = await infc.get(kind=webhook_data.data.target_kind, id=webhook_data.data.target_id)
    await application.f5_cluster.fetch()
    await application.f5_cluster.peer.primary_address.fetch()
    cluster_ip = str(application.f5_cluster.peer.primary_address.peer.address.value.ip)
    await application.entity.fetch()
    entity = application.entity.peer.name.value

    # Fetch the payload for the Application
    payload = await fetch_infrahub_artifact(infc, webhook_data.data.storage_id)

    payload = json.loads(json.dumps(payload).replace("XXXXXX", webhook_data.data.checksum[:6]))

    logger.info(f"Deploying AS3 application to cluster at {cluster_ip} (tenant={entity})")
    result = await asyncio.to_thread(deploy_as3, cluster_ip, entity, payload)
    logger.info(f"AS3 deploy response: {result}")

    set_node_deployment_status(infc, webhook_data.data.target_kind, webhook_data.data.target_id, DeploymentStatus.deployed)


@deploy_as3_application.on_failure
async def deploy_as3_application_failed(flow, flow_run, state):
    logger = get_run_logger()
    logger.info(f"Flow {flow.name} failed with state: {state}")
    logger.info(f"Flow run parameters: {flow_run.parameters}")
    client = get_infrahub_client()
    webhook_data = validate_webhook_data(flow_run.parameters.get("webhook_data", {}))
    set_node_deployment_status(client, webhook_data.data.target_kind, webhook_data.data.target_id, DeploymentStatus.failed)


if __name__ == "__main__":
    mock_webhook_data = {
        "data": {
            "node_id": "18aa2b96-6f26-e112-efe2-c511c8788b17",
            "checksum": "2dcdf5fcf61739fc947986bf08a47496",
            "target_id": "189f7448-6ae6-b797-efe0-c51a44bc4ca9",
            "storage_id": "18aa2b96-d501-fb69-efe1-c51527734c1c",
            "target_kind": "NetautoFlexApplication",
            "checksum_previous": "2dcdf5fcf61739fc947986bf08a47496",
            "storage_id_previous": "18aa2b96-d501-fb69-efe1-c51527734c1c",
            "artifact_definition_id": "188023e7-302d-7ff3-e387-c51754f3090c"
        },
        "id": "0b550602-4a3c-446b-ad11-9c3d7575c497",
        "branch": "main",
        "account_id": "1848f278-8904-6350-e08f-c516602d870a",
        "occured_at": "2025-06-16 12:38:15.177969+00:00",
        "event": "infrahub.artifact.updated"
    }
    asyncio.run(deploy_as3_application(mock_webhook_data))