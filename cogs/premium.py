import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import config

class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_premium_expiry.start()

    @commands.hybrid_command(
        name="buy_premium", 
        description="Submit your transaction ID to buy premium membership."
    )
    async def buy_premium(self, ctx, transaction_id: str):
        admin = await self.bot.fetch_user(config.ADMIN_ID)
        
        embed = discord.Embed(title="New Premium Request", color=discord.Color.gold())
        embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})")
        embed.add_field(name="Transaction ID", value=transaction_id)
        embed.set_footer(text="Verify the payment and click Approve.")
        
        view = PremiumAction(self.bot, ctx.author.id)
        await admin.send(embed=embed, view=view)
        
        await ctx.send("✅ Your request has been sent to the admin. You will be notified once it's verified!")

    @tasks.loop(hours=1)
    async def check_premium_expiry(self):
        now = datetime.utcnow()
        # মেয়াদ শেষ হওয়া ইউজারদের খুঁজে বের করে ডিলেট করা
        await self.bot.db.premium_users.delete_many({"expiry": {"$lt": now}})

class PremiumAction(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="Approve (30 Days)", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        expiry = datetime.utcnow() + timedelta(days=30)
        await self.bot.db.premium_users.update_one(
            {"user_id": self.user_id}, 
            {"$set": {"expiry": expiry}}, 
            upsert=True
        )
        
        user = await self.bot.fetch_user(self.user_id)
        try:
            await user.send("🎉 Congratulations! Your 30-day Premium is now active.")
        except:
            pass
            
        await interaction.response.send_message(f"User {self.user_id} approved!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Premium(bot))
