from sqlalchemy import create_engine, Column, Integer, String, BigInteger, Boolean, Float
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime

# Database ka setup
DATABASE_URL = "sqlite:///bot_data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Admin Settings ke liye Table/Model
class AdminSettings(Base):
    __tablename__ = "admin_settings"
    id = Column(Integer, primary_key=True, index=True, default=1)
    channel_id = Column(BigInteger, nullable=True)
    shortener_api = Column(String, nullable=True)
    shortener_domain = Column(String, nullable=True)
    invite_duration_seconds = Column(Integer, default=86400) # Default: 1 din

# Users ke liye Table/Model
class User(Base):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True, index=True, unique=True)
    has_received_free_link = Column(Boolean, default=False)
    last_link_timestamp = Column(Float, nullable=True)

# Database aur tables create karna
def init_db():
    Base.metadata.create_all(bind=engine)

# Helper function jo admin settings ko get ya create karega
def get_or_create_admin_settings(db):
    settings = db.query(AdminSettings).filter(AdminSettings.id == 1).first()
    if not settings:
        settings = AdminSettings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

# Pehli baar run karne par DB initialize karna
init_db()
