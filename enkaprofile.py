
from enkacard import encbanner
import asyncio

async def encprofile(uid):
    profile = None
    async with encbanner.ENC() as encard:
        try:
            ENCpy = await encard.enc(uids=uid)
            profile = await encard.create(ENCpy, 1)
        except AttributeError:
            print(f"Карточка игрока не найдена для uid {uid}")  # Выводим uid с ошибкой
        except Exception as e:
            print(f"Произошла ошибка с uid {uid}: {e}")  # Обработка других ошибок и вывод uid
    return profile
