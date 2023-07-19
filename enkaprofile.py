
from enkacard import encbanner
import asyncio

async def encprofile(uid):
    profile = None
    async with encbanner.ENC() as encard:
        ENCpy = await encard.enc(uids=uid)
        profile = await encard.profile(enc=ENCpy, image=True)
    return profile
