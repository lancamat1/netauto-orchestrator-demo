from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from prefect import get_client, flow

app = FastAPI()

FLOW_MAPPING = {
    "NetautoFlexApplication": "process_netauto_flex_application",
    # Add more mappings as needed
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
        
        flow_func = FLOW_MAPPING.get(target_kind)
        if not flow_func:
            raise HTTPException(status_code=400, detail=f"Unsupported target_kind: {target_kind}")
        
        flow_run = flow.from_source(
            "https://github.com/lancamat1/netauto-orchestrator-demo.git",
            entrypoint="flows/netauto_flex_app.py:process_netauto_flex_application"
        ).deploy(
            name="Netauto Flex Application Processing",
            parameters={"webhook_data": webhook_data.model_dump()},
            work_pool_name="my-docker-pool",
            build=False
        )
    
        return {"status": "flow_triggered", "flow_run_id": str(flow_run.id)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}