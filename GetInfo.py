import asyncio
from enkanetwork import EnkaNetworkAPI
from enkanetwork.exception import EnkaPlayerNotFound
from aiohttp.client_exceptions import ClientOSError

client = EnkaNetworkAPI()

async def get_player(uid):
    try:
        async with client:
            data = await client.fetch_user_by_uid(uid)
            return data.player
    except asyncio.TimeoutError:
        print("Timeout error occurred")
        return None
    except EnkaPlayerNotFound:
        print("Player not found")
        return None
    except ClientOSError as e:
        print(f"ClientOSError occurred: {e}")
        return None
