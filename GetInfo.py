import asyncio
from enkanetwork import EnkaNetworkAPI
from enkanetwork.exception import EnkaPlayerNotFound


client = EnkaNetworkAPI()

async def get_player(uid):
    try:
        async with client:
            await client.update_assets()
            data = await client.fetch_user_by_uid(uid)
            return data.player
    except asyncio.TimeoutError:
        print("Timeout error occurred")
        return None
    except ValueError:
        print("Value error occurred")
        return None
    except EnkaPlayerNotFound:
        print("Player not found")
        return None
