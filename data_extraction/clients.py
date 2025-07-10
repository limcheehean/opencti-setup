from os import getenv

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from openai import OpenAI
from pycti import OpenCTIApiClient
from sentence_transformers import SentenceTransformer
from urllib3 import disable_warnings

disable_warnings()  # Disable warning for elasticsearch https
load_dotenv()


def get_opencti():
    return OpenCTIApiClient(getenv("OPENCTI_URL"), getenv("OPENCTI_API_KEY"), ssl_verify=True)


def get_elasticsearch():
    return Elasticsearch(
        "https://localhost:9200",
        request_timeout=120,
        basic_auth=(getenv("ELASTICSEARCH_USER"), getenv("ELASTICSEARCH_PASSWORD")),
        verify_certs=False
    )


def get_model(model_name):
    match model_name:
        case "gpt-4o-mini":
            return OpenAI(base_url="https://api.openai.com/v1", api_key=getenv("OPENAI_API_KEY"))
        case "deepseek-chat":
            return OpenAI(base_url="https://api.deepseek.com", api_key=getenv("DEEPSEEK_API_KEY"))
        case "all-MiniLM-L6-v2":
            return SentenceTransformer(model_name)
        case _:
            raise ValueError(f"Model {model_name} not supported")
