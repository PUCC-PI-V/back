from prisma import Prisma

prisma = Prisma()

ADMIN_EMAIL = "admin@viboraink.com"
ADMIN_PASSWORD = "admin123"


async def connect_db() -> None:
    await prisma.connect()
    await ensure_admin_user()


async def disconnect_db() -> None:
    await prisma.disconnect()


async def ensure_admin_user() -> None:
    existing = await prisma.user.find_unique(where={"email": ADMIN_EMAIL})
    if existing is None:
        await prisma.user.create(
            data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
