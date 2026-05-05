import discord
from discord.ext import commands
from discord import ui, app_commands
from datetime import datetime, timezone

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_and_assign_roles(self, member):
        if member.bot or not member.guild: return
        guild = member.guild
        
        data = await self.bot.db.guild_settings.find_one({"guild_id": guild.id})
        if not data: return

        # ১. নরমাল অটো-রোল
        if data.get("normal_on", False):
            role_id = data.get("normal_role")
            role = guild.get_role(role_id)
            if role and guild.me.top_role > role and role not in member.roles:
                try: await member.add_roles(role)
                except: pass

        # ২. প্রিমিয়াম এজ-রোল (Live Tracking)
        premium = await self.bot.db.server_premium.find_one({"guild_id": guild.id})
        if premium and premium.get("expiry") > datetime.utcnow() and data.get("premium_on", False):
            now = datetime.now(timezone.utc)
            years = (now - member.created_at).days // 365
            
            if years > 0:
                custom_names = data.get("custom_names", {})
                role_name = custom_names.get(str(years), f"{years} Year Old")
                
                colors = {1: 0xbdc3c7, 2: 0xf1c40f, 3: 0x1abc9c, 4: 0x9b59b6, 5: 0xe74c3c}
                selected_color = colors.get(years, 0xe74c3c)

                # বর্তমান রোল চেক
                has_role = any(r.name == role_name for r in member.roles)
                if not has_role:
                    # পুরনো বছরগুলোর রোল সরানো
                    old_age_roles = [r for r in member.roles if "Year Old" in r.name or r.name in custom_names.values()]
                    if old_age_roles:
                        try: await member.remove_roles(*old_age_roles)
                        except: pass

                    # নতুন রোল তৈরি/দেওয়া
                    age_role = discord.utils.get(guild.roles, name=role_name)
                    if not age_role:
                        try:
                            age_role = await guild.create_role(name=role_name, color=discord.Color(selected_color), hoist=True)
                        except: pass
                    
                    if age_role and guild.me.top_role > age_role:
                        try: await member.add_roles(age_role)
                        except: pass

    @commands.Cog.listener()
    async def on_member_join(self, member): await self.check_and_assign_roles(member)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild: await self.check_and_assign_roles(message.author)

    @commands.hybrid_command(name="autorole", description="অ্যাডভান্সড অটো-রোল সেটআপ প্যানেল খুলুন।")
    @commands.has_permissions(administrator=True)
    async def autorole(self, ctx):
        embed = discord.Embed(
            title="💎 Nova Advanced Auto-Role Control",
            description="আপনার সার্ভারের রোল অটোমেশন এখান থেকে কন্ট্রোল করুন।\n\n"
                        "• **Normal:** নতুনদের জন্য ডিফল্ট রোল।\n"
                        "• **Premium:** একাউন্টের বয়স অনুযায়ী অটো-আপডেট রোল।",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        view = AutoRolePanelView(self.bot, ctx.guild)
        await ctx.send(embed=embed, view=view)

class AutoRolePanelView(ui.View):
    def __init__(self, bot, guild):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild = guild

    @ui.select(cls=ui.RoleSelect, placeholder="নরমাল অটো-রোল সিলেক্ট করুন (Low Level)...")
    async def role_select(self, interaction: discord.Interaction, select: ui.RoleSelect):
        role = select.values[0]
        if interaction.guild.me.top_role <= role:
            return await interaction.response.send_message("❌ বটের রোলের উপরের কোনো রোল সেট করা সম্ভব নয়!", ephemeral=True)
        
        await self.bot.db.guild_settings.update_one(
            {"guild_id": self.guild.id}, 
            {"$set": {"normal_role": role.id, "normal_on": True}}, 
            upsert=True
        )
        await interaction.response.send_message(f"✅ Normal Auto-Role সেট করা হয়েছে: **{role.name}**", ephemeral=True)

    @ui.button(label="Premium Age-Role (On/Off)", style=discord.ButtonStyle.primary, emoji="🌟")
    async def toggle_premium(self, interaction: discord.Interaction, button: ui.Button):
        # সার্ভার প্রিমিয়াম চেক
        premium = await self.bot.db.server_premium.find_one({"guild_id": self.guild.id})
        if not premium or premium.get("expiry") < datetime.utcnow():
            return await interaction.response.send_message("❌ এই সার্ভারে প্রিমিয়াম অ্যাক্টিভ নেই। `/buy_premium` দেখুন।", ephemeral=True)

        data = await self.bot.db.guild_settings.find_one({"guild_id": self.guild.id})
        current = data.get("premium_on", False) if data else False
        await self.bot.db.guild_settings.update_one(
            {"guild_id": self.guild.id}, {"$set": {"premium_on": not current}}, upsert=True
        )
        await interaction.response.send_message(f"Premium Age-Role এখন: **{'Enabled' if not current else 'Disabled'}**", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
