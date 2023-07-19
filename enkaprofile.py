from enkacard import encbanner
import asyncio

async def encprofile(uid):
    profile = None
    async with encbanner.ENC() as encard:
        try:
            ENCpy = await encard.enc(uids=uid)
            profile = await encard.profile(enc=ENCpy, image=True)
        except encbanner.CostumeNotFoundError:
            print(f"Костюм не найден для uid {uid}")
            return profile  # Возвращаем profile при возникновении исключения
        except Exception as e:
            print(f"Произошла ошибка с uid {uid}: {e}")
    return profile


