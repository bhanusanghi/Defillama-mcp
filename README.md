# 🦙 DefiLlama MCP Server

A simple, powerful Model Context Protocol (MCP) server that gives AI assistants access to real-time DeFi data from DefiLlama. Works seamlessly with **Cursor IDE**, **Claude Desktop**, **Zed**, and other MCP-compatible tools.

## 🚀 Quick Install

### Option 1: Direct Installation (Recommended)

```bash
# Install from PyPI (coming soon) or clone locally
git clone https://github.com/bhanusanghi/Defillama-mcp.git
cd defillama

# Install with pip
pip install -e .

# Test it works
defillama-mcp --help
```

### Option 2: Manual Setup

```bash
# Download the server file
curl -O https://raw.githubusercontent.com/bhanusanghi/Defillama-mcp/main/defillama_mcp_server.py

# Install dependencies
pip install mcp httpx

# Run directly
python defillama_mcp_server.py
```

## 🖥️ IDE Integration

### Cursor IDE

1. Open Cursor settings (`Cmd/Ctrl + ,`)
2. Go to "Features" → "Model Context Protocol"
3. Add a new server:

```json
{
  "name": "DefiLlama",
  "command": "defillama-mcp"
}
```

Or with full path:
```json
{
  "name": "DefiLlama", 
  "command": "python",
  "args": ["/absolute/path/to/defillama_mcp_server.py"]
}
```

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "defillama": {
      "command": "defillama-mcp"
    }
  }
}
```

### Zed Editor

Add to your Zed settings:

```json
{
  "assistant": {
    "mcp_servers": {
      "defillama": {
        "command": "defillama-mcp"
      }
    }
  }
}
```

## 🎯 What You Get

Once installed, your AI assistant can:

### 💰 **Get Token Prices**
```
"What's the current price of WETH and USDC?"
"How much was Bitcoin worth on January 1st, 2024?"
```

### 🌾 **Analyze Yield Farming**
```
"Find yield farming pools with over $10M TVL"
"Show me the best stablecoin yield opportunities"
"What's the APY for pool XYZ?"
```

### 📊 **DeFi Intelligence**
```
"Analyze my portfolio: WETH, USDC, AAVE"
"Compare yields across different protocols"
"What chains have the highest TVL?"
```

## 🛠️ Available Tools

| Tool | Description | Example |
|------|-------------|---------|
| `get_current_prices` | Real-time token prices | Current WETH price |
| `get_historical_prices` | Historical price data | ETH price on 2024-01-01 |
| `get_yield_pools` | Yield farming pools | Pools with >$1M TVL |
| `get_pool_chart` | Pool performance history | APY trends for a pool |

## 🔧 Troubleshooting

### Common Issues

**"Command not found: defillama-mcp"**
```bash
# Reinstall with pip
pip install -e .

# Or use full path
python /path/to/defillama_mcp_server.py
```

**"Module not found"**
```bash
# Install dependencies
pip install mcp httpx
```

**"Server not responding"**
```bash
# Test the server directly
python defillama_mcp_server.py
# Should show: "Starting DefiLlama MCP Server..."
```

### Testing Your Setup

```bash
# Run the test suite
python test_server.py

# Should show all green checkmarks ✅
```

## 📚 Token Formats Supported

The server accepts multiple token identifier formats:

- **Contract addresses**: `ethereum:0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2`
- **Symbols**: `WETH`, `USDC`, `BTC`
- **CoinGecko IDs**: `coingecko:bitcoin`
- **Multiple tokens**: `WETH,USDC,AAVE` (comma-separated)

## 🌐 Supported Chains

Ethereum, BSC, Polygon, Avalanche, Arbitrum, Optimism, Fantom, Solana, and 40+ more chains supported by DefiLlama.

## 🔒 Privacy & Security

- ✅ **No API keys required** - Uses public DefiLlama endpoints
- ✅ **No data collection** - Runs entirely locally
- ✅ **Open source** - Full transparency
- ✅ **Rate limit friendly** - Respects API limits

## 📖 Examples

### Basic Price Queries
```
User: "What's WETH trading at?"
AI: Uses get_current_prices("WETH") → "WETH is currently $3,245.67"
```

### Yield Farming Analysis
```
User: "Find me high-yield stablecoin pools"
AI: Uses get_yield_pools(min_tvl=1000000) → Shows top pools with APY data
```

### Portfolio Analysis  
```
User: "Analyze my DeFi portfolio: WETH, USDC, AAVE"
AI: Uses multiple tools → Comprehensive analysis with prices, yields, and recommendations
```

## 🚀 Advanced Usage

### Custom Configuration

Set environment variables for advanced configuration:
```bash
export DEFILLAMA_TIMEOUT=60    # API timeout in seconds
export DEFILLAMA_DEBUG=true    # Enable debug logging
```

### Integration with Other Tools

The MCP server works with any MCP-compatible client:
- **Cursor IDE** - Code with DeFi context
- **Claude Desktop** - Chat with DeFi data
- **Zed** - Lightweight editor integration  
- **Custom tools** - Build your own MCP client

## 📝 Requirements

- **Python 3.8+**
- **Dependencies**: `mcp`, `httpx` (auto-installed)
- **Internet connection** for DefiLlama API access

## 🤝 Contributing

Found a bug or want to add features? 

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - Use freely in personal and commercial projects.

## 🆘 Support

- **Issues**: Open a GitHub issue
- **Questions**: Check existing issues or start a discussion
- **Updates**: Watch the repository for new features

---

**Made with ❤️ for the DeFi community. Happy yield farming! 🌾**