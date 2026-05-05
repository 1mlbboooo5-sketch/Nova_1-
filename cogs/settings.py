import discord
from discord.ext import commands

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="setprefix", 
        description="Set a custom prefix for this server. (Admins only)"
    )
    @commands.has_permissions(administrator=True)
    async def setprefix(self, ctx, new_prefix: str):
        # স্পেস ক্লিন করা
        clean_prefix = new_prefix.strip()
        
        # MongoDB-তে সেভ করা
        await self.bot.db.guild_settings.update_one(
            {"guild_id": ctx.guild.id},
            {"$set": {"prefix": clean_prefix}},
            upsert=True
        )
        
        # ইংলিশে কনফার্মেশন রিপ্লাই
        embed = discord.Embed(
            title="Prefix Updated",
            description=f"✅ New prefix has been set to: `{clean_prefix}`\n\n"
                        f"• You can use it like `{clean_prefix}help` or `{clean_prefix} help`.\n"
                        f"• Default `Nova ` will always work.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Settings(bot))
