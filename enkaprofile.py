from enkacard import encbanner
import asyncio

async def encprofile(uid):
    profile = None
    async with encbanner.ENC() as encard:
        ENCpy = await encard.enc(uids=uid)
        try:
            profile = await encard.profile(enc=ENCpy, image=True)
        except AttributeError:
            print("Карточка игрока не найдена")  # Вместо print может быть любая другая обработка
    return profile
