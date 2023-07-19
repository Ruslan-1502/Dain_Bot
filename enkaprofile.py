async def encprofile(uid):
    profile = None
    async with encbanner.ENC() as encard:
        try:
            ENCpy = await encard.enc(uids=uid)
            profile = await encard.profile(enc=ENCpy, image=True)
        except Exception as e:
            print(f"Произошла ошибка с uid {uid}: {e}")  # Обработка других ошибок и вывод uid
    return profile

