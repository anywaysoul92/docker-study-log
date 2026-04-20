from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URL = "mysql+aiomysql://root:password@db:3306/app_db"

engine = create_async_engine(DATABASE_URL)

AsyncSessionFactory = async_sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
)

