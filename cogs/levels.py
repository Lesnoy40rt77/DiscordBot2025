import discord
from discord.ext import commands
import os
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import config

# Checking whether DATABASE_URL is determined
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///levels.db")

# Heroku uses "postgres://", but sqlalchemy needs "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
engine = sqlalchemy.create_engine(DATABASE_URL, echo=False)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Levels table
class Level(Base):
    __tablename__ = "levels"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    user_id = sqlalchemy.Column(sqlalchemy.BigInteger, unique=True, nullable=False)
    guild_id = sqlalchemy.Column(sqlalchemy.BigInteger, nullable=False)
    xp = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    level = sqlalchemy.Column(sqlalchemy.Integer, default=1)


# Creating table if it doesn't exist
if "sqlite" in DATABASE_URL:
    Base.metadata.create_all(bind=engine)


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return  # Ignoring bots

        session = SessionLocal()
        user_entry = session.query(Level).filter_by(user_id=message.author.id, guild_id=message.guild.id).first()

        if not user_entry:
            user_entry = Level(user_id=message.author.id, guild_id=message.guild.id)
            session.add(user_entry)

        user_entry.xp += len(message.content) // 5
        if user_entry.xp >= user_entry.level * 100:
            user_entry.xp = 0
            user_entry.level += 1
            if config.LEVEL_CHANNEL != 0:
                await config.LEVEL_CHANNEL.send(f"🎉 {message.author.mention} reached level {user_entry.level}!")

            else:
                await message.channel.send(f"🎉 {message.author.mention} reached level {user_entry.level}!")

        session.commit()
        session.close()


async def setup(bot):
    bot.add_cog(Levels(bot))
