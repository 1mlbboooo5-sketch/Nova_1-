import discord
from discord.ext import commands
from discord import ui, app_commands
from datetime import datetime, timedelta
import config 

class PremiumSubmissionModal(ui.Modal, title='Submit Payment Details'):
    months = ui.TextInput(label='Duration (Months)', placeholder='Enter number of months (e.g. 1, 3, 12)', min_length=1, max_length=2)
    tx_id = ui.TextInput(label='Transaction ID', placeholder='Enter your payment TX ID here...', min_length=5)

    def __init__(self, bot, guild_id):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            month_count = int(self.months.value)
            admin = await self.bot.fetch_user(config.ADMIN_ID)
            
            embed = discord.Embed(title="🚀 New Premium Request", color=discord.Color.blue())
            embed.add_field(name="Server", value=f"{interaction.guild.name} ({self.guild_id})", inline=False)
            embed.add_field(name="Requester", value=interaction.user.mention, inline=True)
            embed.add_field(name="Plan", value=f"{month_count} Month(s)", inline=True)
            embed.add_field(name="TX ID", value=f"`{self.tx_id.value}`", inline=False)
            
            view = PremiumApprovalView(self.bot, self.guild_id, month_count, interaction.user.id)
            await admin.send(embed=embed, view=view)
            await interaction.response.send_message("✅ Your request has been sent to the Admin! You will be notified via DM.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number for months.", ephemeral=True)

class PremiumApprovalView(ui.View):
    def __init__(self, bot, guild_id, months, requester_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.months = months
        self.requester_id = requester_id

    @ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        expiry = datetime.utcnow() + timedelta(days=30 * self.months)
        await self.bot.db.server_premium.update_one(
            {"guild_id": self.guild_id},
            {"$set": {"expiry": expiry, "is_premium": True}},
            upsert=True
        )
        try:
            user = await self.bot.fetch_user(self.requester_id)
            await user.send(f"🎉 Congratulations! Your server (ID: {self.guild_id}) is now **Premium** for **{self.months}** month(s).")
        except: pass
        await interaction.response.send_message(f"✅ Approved for Server {self.guild_id}", ephemeral=True)
        self.stop()

class BuyPremiumView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @ui.button(label="Submit TX ID", style=discord.ButtonStyle.primary, emoji="📝")
    async def submit_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(PremiumSubmissionModal(self.bot, interaction.guild.id))

class ServerPremium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.qr_link = "https://cdn.discordapp.com/attachments/1465014056090996836/1501256569256673351/GooglePay_QR_1.png?ex=69fb69a2&is=69fa1822&hm=c8471ff9bc3e5e1c056209140c26911e2590655b8c1ac58022999f7b6ee62653&"

    @commands.hybrid_command(name="buy_premium", description="View premium plans and payment QR code.")
    async def buy_premium(self, ctx):
        embed = discord.Embed(
            title="🌟 Nova Server Premium Plans",
            description="Scan the QR code to pay. **1 Month (30 Days) = 100 BDT**.",
            color=discord.Color.gold()
        )
        embed.add_field(name="💳 Pricing", value="• 1 Month: 100 BDT\n• 3 Months: 300 BDT\n• 6 Months: 600 BDT\n• 1 Year: 1200 BDT", inline=False)
        embed.add_field(name="📝 How to Activate?", value="1. Scan the QR and complete payment.\n2. Click the **Submit TX ID** button below.\n3. Wait for Admin approval.", inline=False)
        embed.set_image(url=self.qr_link)
        await ctx.send(embed=embed, view=BuyPremiumView(self.bot))

async def setup(bot):
    await bot.add_cog(ServerPremium(bot))
    
