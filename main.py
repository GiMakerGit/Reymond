# ©2025 GiMaker Software inc.
# ©2025 Alogical Std. as a mother company

import sys
sys.path.append('lib')
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import json

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

guild_settings = {}
admin_roles = {} 

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!Rey_', intents=intents, help_command=None)

def load_ratings():
    ratings = {}
    if not os.path.exists('ratings'):
        os.makedirs('ratings')
    return ratings

def save_ratings(guild_id, guild_ratings):
    with open(f'ratings/{guild_id}_ratings.json', 'w') as f:
        json.dump(guild_ratings, f)

def load_guild_ratings(guild_id):
    try:
        with open(f'ratings/{guild_id}_ratings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

ratings = load_ratings() 
RATED_ROLE_ID = 1182638660030570496  

@bot.tree.command(name="echo", description="Repeats what you say")
async def echo(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("Message sent!", ephemeral=True)
    await interaction.channel.send(message)

@bot.event
async def on_ready():
    if not os.path.exists('ratings'):
        os.makedirs('ratings')
        
    for guild in bot.guilds:
        if guild.id in guild_settings:
            role = guild.get_role(guild_settings[guild.id])
            if role:
                guild_ratings = load_guild_ratings(guild.id)
                for member in role.members:
                    if str(member.id) not in guild_ratings:
                        guild_ratings[str(member.id)] = 0
                save_ratings(guild.id, guild_ratings)
    
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print('------')

@bot.tree.command(name="setuprating", description="Set up the rating system role")
async def setuprating(interaction: discord.Interaction, role: discord.Role):
    guild_settings[interaction.guild_id] = role.id
    await interaction.response.send_message(f"Rating system set up for role: {role.name}")
    
    guild_ratings = load_guild_ratings(interaction.guild_id)
    for member in role.members:
        if str(member.id) not in guild_ratings:
            guild_ratings[str(member.id)] = 0
    save_ratings(interaction.guild_id, guild_ratings)

@bot.tree.command(name="addrating", description="Add rating points to a user")
async def addrating(interaction: discord.Interaction, user: discord.Member, amount: int):

    if interaction.guild_id not in admin_roles:
        await interaction.response.send_message("Admin role not set up! Ask an administrator to use /setupadmin first.", ephemeral=True)
        return
    

    admin_role = interaction.guild.get_role(admin_roles[interaction.guild_id])
    if admin_role not in interaction.user.roles:
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return

    if interaction.guild_id not in guild_settings:
        await interaction.response.send_message("Rating system not set up! Use /setuprating first.", ephemeral=True)
        return
        
    role = interaction.guild.get_role(guild_settings[interaction.guild_id])
    if role not in user.roles:
        await interaction.response.send_message(f"{user.name} doesn't have the required role!", ephemeral=True)
        return
    
    guild_ratings = load_guild_ratings(interaction.guild_id)
    if str(user.id) not in guild_ratings:
        guild_ratings[str(user.id)] = 0
    
    guild_ratings[str(user.id)] += amount
    save_ratings(interaction.guild_id, guild_ratings)
    
    await interaction.response.send_message(
        f"✨ Added {amount} points to {user.name}'s rating. New rating: {guild_ratings[str(user.id)]}"
    )

@bot.tree.command(name="rmrating", description="Remove rating points from a user")
async def rmrating(interaction: discord.Interaction, user: discord.Member, amount: int):

    if interaction.guild_id not in admin_roles:
        await interaction.response.send_message("Admin role not set up! Ask an administrator to use /setupadmin first.", ephemeral=True)
        return
    
    admin_role = interaction.guild.get_role(admin_roles[interaction.guild_id])
    if admin_role not in interaction.user.roles:
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return

    if interaction.guild_id not in guild_settings:
        await interaction.response.send_message("Rating system not set up! Use /setuprating first.", ephemeral=True)
        return
        
    role = interaction.guild.get_role(guild_settings[interaction.guild_id])
    if role not in user.roles:
        await interaction.response.send_message(f"{user.name} doesn't have the required role!", ephemeral=True)
        return
    
    guild_ratings = load_guild_ratings(interaction.guild_id)
    if str(user.id) not in guild_ratings:
        guild_ratings[str(user.id)] = 0
    
    guild_ratings[str(user.id)] -= amount
    save_ratings(interaction.guild_id, guild_ratings)
    
    await interaction.response.send_message(
        f"📉 Removed {amount} points from {user.name}'s rating. New rating: {guild_ratings[str(user.id)]}"
    )

@bot.tree.command(name="rating", description="Check user's rating")
async def rating(interaction: discord.Interaction, user: discord.Member):
    guild_ratings = load_guild_ratings(interaction.guild_id)
    
    if str(user.id) not in guild_ratings:
        await interaction.response.send_message(f"{user.name} has no rating.")
        return
    
    embed = discord.Embed(
        title="📊 Rating Information",
        color=discord.Color.blue()
    )
    embed.add_field(name="User", value=user.mention, inline=True)
    embed.add_field(name="Rating", value=str(guild_ratings[str(user.id)]), inline=True)
    embed.set_thumbnail(url=user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setupadmin", description="Set up the role that can manage ratings")
@commands.has_permissions(administrator=True)
async def setupadmin(interaction: discord.Interaction, role: discord.Role):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only administrators can use this command!", ephemeral=True)
        return

    admin_roles[interaction.guild_id] = role.id
    await interaction.response.send_message(f"Rating management role set to: {role.name}")

bot.run(token, log_handler=handler, log_level=logging.INFO)