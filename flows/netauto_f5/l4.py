from prefect import flow

@flow(log_prints=True)
def process_l4_application():
    print("Processing Netauto L4 Application...")