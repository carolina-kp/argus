"""Canonical watchlist seed. Symbols map to CoinGecko ids and DeFiLlama slugs."""

SEED_WATCHLIST: list[dict[str, object]] = [
    {"symbol": "BTC", "name": "Bitcoin", "coingecko_id": "bitcoin",
     "defillama_slug": None, "is_stablecoin": False},
    {"symbol": "ETH", "name": "Ethereum", "coingecko_id": "ethereum",
     "defillama_slug": None, "is_stablecoin": False},
    {"symbol": "SOL", "name": "Solana", "coingecko_id": "solana",
     "defillama_slug": None, "is_stablecoin": False},
    {"symbol": "AAVE", "name": "Aave", "coingecko_id": "aave",
     "defillama_slug": "aave", "is_stablecoin": False},
    {"symbol": "UNI", "name": "Uniswap", "coingecko_id": "uniswap",
     "defillama_slug": "uniswap", "is_stablecoin": False},
    {"symbol": "LINK", "name": "Chainlink", "coingecko_id": "chainlink",
     "defillama_slug": "chainlink", "is_stablecoin": False},
    {"symbol": "USDC", "name": "USD Coin", "coingecko_id": "usd-coin",
     "defillama_slug": None, "is_stablecoin": True},
    {"symbol": "USDT", "name": "Tether", "coingecko_id": "tether",
     "defillama_slug": None, "is_stablecoin": True},
]
