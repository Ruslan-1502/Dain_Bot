from enkacard import encbanner
import asyncio

async def encprofile(uids):
    await encbanner.update()
    async with encbanner.ENC(uid=uids) as encard:
        try:
            image = await encard.profile(card=True, teamplate=1)
            card_image = image.card
        except Exception as e:
            card_image = None
            print(f"Произошла ошибка при создании карты: {e}")
        return card_image
    # profile = None
    # async with encbanner.ENC() as encard:
    #     try:
    #         await encbanner.update()
    #         ENCpy = await encard.enc(uids=uid)
    #         profile = await encard.profile(enc=ENCpy, image=True)
    #     except AttributeError:
    #         print(f"Карточка игрока не найдена для uid {uid}")  # Выводим uid с ошибкой
    #     except Exception as e:
    #         print(f"Произошла ошибка с uid {uid}: {e}")  # Обработка других ошибок и вывод uid
    # return profile
