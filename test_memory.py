import asyncio
from core.history import history
from core.tools import remember, forget
from core.engine import _load_user_memory

async def main():
    print("🧹 Cleaning old memory...")
    for mem in history.get_all_memories():
        await forget(mem["id"])

    print("🧠 Testing 'remember' tool...")
    await remember("User loves Italian food.")
    await remember("User is building a Long-Term Memory feature.")

    print("🔍 Fetching memory injection block...")
    mem_block = await _load_user_memory()
    print(mem_block)

    print("🧹 Testing 'forget' tool...")
    mems = history.get_all_memories()
    if mems:
        await forget(mems[0]["id"])
    
    print("🔍 Fetching memory injection block after parsing...")
    mem_block_after = await _load_user_memory()
    print(mem_block_after)

if __name__ == "__main__":
    asyncio.run(main())
