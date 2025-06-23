from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from prefect.deployments import run_deployment

app = FastAPI()

FLOW_MAPPING = {
    "NetautoFlexApplication": "process-flex-application/netauto-flex",
    "NetautoL4Application": "process-l4-application/netauto-l4",
    "NetautoMTLSApplication": "process-mtls-application/netauto-mtls",
}

class WebhookPayload(BaseModel):
    data: dict
    id: str
    branch: str
    account_id: str
    occured_at: str
    event: str

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        payload = await request.json()
        webhook_data = WebhookPayload(**payload)
        
        if webhook_data.event not in ["infrahub.artifact.created", "infrahub.artifact.updated"]:
            raise HTTPException(status_code=400, detail="Unsupported event type")
        
        target_kind = webhook_data.data.get("target_kind")
        if not target_kind:
            raise HTTPException(status_code=400, detail="Missing target_kind in payload")
        
        deployment_name = FLOW_MAPPING.get(target_kind)
        if not deployment_name:
            raise HTTPException(status_code=400, detail=f"Unsupported target_kind: {target_kind}")
        
        flow_run = await run_deployment(
            name=deployment_name,
            parameters={"webhook_data": webhook_data.model_dump()}
        )
        return {"status": "flow_triggered", "flow_run_id": str(flow_run.id)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
