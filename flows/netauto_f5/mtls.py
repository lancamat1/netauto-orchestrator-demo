from prefect import flow

@flow(log_prints=True)
def process_mtls_application():
    print("Processing Netauto mTLS Application...")