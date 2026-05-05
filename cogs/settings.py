import discord
from discord.ext import commands

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="setprefix", description="বটের কাস্টম প্রিফিক্স সেট করো")
    @commands.has_permissions(administrator=True)
    async def setprefix(self, ctx, new_prefix: str):
        clean_prefix = new_prefix.strip()
        await self.bot.db.guild_settings.update_one(
            {"guild_id": ctx.guild.id},
            {"$set": {"prefix": clean_prefix}},
            upsert=True
        )
        await ctx.send(f"✅ প্রিফিক্স আপডেট হয়েছে: `{clean_prefix}`। (ডিফল্ট `Nova ` সবসময় কাজ করবে)")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        owner = guild.owner
        if owner:
            embed = discord.Embed(title="Nova - Setup", description="বটের ভাষা সেট করতে নিচের মেনু ব্যবহার করুন।", color=discord.Color.blue())
            view = LanguageSelectView(self.bot, guild.id)
            try: await owner.send(embed=embed, view=view)
            except: pass

class LanguageSelectView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    @discord.ui.select(
        placeholder="Select Language (১০টি ভাষা)",
        options=[
            discord.SelectOption(label="English", value="en", emoji="🇺🇸"),
            discord.SelectOption(label="Bengali", value="bn", emoji="🇧🇩"),
            discord.SelectOption(label="Hindi", value="hi", emoji="🇮🇳"),
            discord.SelectOption(label="Spanish", value="es", emoji="🇪🇸"),
            discord.SelectOption(label="French", value="fr", emoji="🇫🇷"),
            discord.SelectOption(label="Arabic", value="ar", emoji="🇸🇦"),
            discord.SelectOption(label="Japanese", value="ja", emoji="🇯🇵"),
            discord.SelectOption(label="Russian", value="ru", emoji="🇷🇺"),
            discord.SelectOption(label="Portuguese", value="pt", emoji="🇵🇹"),
            discord.SelectOption(label="German", value="de", emoji="🇩🇪"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select):
        await self.bot.db.guild_settings.update_one(
            {"guild_id": self.guild_id}, {"$set": {"language": select.values[0]}}, upsert=True
        )
        await interaction.response.send_message(f"✅ ভাষা সেট করা হয়েছে: **{select.values[0].upper()}**", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Settings(bot))
  
