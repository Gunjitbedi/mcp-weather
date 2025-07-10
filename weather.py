from typing import Any 
import httpx 
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server named "weather" 
mcp = FastMCP("weather")  

# Constants for the National Weather Service API 
NWS_API_BASE = "https://api.weather.gov" 
USER_AGENT = "weather-app/1.0"

# get weather alerts from the weather API

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a GET request to the weather API and return JSON (or None on error)."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

# Beuatify the weather alert API response to be more readable

def format_alert(feature: dict) -> str:
    """Format a weather alert feature into a readable string."""
    props = feature["properties"]
    return (
        f"Event: {props.get('event', 'Unknown')}\n"
        f"Area: {props.get('areaDesc', 'Unknown')}\n"
        f"Severity: {props.get('severity', 'Unknown')}\n"
        f"Description: {props.get('description', 'No description available')}\n"
        f"Instructions: {props.get('instruction', 'No specific instructions provided')}"
    )

# Tool1: takes US state as input and gives formatted alert back to MCP Server
@mcp.tool()
async def get_alerts(state: str) -> str:
    print(f"Getting alerts for {state}")
    """Get weather alerts for a US state (two-letter code)."""
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)
    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."
    if not data["features"]:
        return "No active alerts for this state."
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

# Tool2: takes latitude and longitude as input and gives forcasted information to MCP Server
@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location (latitude, longitude)."""
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)
    if not points_data:
        return "Unable to fetch forecast data for this location."
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)
    if not forecast_data:
        return "Unable to fetch detailed forecast."
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # show next 5 periods
        forecast = (
            f"{period['name']}:\n"
            f"  Temperature: {period['temperature']}°{period['temperatureUnit']}\n"
            f"  Wind: {period['windSpeed']} {period['windDirection']}\n"
            f"  Forecast: {period['detailedForecast']}"
        )
        forecasts.append(forecast)
    return "\n---\n".join(forecasts)


@mcp.prompt
def plan_the_evening(text: str) -> str:
    """Plan the evening based on the weather forecast."""
    return f"Plan the evening based on the weather forecast:\n\n{text}"

if __name__ == "__main__":
    mcp.run(transport='stdio')     