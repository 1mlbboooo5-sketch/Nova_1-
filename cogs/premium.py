import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import config # তোমার config.py ফাইলটি ইমপোর্ট করা হলো

class ServerPremium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.qr_link = "https://cdn.discordapp.com/attachments/1465014056090996836/1501256569256673351/GooglePay_QR_1.png?ex=69fb69a2&is=69fa1822&hm=c8471ff9bc3e5e1c056209140c26911e2590655b8c1ac58022999f7b6ee62653&"
        # config.py থেকে ADMIN_ID নেওয়া হচ্ছে
        self.admin_user_id = config.ADMIN_ID

    @commands.hybrid_command(name="buy_premium", description="প্রিমিয়াম প্ল্যান এবং পেমেন্ট কিউআর কোড দেখুন।")
    async def buy_premium(self, ctx):
        embed = discord.Embed(
            title="🌟 Nova Server Premium",
            description="নিচের কিউআর কোডটি স্ক্যান করে পেমেন্ট করুন। প্রতি মাস (৩০ দিন) = **১০০ টাকা**।",
            color=discord.Color.gold()
        )
        embed.add_field(name="💳 মূল্য তালিকা", value="• ১ মাস: ১০০ টাকা\n• ৩ মাস: ৩০০ টাকা\n• ৬ মাস: ৬০০ টাকা\n• ১ বছর: ১২০০ টাকা", inline=False)
        embed.add_field(name="📝 কেনার নিয়ম", value="১. কিউআর স্ক্যান করে পে করুন।\n২. ট্রানজ্যাকশন আইডি সংগ্রহ করুন।\n৩. `/submit_premium` কমান্ড ব্যবহার করে রিকোয়েস্ট পাঠান।", inline=False)
        embed.set_image(url=self.qr_link)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="submit_premium", description="পেমেন্ট ট্রানজ্যাকশন আইডি সাবমিট করুন।")
    @app_commands.describe(months="আপনি কত মাসের জন্য নিতে চান?", tx_id="আপনার পেমেন্ট ট্রানজ্যাকশন আইডি")
    async def submit_premium(self, ctx, months: int, tx_id: str):
        if months < 1:
            return await ctx.send("কমপক্ষে ১ মাসের জন্য নিতে হবে।", ephemeral=True)
        
        # সরাসরি আইডি ব্যবহার করে ফেচ করা
        admin = await self.bot.fetch_user(self.admin_user_id)
        
        embed = discord.Embed(title="🚀 New Premium Request", color=discord.Color.blue())
        embed.add_field(name="Server", value=f"{ctx.guild.name} ({ctx.guild.id})", inline=False)
        embed.add_field(name="Requester", value=ctx.author.mention, inline=True)
        embed.add_field(name="Plan", value=f"{months} Month(s)", inline=True)
        embed.add_field(name="TX ID", value=f"`{tx_id}`", inline=False)
        
        view = PremiumApprovalView(self.bot, ctx.guild.id, months, ctx.author.id)
        await admin.send(embed=embed, view=view)
        await ctx.send("✅ আপনার রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে। অ্যাপ্রুভ হলে আপনাকে জানিয়ে দেওয়া হবে।")

class PremiumApprovalView(discord.ui.View):
    def __init__(self, bot, guild_id, months, requester_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.months = months
        self.requester_id = requester_id

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        expiry = datetime.utcnow() + timedelta(days=30 * self.months)
        await self.bot.db.server_premium.update_one(
            {"guild_id": self.guild_id},
            {"$set": {"expiry": expiry, "is_premium": True}},
            upsert=True
        )
        
        try:
            user = await self.bot.fetch_user(self.requester_id)
            await user.send(f"🎉 অভিনন্দন! আপনার সার্ভার (ID: {self.guild_id}) এখন **{self.months}** মাসের জন্য প্রিমিয়াম।")
        except: pass
        
        await interaction.response.send_message(f"✅ Approved for Server {self.guild_id}", ephemeral=True)
        self.stop()

async def setup(bot):
    await bot.add_cog(ServerPremium(bot))
