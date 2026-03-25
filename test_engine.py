import sys
import os
import asyncio

# Ensure Sentinal_Lee is in the python path
project_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_dir)

from core.engine import chat

async def main():
    print("Testing chat stream...")
    async for event in chat("What is the time right now?", channel="cli_test"):
        if event["type"] == "content_chunk":
            print(event["content"], end="", flush=True)
        else:
                print(f"\n[{event['type']}] {str(event)}")
    print("\n--- Test Finished ---")

if __name__ == "__main__":
    asyncio.run(main())
