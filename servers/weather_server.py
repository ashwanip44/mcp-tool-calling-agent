import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient

load_dotenv()

mcp = FastMCP("WeatherServer")

tavily_api_key = os.getenv("TAVILY_API_KEY")

if not tavily_api_key:
    raise RuntimeError("TAVILY_API_KEY is not configured in .env")

tavily_client = TavilyClient(api_key=tavily_api_key)


@mcp.tool()
def get_weather(city: str) -> str:
    """Get current weather information for a city."""

    print(
        f"Searching weather for: {city}",
        file=sys.stderr
    )

    query = f"current weather in {city} today"

    try:
        result = tavily_client.search(
            query=query,
            max_results=3
        )
    except Exception as e:
        return f"Weather search failed for {city}: {e}"

    results = result.get("results", [])

    if not results:
        return f"No weather information found for {city}."

    output = []

    for item in results:
        title = item.get("title", "")
        content = item.get("content", "")
        url = item.get("url", "")

        output.append(
            f"Title: {title}\n"
            f"Information: {content}\n"
            f"Source: {url}"
        )

    return "\n\n".join(output)


if __name__ == "__main__":
    mcp.run(transport="stdio")