"""Offline contract tests: no HydraDB/network required."""
import asyncio
from unittest.mock import AsyncMock
from chronicle import HydraClient

async def main():
    c = HydraClient()
    c.query = AsyncMock(side_effect=[{"rows": []}, {"rows": [{"value": "neovim"}]}, {"rows": []}])
    await c.setup_demo()
    current = await c.current_assertion("Emmanuel", "preferred_editor")
    missing = await c.abstain("Emmanuel", "preferred_language")
    assert current["rows"][0]["value"] == "neovim"
    assert missing["status"] == "NOT_IN_MEMORY"
    print("chronicle-offline-contracts-ok")

if __name__ == "__main__": asyncio.run(main())
