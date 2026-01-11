import logging
import os

import click
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from search_executor import SearchExecutor

from search_agent import search_agent

load_dotenv()

logging.basicConfig()

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 10003


def main(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    # Verify an API key is set.
    # Not required if using Vertex AI APIs.
    if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') != 'TRUE' and not os.getenv(
            'GOOGLE_API_KEY'
    ):
        raise ValueError(
            'GOOGLE_API_KEY environment variable not set and '
            'GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
        )

    skill = AgentSkill(
        id='info_search',
        name='Information Search',
        description='It retrieves information from the web using google search',
        tags=['search', 'information'],
        examples=['what is few exhibitions to visit in London, UK'],
    )
    app_url = os.environ.get('APP_URL', f'http://{host}:{port}')
    agent_card = AgentCard(
        name='Search Agent',
        description='Helps with searching general information on the web',
        url=app_url,
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )
