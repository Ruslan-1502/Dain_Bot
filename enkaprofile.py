from enkacard import encbanner,enkanetwork
import asyncio

async def encprofile(uid):
    profile = None
    async with encbanner.ENC() as encard:
        ENCpy = await encard.enc(uids=uid)
        try:
            profile = await encard.profile(enc=ENCpy, image=True)
        except (AttributeError, enkanetwork.assets.CharacterNotFoundError) as e:
            print(f"Error occurred for character with id {uid}: {e}")
            # Handle the error accordingly
    return profile

