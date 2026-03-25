import sys
import asyncio
from core.tools import get_unread_emails

async def main():
    print("Testing get_unread_emails...")
    result = await get_unread_emails(5)
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
