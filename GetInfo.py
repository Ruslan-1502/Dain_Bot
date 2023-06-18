import asyncio
from enkanetwork import EnkaNetworkAPI
from enkanetwork.exception import EnkaPlayerNotFound

client = EnkaNetworkAPI()

async def get_player(uid):
    try:
        async with client:
            data = await client.fetch_user(uid)
            return data.player
    except asyncio.TimeoutError:
        return None
    except ValueError:
        return None
    except EnkaPlayerNotFound:
        return None
