import asyncio
from chronicle import HydraClient

async def main():
    c = HydraClient()
    await c.setup_demo()
    print("CURRENT", await c.current_assertion("Emmanuel", "preferred_editor"))
    print("HISTORY", await c.history("Emmanuel", "preferred_editor"))
    print("ABSTAIN", await c.abstain("Emmanuel", "preferred_language"))

if __name__ == "__main__": asyncio.run(main())
