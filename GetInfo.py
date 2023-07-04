import asyncio
from enkanetwork import EnkaNetworkAPI
from enkanetwork.exception import EnkaPlayerNotFound
from aiohttp.client_exceptions import ClientOSError

client = EnkaNetworkAPI()

async def get_player(uid):
    try:
        async with client:
            data = await client.fetch_user(uid)
            return data.player
    except asyncio.TimeoutError:
        print("Timeout error occurred")
        return None
    except ValueError:
        print("Value error occurred")
        return None
    except EnkaPlayerNotFound:
        print(f"Character not found with id: {uid}")
        return None
    except ClientOSError as e:
        print(f"ClientOSError occurred: {e}")
        return None

