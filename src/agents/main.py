import asyncio
import os
import sys

from contextlib import asynccontextmanager
from typing import Any, List, Dict

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
from agent_executor import (
    AirbnbAgentExecutor,
)
from airbnb_agent import (
    AirbnbAgent,
)
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv(override=True)

SERVER_CONFIGS = {
    'bnb': {
        'command': 'npx',
        'args': ['-y', '@openbnb/mcp-server-airbnb', '--ignore-robots-txt'],
        'transport': 'stdio',
    },
}


app_context: dict[str, Any] = {}


DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 10002
DEFAULT_LOG_LEVEL = 'info'

@asynccontextmanager
async def app_lifespan(context: Dict[str, Any]):
    """Manages the lifecycle of shared resources like the MCP client and tools."""
    print('Lifespan: Initializing MCP client and tools...')
    mcp_client_instance: MultiServerMCPClient | None = None

    try:
        mcp_client_instance = MultiServerMCPClient(SERVER_CONFIGS)
        mcp_tools = await mcp_client_instance.get_tools()
        context['mcp_tools'] = mcp_tools

        tool_count = len(mcp_tools) if mcp_tools else 0
        print(
            f'Lifespan: MCP Tools preloaded successfully ({tool_count} tools found).'
        )
        yield

    except Exception as e:
        print(f'Lifespan: Error during initialization: {e}', file=sys.stderr)
        raise
    finally:
        print('Lifespan: Shutting down MCP client...')
        # Check if the MultiServerMCPClient instance was created
        # The original code called __aexit__ on the MultiServerMCPClient instance
        # (which was mcp_client_manager). We assume this is still the correct cleanup method.
        if (mcp_client_instance
        ):
            if hasattr(mcp_client_instance, '__aexit__'):
                try:
                    print(
                        f'Lifespan: Calling __aexit__ on {type(mcp_client_instance).__name__} instance...'
                    )
                    await mcp_client_instance.__aexit__(None, None, None)
                    print(
                        'Lifespan: MCP Client resources released via __aexit__.'
                    )
                except Exception as e:
                    print(
                        f'Lifespan: Error during MCP client __aexit__: {e}',
                        file=sys.stderr,
                    )

            else:
                print(
                    f'Lifespan: CRITICAL - {type(mcp_client_instance).__name__} instance does not have __aexit__ method for cleanup. Resource leak possible.',
                    file=sys.stderr,
                )

        else:
            print(
                'Lifespan: MCP Client instance was not created, no shutdown attempt via __aexit__.'
            )

        print('Lifespan: Clearing application context.')
        context.clear()

def main(
        host: str = DEFAULT_HOST,
        port: str = DEFAULT_PORT,
        log_level: str = DEFAULT_LOG_LEVEL
):
    if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') != 'TRUE' and not os.getenv('GOOGLE_API_KEY'):
        raise ValueError(
            'GOOGLE_API_KEY environment variable not set and '
            'GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
        )
    async def run_server_async():
        async with app_lifespan(app_context):
            if not app_context.get('mcp_tools'):
                print(
                    'Warning: MCP tools were not loaded. Agent may not function correctly.',
                    file=sys.stderr,
                )

            airbnb_agent_executor = AirbnbAgentExecutor(
                mcp_tools=app_context.get('mcp_tools', [])
            )

            request_handler = DefaultRequestHandler(
                agent_executor=airbnb_agent_executor,
                task_store=InMemoryTaskStore(),
            )

            a2a_server = A2AStarletteApplication(
                agent_card=get_agent_card(host, port),
                http_handler=request_handler,
            )
            asgi_app = a2a_server.build()
            config = uvicorn.Config(
                app=asgi_app,
                host=host,
                port=port,
                log_level=log_level.lower(),
                lifespan='auto',
            )
            uvicorn_server = uvicorn.Server(config)

            print(
                f'Starting Uvicorn server at http://{host}:{port} with log-level {log_level}...'
            )
            try:
                await uvicorn_server.serve()
            except KeyboardInterrupt:
                print('Server shutdown requested (KeyboardInterrupt).')
            finally:
                print('Uvicorn server has stopped.')
                # The app_lifespan's finally block handles mcp_client shutdown

    try:
        asyncio.run(run_server_async())
    except RuntimeError as e:
        if 'cannot be called from a running event loop' in str(e):
            print(
                'Critical Error: Attempted to nest asyncio.run(). This should have been prevented.',
                file=sys.stderr,
            )
        else:
            print(f'RuntimeError in main: {e}', file=sys.stderr)
        sys.exit(1)


def get_agent_card(host: str, port: int):
    capabilities = AgentCapabilities(streaming=True, push_notifications=True)
    skill = AgentSkill(
        id='airbnb_search',
        name='Search airbnb accommodation',
        description='Helps with accommodation search using airbnb',
        tags=['airbnb accomodation'],
        examples=[
            'Please find a room in LA, CA, April 15, 2025, checkout date is april 18, 2 adults'
        ],
    )
    app_url = os.environ.get('APP_URL', f'http://{host}:{port}')
    return AgentCard(
        name='Airbnb Agent',
        description='Helps with searching accommodation',
        url=app_url,
        version='1.0.0',
        default_input_modes=AirbnbAgent.SUPPORTED_CONTENT_TYPES,
        default_output_modes=AirbnbAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

@click.command()
@click.option(
    '--host',
    'host',
    default=DEFAULT_HOST,
    help='Hostname to bind the server to.',
)
@click.option(
    '--port',
    'port',
    default=DEFAULT_PORT,
    type=int,
    help='Port to bind the server to.',
)
@click.option(
    '--log-level',
    'log_level',
    default=DEFAULT_LOG_LEVEL,
    help='Uvicorn log level.',
)
def cli(host: str, port: int, log_level: str):
    main(host, port, log_level)


if __name__ == '__main__':
    main()























