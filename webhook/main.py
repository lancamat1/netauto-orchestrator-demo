from fastapi import FastAPI, Request
from prefect.client import get_client

app = FastAPI()

@app.post("/webhook")
async def trigger_flow(request: Request):
    payload = await request.json()
    target_kind = payload["data"]["target_kind"]

    deployment_name = {
        "NetautoFlexApplication": "application-deploy"
    }.get(target_kind)

    if deployment_name:
        async with get_client() as client:
            await client.create_flow_run_from_deployment(
                name=deployment_name,
                parameters={"payload": payload}
            )
        return {"status": "triggered", "deployment": deployment_name}
    return {"status": "ignored", "reason": "unknown target_kind"}
