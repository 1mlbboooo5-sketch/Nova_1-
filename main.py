import discord
import os
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import config

async def get_prefix(bot, message):
    default = "Nova "
    if not message.guild:
        return default
    
    # ডেটাবেজ থেকে কাস্টম প্রিফিক্স খোঁজা
    data = await bot.db.guild_settings.find_one({"guild_id": message.guild.id})
    custom = data.get("prefix") if data else None
    
    if custom:
        # Case-insensitive (বড়/ছোট হাতের অক্ষর) সাপোর্ট
        return commands.when_mentioned_or(default, custom.lower(), custom.upper())(bot, message)
    return commands.when_mentioned_or(default)(bot, message)

class NovaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix=get_prefix, 
            intents=intents,
            case_insensitive=True,      # কমান্ড Help/help দুটোতেই কাজ করবে
            strip_after_prefix=True     # প্রিফিক্স ও কমান্ডের মাঝে স্পেস থাকলে কাজ করবে
        )

    async def setup_hook(self):
        # Database Connection
        self.db_client = AsyncIOMotorClient(config.MONGO_URL)
        self.db = self.db_client['nova_database']
        print("✅ MongoDB Connected Successfully!")

        # Cogs লোড করা
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Loaded Cog: {filename}')

bot = NovaBot()

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    # স্ল্যাশ কমান্ড সিঙ্ক করা
    await bot.tree.sync()

bot.run(config.TOKEN)
