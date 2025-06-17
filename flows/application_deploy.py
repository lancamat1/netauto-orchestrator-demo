from prefect import flow, task

@task
def process_artifact(data: dict):
    print("Processing artifact:")
    print(data)

@flow
def application_deploy(artifact: dict):
    process_artifact(artifact)

if __name__ == "__main__":
    application_deploy(artifact={"test": "value"})
