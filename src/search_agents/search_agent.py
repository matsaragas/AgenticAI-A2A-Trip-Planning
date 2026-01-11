import serpapi
import logging
from typing import Optional, Dict, Any

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from google.genai import types


logger = logging.getLogger(__name__)


retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)


def web_search(query: str) -> Optional[str]:
    """Finds general knowledge information using Google Search. Can
    also be used to augment 'general' knowledge to a previous
    specialist query.

    Args:
        query: The search query provided by the users to search for a particular topic

    Returns:
        A formatted string with search results, or None if no results.

    """
    serpapi_params = {
        "engine": "google",
        "api_key": config["serpapi_key"]
    }
    try:
        search = serpapi.search({
            **serpapi_params,
            "q": query,
            "num": 5,
        })
    except Exception as e:
        logger.error(f"SerpAPI request failed for query '{query}': {e}", exc_info=True)
        return f"Search failed due to an internal error. Query: '{query}'"


    # Validate response structure
    if not isinstance(search, Dict):
        logger.error(f"Unexpected SerpAPI response type: {type(search)} for query '{query}'")
        return f"Unexpected response format from search API."

    results = search["organic_results"]
    if not results:
        logger.warning(f"No search results found for query '{query}'")
        return f"No results found for query: '{query}'. Try a different search."

    contexts = "\n---\n".join(
        ["\n".join([x["title"], x["snippet"], x["link"]]) for x in results]
    )
    return contexts


search_agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    name="Google_Search_Agent",
    description="An agent to search google and retrieve information relevant to user's queries",
    instruction="""You are a Google search assistant. You search the web using google and retrieve information that 
     is relevant to user's queries. Your primary function is to utilize the provided tools to retrieve information 
     in response to user queries. Ensure that all responses include the detailed output from the tools used and are 
     formatted in Markdown""",
    tools=[web_search],
)

