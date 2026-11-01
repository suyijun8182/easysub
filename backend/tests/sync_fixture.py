"""Disposable localhost-only HTTP integration fixture; never opens the application database."""
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models import User, Currency, Category
from app.routers import auth, subscriptions, sync
from app.security import hash_password

engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
with Session(engine) as db:
    db.add(User(id=1, username='sync-fixture', email='fixture@example.test', password_hash=hash_password('fixture-password')))
    db.add(Currency(code='CNY', name='人民币', symbol='¥', is_custom=False))
    db.add(Category(name='视频', icon='🎬', sort=0, is_system=True))
    db.commit()
app = FastAPI()
for router in (auth.router, subscriptions.router, sync.router):
    app.include_router(router)
def fixture_db():
    with Session(engine) as db:
        yield db
app.dependency_overrides[get_db] = fixture_db
