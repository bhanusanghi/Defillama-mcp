#!/usr/bin/env python3
"""
DefiLlama MCP Server

A Model Context Protocol server that provides access to DefiLlama's DeFi data APIs,
including token prices and yield farming information.

This server exposes tools for:
- Fetching current token prices
- Getting historical price data
- Retrieving yield pool information
- Analyzing pool performance

Usage:
    python defillama_mcp_server.py

For Claude Desktop integration, add to claude_desktop_config.json:
{
    "mcpServers": {
        "defillama": {
            "command": "python",
            "args": ["/path/to/defillama_mcp_server.py"]
        }
    }
}
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP(
    name="DefiLlama",
    dependencies=["httpx>=0.24.0"]
)

# Constants
DEFILLAMA_API_BASE = "https://api.llama.fi"
DEFILLAMA_COINS_API = "https://coins.llama.fi"
DEFILLAMA_YIELDS_API = "https://yields.llama.fi"
USER_AGENT = "DefiLlama-MCP-Server/1.0"
DEFAULT_TIMEOUT = 30.0

# Global HTTP client
http_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create the global HTTP client."""
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True
        )
    return http_client


async def make_api_request(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Make a request to the DefiLlama API with proper error handling.
    
    Args:
        url: The API endpoint URL
        params: Optional query parameters
        
    Returns:
        Parsed JSON response
        
    Raises:
        ValueError: If the API request fails or returns invalid data
    """
    client = await get_http_client()
    
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        # Handle empty responses
        if not response.content:
            raise ValueError("Empty response from API")
            
        return response.json()
        
    except httpx.HTTPStatusError as e:
        raise ValueError(f"API request failed with status {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        raise ValueError(f"Network error: {str(e)}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {str(e)}")


def format_price_data(data: Dict[str, Any]) -> str:
    """Format price data for display."""
    if not data or "coins" not in data:
        return "No price data available"
    
    formatted_lines = []
    for coin_id, coin_data in data["coins"].items():
        if not isinstance(coin_data, dict):
            continue
            
        symbol = coin_data.get("symbol", "Unknown")
        price = coin_data.get("price", "N/A")
        decimals = coin_data.get("decimals", "N/A")
        timestamp = coin_data.get("timestamp")
        
        formatted_price = f"${price:,.6f}" if isinstance(price, (int, float)) else str(price)
        
        timestamp_str = ""
        if timestamp:
            try:
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                timestamp_str = f" (as of {dt.strftime('%Y-%m-%d %H:%M:%S UTC')})"
            except (ValueError, TypeError):
                timestamp_str = f" (timestamp: {timestamp})"
        
        formatted_lines.append(f"• {symbol} ({coin_id}): {formatted_price}{timestamp_str}")
        if decimals != "N/A":
            formatted_lines[-1] += f" [Decimals: {decimals}]"
    
    return "\n".join(formatted_lines) if formatted_lines else "No valid price data found"


def format_pool_data(pools: List[Dict[str, Any]], limit: int = 20) -> str:
    """Format pool data for display."""
    if not pools:
        return "No pool data available"
    
    formatted_lines = ["🏊 **Top Yield Pools**\n"]
    
    # Sort by TVL (descending) and limit results
    sorted_pools = sorted(
        pools, 
        key=lambda x: float(x.get("tvlUsd", 0)), 
        reverse=True
    )[:limit]
    
    for i, pool in enumerate(sorted_pools, 1):
        pool_id = pool.get("pool", "Unknown")
        project = pool.get("project", "Unknown")
        symbol = pool.get("symbol", "Unknown")
        apy = pool.get("apy", 0)
        tvl = pool.get("tvlUsd", 0)
        chain = pool.get("chain", "Unknown")
        
        # Format large numbers
        if tvl >= 1_000_000:
            tvl_str = f"${tvl/1_000_000:.1f}M"
        elif tvl >= 1_000:
            tvl_str = f"${tvl/1_000:.1f}K"
        else:
            tvl_str = f"${tvl:.2f}"
        
        apy_str = f"{apy:.2f}%" if isinstance(apy, (int, float)) else "N/A"
        
        formatted_lines.append(
            f"{i:2d}. **{project}** - {symbol}\n"
            f"    📈 APY: {apy_str} | 💰 TVL: {tvl_str} | ⛓️ {chain}\n"
            f"    🆔 Pool ID: `{pool_id}`"
        )
    
    return "\n".join(formatted_lines)


# =============================================================================
# TOOLS
# =============================================================================

@mcp.tool()
async def get_current_prices(
    coins: str,
    search_width: Optional[str] = None
) -> str:
    """
    Get current prices for specified tokens.
    
    Args:
        coins: Comma-separated list of coin identifiers. Can be:
               - Contract addresses (e.g., ethereum:0xA0b86a33E6)
               - Coin gecko IDs (e.g., coingecko:bitcoin)
               - Symbols (e.g., WETH, USDC)
        search_width: Search width for price data (optional)
        
    Returns:
        Formatted string with current price information
        
    Examples:
        get_current_prices("ethereum:0xA0b86a33E6,coingecko:bitcoin")
        get_current_prices("WETH,USDC,WBTC")
    """
    try:
        # Clean and encode the coins parameter
        coins_clean = quote(coins.strip(), safe=',:-')
        url = f"{DEFILLAMA_COINS_API}/prices/current/{coins_clean}"
        
        params = {}
        if search_width:
            params["searchWidth"] = search_width
        
        logger.info(f"Fetching current prices for: {coins}")
        data = await make_api_request(url, params)
        
        return f"**Current Token Prices**\n\n{format_price_data(data)}"
        
    except Exception as e:
        logger.error(f"Error fetching current prices: {e}")
        return f"❌ Error fetching current prices: {str(e)}"


@mcp.tool()
async def get_historical_prices(
    timestamp: Union[int, str],
    coins: str,
    search_width: Optional[str] = None
) -> str:
    """
    Get historical prices for tokens at a specific timestamp.
    
    Args:
        timestamp: Unix timestamp or date string (YYYY-MM-DD)
        coins: Comma-separated list of coin identifiers
        search_width: Search width for price data (optional)
        
    Returns:
        Formatted string with historical price information
        
    Examples:
        get_historical_prices(1609459200, "ethereum:0xA0b86a33E6")
        get_historical_prices("2024-01-01", "WETH,USDC")
    """
    try:
        # Convert date string to timestamp if needed
        if isinstance(timestamp, str):
            try:
                if "-" in timestamp:  # Assume YYYY-MM-DD format
                    dt = datetime.strptime(timestamp, "%Y-%m-%d")
                    timestamp = int(dt.replace(tzinfo=timezone.utc).timestamp())
                else:
                    timestamp = int(timestamp)
            except ValueError:
                return "❌ Invalid timestamp format. Use Unix timestamp or YYYY-MM-DD format."
        
        coins_clean = quote(str(coins).strip(), safe=',:-')
        url = f"{DEFILLAMA_COINS_API}/prices/historical/{timestamp}/{coins_clean}"
        
        params = {}
        if search_width:
            params["searchWidth"] = search_width
        
        logger.info(f"Fetching historical prices for: {coins} at timestamp: {timestamp}")
        data = await make_api_request(url, params)
        
        # Format timestamp for display
        try:
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            date_str = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except (ValueError, TypeError):
            date_str = str(timestamp)
        
        return f"**Historical Token Prices ({date_str})**\n\n{format_price_data(data)}"
        
    except Exception as e:
        logger.error(f"Error fetching historical prices: {e}")
        return f"❌ Error fetching historical prices: {str(e)}"


@mcp.tool()
async def get_yield_pools(min_tvl: Optional[float] = None) -> str:
    """
    Get yield farming pools data.
    
    Args:
        min_tvl: Minimum TVL threshold in USD (optional)
        
    Returns:
        Formatted string with yield pool information
        
    Examples:
        get_yield_pools()
        get_yield_pools(1000000)  # Pools with at least $1M TVL
    """
    try:
        url = f"{DEFILLAMA_YIELDS_API}/pools"
        
        logger.info("Fetching yield pools data")
        data = await make_api_request(url)
        
        if not isinstance(data, dict) or "data" not in data:
            # The yields API returns the data directly as a list
            if isinstance(data, list):
                pools = data
            else:
                return "❌ Invalid pools data format received"
        else:
            pools = data["data"]
            if not isinstance(pools, list):
                return "❌ Expected list of pools but got different format"
        
        # Filter by minimum TVL if specified
        if min_tvl is not None:
            pools = [p for p in pools if p.get("tvlUsd", 0) >= min_tvl]
            filter_msg = f" (filtered by min TVL: ${min_tvl:,.0f})"
        else:
            filter_msg = ""
        
        result = f"**Yield Farming Pools{filter_msg}**\n\n"
        result += f"Found {len(pools)} pools\n\n"
        result += format_pool_data(pools)
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching yield pools: {e}")
        return f"❌ Error fetching yield pools: {str(e)}"


@mcp.tool()
async def get_pool_chart(pool_id: str) -> str:
    """
    Get historical data for a specific yield pool.
    
    Args:
        pool_id: The unique identifier for the pool
        
    Returns:
        Formatted string with pool historical data
        
    Examples:
        get_pool_chart("747c1d2a-c668-4682-b9f9-296708a3dd90")
    """
    try:
        pool_id_clean = quote(pool_id.strip(), safe='-')
        url = f"{DEFILLAMA_YIELDS_API}/chart/{pool_id_clean}"
        
        logger.info(f"Fetching pool chart for: {pool_id}")
        data = await make_api_request(url)
        
        if not isinstance(data, dict) or "data" not in data:
            return "❌ Invalid pool chart data format received"
        
        pool_data = data["data"]
        if not pool_data:
            return f"❌ No historical data found for pool: {pool_id}"
        
        # Get basic pool info
        status = data.get("status", "unknown")
        
        # Format historical data
        result_lines = [
            f"**Pool Historical Data**",
            f"🆔 Pool ID: `{pool_id}`",
            f"📊 Status: {status}",
            f"📈 Data Points: {len(pool_data)}",
            ""
        ]
        
        if len(pool_data) > 0:
            # Show recent data points (last 10)
            recent_data = pool_data[-10:] if len(pool_data) > 10 else pool_data
            result_lines.append("**Recent Performance:**")
            
            for point in recent_data:
                timestamp = point.get("timestamp")
                apy = point.get("apy")
                tvl = point.get("tvlUsd")
                
                if timestamp:
                    try:
                        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        date_str = dt.strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        date_str = str(timestamp)
                else:
                    date_str = "Unknown"
                
                apy_str = f"{apy:.2f}%" if isinstance(apy, (int, float)) else "N/A"
                
                if isinstance(tvl, (int, float)) and tvl >= 1_000_000:
                    tvl_str = f"${tvl/1_000_000:.1f}M"
                elif isinstance(tvl, (int, float)) and tvl >= 1_000:
                    tvl_str = f"${tvl/1_000:.1f}K"
                elif isinstance(tvl, (int, float)):
                    tvl_str = f"${tvl:.2f}"
                else:
                    tvl_str = "N/A"
                
                result_lines.append(f"• {date_str}: APY {apy_str}, TVL {tvl_str}")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        logger.error(f"Error fetching pool chart: {e}")
        return f"❌ Error fetching pool chart: {str(e)}"


# =============================================================================
# RESOURCES
# =============================================================================

@mcp.resource("chains://list")
def get_supported_chains() -> str:
    """List of supported blockchain networks in DefiLlama."""
    chains = [
        "Ethereum", "BSC", "Polygon", "Avalanche", "Fantom", "Arbitrum", "Optimism",
        "Solana", "Terra", "Heco", "xDai", "Harmony", "Moonriver", "Cronos",
        "Aurora", "Fuse", "KCC", "OKExChain", "Celo", "Moonbeam", "Metis",
        "Kava", "Klaytn", "Iotex", "Milkomeda", "DFK", "REI", "Astar", "Emerald",
        "Palm", "Kardia", "TomoChain", "Velas", "Syscoin", "Ubiq", "Energi",
        "Step", "Godwoken", "Callisto", "CSC", "Ergo", "Liquidchain", "Nahmii",
        "ThunderCore", "Telos", "EOS", "WAX", "Hive", "Kujira", "Cosmos"
    ]
    
    return f"**Supported Blockchain Networks ({len(chains)} total)**\n\n" + \
           "\n".join(f"• {chain}" for chain in chains)


@mcp.resource("api://endpoints")
def get_api_endpoints() -> str:
    """Available DefiLlama API endpoints."""
    endpoints = {
        "Price APIs": [
            "GET /prices/current/{coins} - Get current token prices",
            "GET /prices/historical/{timestamp}/{coins} - Get historical prices",
            "GET /batchHistorical - Get batch historical data",
            "GET /chart/{coins} - Get price charts",
            "GET /percentage/{coins} - Get price percentage changes"
        ],
        "TVL APIs": [
            "GET /protocols - List all protocols",
            "GET /protocol/{protocol} - Get protocol details",
            "GET /tvl/{protocol} - Get protocol TVL",
            "GET /v2/chains - List all chains",
            "GET /v2/historicalChainTvl/{chain} - Get chain TVL history"
        ],
        "Yield APIs": [
            "GET /pools - Get all yield pools",
            "GET /chart/{pool} - Get pool historical data"
        ]
    }
    
    result_lines = ["**DefiLlama API Endpoints**\n"]
    
    for category, endpoint_list in endpoints.items():
        result_lines.append(f"**{category}:**")
        for endpoint in endpoint_list:
            result_lines.append(f"  {endpoint}")
        result_lines.append("")
    
    return "\n".join(result_lines)


# =============================================================================
# PROMPTS
# =============================================================================

@mcp.prompt()
def analyze_defi_portfolio(tokens: str) -> str:
    """Generate a prompt for DeFi portfolio analysis."""
    return f"""Please analyze this DeFi portfolio and provide insights:

Tokens: {tokens}

Please provide:
1. Current price analysis for each token
2. Risk assessment (volatility, smart contract risks)
3. Yield farming opportunities
4. Portfolio diversification recommendations
5. Market trends affecting these assets

Use the DefiLlama tools to gather current data for your analysis."""


@mcp.prompt()
def find_yield_opportunities(min_apy: float = 5.0, max_risk: str = "medium") -> str:
    """Generate a prompt for finding yield farming opportunities."""
    return f"""Find the best yield farming opportunities with these criteria:

- Minimum APY: {min_apy}%
- Maximum risk level: {max_risk}

Please:
1. Get current yield pools data
2. Filter by the specified criteria
3. Analyze the top opportunities for:
   - Protocol reputation and security
   - Liquidity and TVL stability
   - Token pair composition
   - Impermanent loss risks
4. Provide specific recommendations with rationale

Use the DefiLlama yield tools to gather the latest data."""


# =============================================================================
# SERVER LIFECYCLE
# =============================================================================

async def cleanup():
    """Clean up resources on server shutdown."""
    global http_client
    if http_client:
        try:
            await http_client.aclose()
        except Exception:
            pass  # Ignore cleanup errors
        http_client = None


def main():
    """Run the DefiLlama MCP server."""
    logger.info("Starting DefiLlama MCP Server...")
    
    try:
        # Run the server
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        # Cleanup
        try:
            asyncio.run(cleanup())
        except Exception:
            pass  # Ignore cleanup errors during shutdown
        logger.info("DefiLlama MCP Server stopped")


if __name__ == "__main__":
    main()