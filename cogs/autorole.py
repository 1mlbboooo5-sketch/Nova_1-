import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timezone

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ১. মেম্বার জয়েন হলে রোল দেওয়ার লজিক
    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.process_auto_role(member)

    # ২. মেসেজ পাঠালে বয়স চেক করে অটো-রোল আপডেট করা (অ্যাডভান্সড ফিচার)
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        # ইউজারের মেসেজ পাঠানোর সময় মেম্বার অবজেক্ট দিয়ে চেক করা
        await self.process_auto_role(message.author)

    # ৩. মেইন প্রসেসিং ফাংশন (যাতে জয়েন এবং মেসেজ দুই জায়গাতেই কাজ করে)
    async def process_auto_role(self, member):
        guild = member.guild
        data = await self.bot.db.guild_settings.find_one({"guild_id": guild.id})
        if not data: return

        # --- নরমাল অটো-রোল ---
        if data.get("normal_status", False):
            normal_role_id = data.get("normal_role")
            if normal_role_id:
                role = guild.get_role(normal_role_id)
                if role and guild.me.top_role > role and role not in member.roles:
                    try: await member.add_roles(role)
                    except: pass

        # --- প্রিমিয়াম এজ-রোল (আপডেট লজিক সহ) ---
        premium_data = await self.bot.db.premium_users.find_one({"user_id": guild.owner_id})
        if premium_data and data.get("premium_status", False):
            now = datetime.now(timezone.utc)
            years = (now - member.created_at).days // 365
            
            if years > 0:
                # কাস্টম নাম আছে কি না চেক করা
                custom_names = data.get("custom_names", {})
                role_name = custom_names.get(str(years), f"{years} Year Old")
                
                # কালার লজিক
                colors = {1: 0x95a5a6, 2: 0xf1c40f, 3: 0x1abc9c, 4: 0xe91e63, 5: 0xff0000}
                selected_color = colors.get(years, 0xff0000)

                # চেক করা: ইউজারের কি অলরেডি সঠিক রোলটি আছে?
                has_current_role = any(r.name == role_name for r in member.roles)
                
                if not has_current_role:
                    # পুরানো এজ-রোলগুলো রিমুভ করা
                    old_age_roles = [r for r in member.roles if "Year Old" in r.name or "Year Legend" in r.name or r.name in custom_names.values()]
                    if old_age_roles:
                        try: await member.remove_roles(*old_age_roles)
                        except: pass

                    # নতুন রোল খোঁজা বা ক্রিয়েট করা
                    age_role = discord.utils.get(guild.roles, name=role_name)
                    if not age_role:
                        try:
                            age_role = await guild.create_role(name=role_name, color=discord.Color(selected_color), hoist=True)
                        except: pass
                    
                    if age_role and guild.me.top_role > age_role:
                        try: await member.add_roles(age_role)
                        except: pass

    # ৪. হাইব্রিড কমান্ড: প্যানেল ওপেন করা
    @commands.hybrid_command(name="autorole", description="Open the advanced auto-role configuration panel.")
    @commands.has_permissions(administrator=True)
    async def autorole(self, ctx):
        embed = discord.Embed(
            title="🛠️ Advanced Auto-Role Panel",
            description="Configure your server's join and age-based role settings below.\n\n"
                        "• **Normal:** Standard role for everyone.\n"
                        "• **Premium:** Dynamic roles based on account age.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        view = AutoRolePanelView(self.bot, ctx.guild.id)
        await ctx.send(embed=embed, view=view)

# --- ইন্টারফেস প্যানেল ভিউ (বাটন এবং ড্রপডাউন) ---
class AutoRolePanelView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    @discord.ui.button(label="Normal Toggle", style=discord.ButtonStyle.secondary, emoji="👥")
    async def normal_toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = await self.bot.db.guild_settings.find_one({"guild_id": self.guild_id})
        current = data.get("normal_status", False) if data else False
        await self.bot.db.guild_settings.update_one(
            {"guild_id": self.guild_id}, {"$set": {"normal_status": not current}}, upsert=True
        )
        status = "Enabled" if not current else "Disabled"
        await interaction.response.send_message(f"Normal Auto-Role is now **{status}**.", ephemeral=True)

    @discord.ui.button(label="Premium Toggle", style=discord.ButtonStyle.primary, emoji="🌟")
    async def premium_toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        # এখানে প্রিমিয়াম চেক লজিক থাকবে
        await interaction.response.send_message("Premium Age-Role system toggled! (Ensure server owner is premium)", ephemeral=True)
        # ডাটাবেজ আপডেট লজিক... (একই ভাবে normal_toggle এর মতো)

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
          
