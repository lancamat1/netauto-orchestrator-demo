FROM python:3.12

# Accept external Python package registry URL (optional)
ARG AUTHED_ARTIFACT_REG_URL

# Copy Python requirements
COPY ./requirements.txt /requirements.txt

# Install dependencies
RUN pip install -r /requirements.txt
