import logging
import os



from typing import List


class AirbnbAgent:

    """Airbnb Agent"""
    SYSTEM_INSTRUCTIONS = """You are a specialized assistant for Airbnb accommodation. Your primary function is to 
    utilize the provided tools to search for Airbnb listings and answer related questions. 
    You must rely exclusively on these tools for information; do not invent listings or prices. 
    Ensure that your Markdown-formatted response includes all relevant tool output, with particular 
    emphasis on providing direct links to listings"""


    RESPONSE_FORMAT_INSTRUCTIONS: str = (
        'Select status as "completed" if the request is fully addressed and no further input is needed. '
        'Select status as "input_required" if you need more information from the user or are asking a clarifying question. '
        'Select status as "error" if an error occurred or the request cannot be fulfilled.'
    )



    def __init__(self, mcp_tools: List[any]):
        """
        Initializes the Airbnb agent
        Args:
           mcp_tools: A list of preloaded MCP tools
        """
        logger.info('Initializing AirbnbAgent with MCP tools...')