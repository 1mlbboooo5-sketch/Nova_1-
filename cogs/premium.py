import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import config

class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_expiry.start()

    @commands.hybrid_command(name="buy_premium", description="প্রিমিয়ামের জন্য ট্রানজ্যাকশন আইডি দিন")
    async def buy_premium(self, ctx, transaction_id: str):
        admin = await self.bot.fetch_user(config.ADMIN_ID)
        embed = discord.Embed(title="New Premium Request", color=discord.Color.gold())
        embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})")
        embed.add_field(name="TxID", value=transaction_id)
        
        view = PremiumAction(self.bot, ctx.author.id)
        await admin.send(embed=embed, view=view)
        await ctx.send("✅ আপনার ট্রানজ্যাকশন আইডি পাঠানো হয়েছে। অ্যাডমিন চেক করে আপনাকে জানিয়ে দেবে।")

    @tasks.loop(minutes=30)
    async def check_expiry(self):
        now = datetime.utcnow()
        expired = self.bot.db.premium_users.find({"expiry": {"$lt": now}})
        async for user in expired:
            await self.bot.db.premium_users.delete_one({"user_id": user['user_id']})

class PremiumAction(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="Approve (30 Days)", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        expiry = datetime.utcnow() + timedelta(days=30)
        await self.bot.db.premium_users.update_one(
            {"user_id": self.user_id}, {"$set": {"expiry": expiry}}, upsert=True
        )
        user = await self.bot.fetch_user(self.user_id)
        try: await user.send("🎉 অভিনন্দন! আপনার ৩০ দিনের প্রিমিয়াম অ্যাক্টিভেট হয়েছে।")
        except: pass
        await interaction.response.send_message("Approved!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Premium(bot))
  
