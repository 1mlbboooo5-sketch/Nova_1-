import discord
import os
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import config

async def get_prefix(bot, message):
    default = "Nova "
    if not message.guild:
        return default
    # MongoDB থেকে সার্ভারের কাস্টম প্রিফিক্স চেক করা
    data = await bot.db.guild_settings.find_one({"guild_id": message.guild.id})
    custom = data.get("prefix") if data else None
    
    if custom:
        # Case-insensitive সাপোর্ট (ছোট ও বড় হাতের অক্ষর)
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
            case_insensitive=True,
            strip_after_prefix=True # স্পেস থাকলেও কমান্ড কাজ করবে
        )

    async def setup_hook(self):
        # Database Connection
        self.db_client = AsyncIOMotorClient(config.MONGO_URL)
        self.db = self.db_client['nova_database']
        print("✅ MongoDB কানেক্টেড!")

        # cogs ফোল্ডার থেকে সব মডিউল লোড করা
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Loaded Cog: {filename}')

bot = NovaBot()

@bot.event
async def on_ready():
    print(f'✅ {bot.user} হিসেবে লগইন করেছি!')
    await bot.tree.sync() # স্ল্যাশ কমান্ড আপডেট করা

bot.run(config.TOKEN)
      
