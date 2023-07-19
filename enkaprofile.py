
from enkacard import encbanner
import asyncio

async def card(uid):
    async with encbanner.ENC() as encard:
        ENCpy = await encard.enc(uids=uid)
        return await encard.creat(ENCpy, 1)
