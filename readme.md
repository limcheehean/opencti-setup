
# OpenCTI Sample Setup

This repository contains the necessary files to run an instance of OpenCTI via Docker Compose.

## Connectors

The following connectors are added into the docker-compose.yml file.\
The configurations can be found from: https://github.com/OpenCTI-Platform/connectors/tree/master/external-import. \
Additional connectors are also available at the same link.

- abuse-ssl
- abuseipdb-ipblacklist
- alienvault
- cisa-known-exploited-vunlerabilities
- cyber-campaign-collection
- cve
- malpedia
- malware-bazaar
- mitre-atlas
- mitre
- opencti
- redflag-domains
- stopforumspam
- threatfox
- urlhaus-recent-payloads
- urlhaus
- urlscan
- vulncheck
- wiz

## Setup

### Register for API Keys

Some connectors require an API key to work. Register at the following links:
- https://www.abuseipdb.com/register
- https://otx.alienvault.com/
- https://nvd.nist.gov/developers/request-an-api-key
- https://urlscan.io/user/signup
- https://docs.vulncheck.com/api

### Update .env file

1. Rename .env.sample to .env
2. Insert the API keys into the .env file.
3. Generate a v4 UUID from https://www.uuidgenerator.net/version4 for `OPENCTI_ADMIN_TOKEN`
4. Update other variables such as email and password as required.

### Run Docker Compose

To start the OpenCTI instance, run:
```
docker compose -p opencti up
```

## Python API Client

OpenCTI offers a Python client at https://github.com/OpenCTI-Platform/client-python.


## Data Extraction (WIP/Experimental)

Some scripts to pull data and ingest into local elasticsearch.\
Rename .env.sample to .env

- retriever.py (pull data from instance specified in .env)
- loader.py (load data into elasticsearch)
- embedder.py (generate embeddings)