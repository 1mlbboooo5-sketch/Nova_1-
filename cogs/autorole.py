import discord
from discord.ext import commands
from discord import ui, app_commands
from datetime import datetime, timezone

class CustomNameModal(ui.Modal, title="Custom Age-Role Names"):
    year1 = ui.TextInput(label="1 Year Old Role Name", placeholder="Example: Legend", required=False)
    year2 = ui.TextInput(label="2 Years Old Role Name", placeholder="Example: Mythic", required=False)
    year3 = ui.TextInput(label="3 Years Old Role Name", placeholder="Example: Immortal", required=False)

    def __init__(self, bot, guild_id):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        names = {}
        if self.year1.value: names["1"] = self.year1.value
        if self.year2.value: names["2"] = self.year2.value
        if self.year3.value: names["3"] = self.year3.value

        await self.bot.db.guild_settings.update_one(
            {"guild_id": self.guild_id},
            {"$set": {"custom_names": names}},
            upsert=True
        )
        await interaction.response.send_message("✅ Custom names updated successfully!", ephemeral=True)

class AutoRolePanelView(ui.View):
    def __init__(self, bot, guild):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild = guild

    # --- Normal Auto-Role Section ---
    @ui.button(label="Toggle Normal", style=discord.ButtonStyle.secondary, emoji="👤", row=0)
    async def toggle_normal(self, interaction: discord.Interaction, button: ui.Button):
        data = await self.bot.db.guild_settings.find_one({"guild_id": self.guild.id})
        current = data.get("normal_on", False) if data else False
        await self.bot.db.guild_settings.update_one(
            {"guild_id": self.guild.id}, {"$set": {"normal_on": not current}}, upsert=True
        )
        await interaction.response.send_message(f"Normal Auto-Role is now **{'Enabled' if not current else 'Disabled'}**", ephemeral=True)

    @ui.select(cls=ui.RoleSelect, placeholder="Select Normal Role (Low Level)", row=1)
    async def role_select(self, interaction: discord.Interaction, select: ui.RoleSelect):
        role = select.values[0]
        if interaction.guild.me.top_role <= role:
            return await interaction.response.send_message("❌ This role is higher than the bot's position!", ephemeral=True)
        
        await self.bot.db.guild_settings.update_one(
            {"guild_id": self.guild.id}, {"$set": {"normal_role": role.id}}, upsert=True
        )
        await interaction.response.send_message(f"✅ Normal Role set to: **{role.name}**", ephemeral=True)

    # --- Premium Age-Role Section ---
    @ui.button(label="Toggle Premium", style=discord.ButtonStyle.primary, emoji="🌟", row=2)
    async def toggle_premium(self, interaction: discord.Interaction, button: ui.Button):
        premium = await self.bot.db.server_premium.find_one({"guild_id": self.guild.id})
        if not premium or premium.get("expiry") < datetime.utcnow():
            return await interaction.response.send_message("❌ Premium is not active. Use `/buy_premium`.", ephemeral=True)

        data = await self.bot.db.guild_settings.find_one({"guild_id": self.guild.id})
        current = data.get("premium_on", False) if data else False
        await self.bot.db.guild_settings.update_one(
            {"guild_id": self.guild.id}, {"$set": {"premium_on": not current}}, upsert=True
        )
        await interaction.response.send_message(f"Premium Age-Role is now **{'Enabled' if not current else 'Disabled'}**", ephemeral=True)

    @ui.button(label="Set Custom Names", style=discord.ButtonStyle.success, emoji="✏️", row=3)
    async def set_names(self, interaction: discord.Interaction, button: ui.Button):
        premium = await self.bot.db.server_premium.find_one({"guild_id": self.guild.id})
        if not premium or premium.get("expiry") < datetime.utcnow():
            return await interaction.response.send_message("❌ Custom names are a Premium feature!", ephemeral=True)
        
        await interaction.response.send_modal(CustomNameModal(self.bot, self.guild.id))

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_and_assign_roles(self, member):
        if member.bot or not member.guild: return
        guild = member.guild
        data = await self.bot.db.guild_settings.find_one({"guild_id": guild.id})
        if not data: return

        # 1. Normal Role
        if data.get("normal_on", False):
            role_id = data.get("normal_role")
            role = guild.get_role(role_id)
            if role and guild.me.top_role > role and role not in member.roles:
                try: await member.add_roles(role)
                except: pass

        # 2. Premium Age Role
        premium = await self.bot.db.server_premium.find_one({"guild_id": guild.id})
        if premium and premium.get("expiry") > datetime.utcnow() and data.get("premium_on", False):
            years = (datetime.now(timezone.utc) - member.created_at).days // 365
            if years > 0:
                custom_names = data.get("custom_names", {})
                role_name = custom_names.get(str(years), f"{years} Year Old")
                colors = {1: 0xbdc3c7, 2: 0xf1c40f, 3: 0x1abc9c, 4: 0x9b59b6, 5: 0xe74c3c}
                color = colors.get(years, 0xe74c3c)

                if not any(r.name == role_name for r in member.roles):
                    # Cleanup old age roles
                    old_roles = [r for r in member.roles if "Year Old" in r.name or r.name in custom_names.values()]
                    if old_roles: await member.remove_roles(*old_roles)

                    age_role = discord.utils.get(guild.roles, name=role_name)
                    if not age_role:
                        age_role = await guild.create_role(name=role_name, color=discord.Color(color), hoist=True)
                    
                    if guild.me.top_role > age_role: await member.add_roles(age_role)

    @commands.Cog.listener()
    async def on_member_join(self, member): await self.check_and_assign_roles(member)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild: await self.check_and_assign_roles(message.author)

    @commands.hybrid_command(name="autorole", description="Open the professional Auto-Role configuration panel.")
    @commands.has_permissions(administrator=True)
    async def autorole(self, ctx):
        embed = discord.Embed(
            title="💎 Nova Advanced Auto-Role Control",
            description="Manage your server's role automation settings.\n\n"
                        "🔵 **Normal Section:** Basic join roles.\n"
                        "🌟 **Premium Section:** Age-based roles & customization.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed, view=AutoRolePanelView(self.bot, ctx.guild))

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
                            
