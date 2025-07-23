# ©2025 Alogical Std.
# Created by GiMaker

import sys
sys.path.append('lib')
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import json
from lang_config import LANGUAGES
import typing
import signal

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

guild_settings = {}
admin_roles = {} 
guild_languages = {}
DEFAULT_LANG = "en"
bank_roles = {}

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
    
    for filename in os.listdir('ratings'):
        if filename.endswith('_ratings.json'):
            guild_id = filename.split('_')[0]  
            try:
                with open(f'ratings/{filename}', 'r') as f:
                    ratings[guild_id] = json.load(f)
            except json.JSONDecodeError:
                print(f"Error loading ratings for guild {guild_id}")
                ratings[guild_id] = {}
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
    
    global ratings
    ratings = load_ratings()
    
    for guild in bot.guilds:
        guild_id_str = str(guild.id)
        
        if guild.id not in guild_settings:
            continue
            
        role = guild.get_role(guild_settings[guild.id])
        if not role:
            continue
            
        if guild_id_str not in ratings:
            ratings[guild_id_str] = {}
            
        guild_ratings = ratings[guild_id_str]
        
        for member in role.members:
            member_id = str(member.id)
            if member_id not in guild_ratings:
                guild_ratings[member_id] = 0
        
        save_ratings(guild.id, guild_ratings)
    
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')
    
    print(f'Loaded ratings for {len(ratings)} guilds')
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print('------')

@bot.tree.command(name="setuprating", description="Set up the rating system role")
async def setuprating(interaction: discord.Interaction, role: discord.Role):
    guild_settings[interaction.guild_id] = role.id
    save_settings() 
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
        await interaction.response.send_message(
            get_text(interaction.guild_id, "user_no_rating", user=user.name)
        )
        return
    
    embed = discord.Embed(
        title=get_text(interaction.guild_id, "rating_info_title"),
        color=discord.Color.blue()
    )
    embed.add_field(
        name=get_text(interaction.guild_id, "user_field", user=user.name), 
        value=user.mention, 
        inline=True
    )
    embed.add_field(
        name=get_text(interaction.guild_id, "rating_field"), 
        value=get_text(
            interaction.guild_id, 
            "rating_display", 
            rating=guild_ratings[str(user.id)]
        ), 
        inline=True
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

class PaginationView(discord.ui.View):
    def __init__(self, page, total_pages, guild_id):
        super().__init__(timeout=180)
        self.page = page
        self.total_pages = total_pages
        
        if page > 1:
            self.add_item(discord.ui.Button(
                label=get_text(guild_id, "prev_button"),
                custom_id=f"prev_{page}",
                style=discord.ButtonStyle.primary
            ))
        if page < total_pages:
            self.add_item(discord.ui.Button(
                label=get_text(guild_id, "next_button"),
                custom_id=f"next_{page}",
                style=discord.ButtonStyle.primary
            ))

@bot.tree.command(name="top", description="Shows top rated users (10 per page)")
async def top(interaction: discord.Interaction, page: int = 1):
    guild_ratings = load_guild_ratings(interaction.guild_id)
    
    if not guild_ratings:
        await interaction.response.send_message(get_text(interaction.guild_id, "no_ratings"))
        return
    
    sorted_ratings = sorted(guild_ratings.items(), key=lambda x: x[1], reverse=True)
    total_pages = (len(sorted_ratings) + 9) // 10  
    
    if page < 1 or page > total_pages:
        await interaction.response.send_message(
            get_text(interaction.guild_id, "invalid_page", total_pages=total_pages),
            ephemeral=True
        )
        return
    
    start_idx = (page - 1) * 10
    end_idx = start_idx + 10
    page_users = sorted_ratings[start_idx:end_idx]
    
    embed = discord.Embed(
        title=get_text(interaction.guild_id, "top_users_title"),
        description=get_text(interaction.guild_id, "page_display", current=page, total=total_pages),
        color=discord.Color.gold()
    )
    
    for i, (user_id, rating) in enumerate(page_users, start=start_idx + 1):
        user = interaction.guild.get_member(int(user_id))
        if user:
            embed.add_field(
                name=f"#{i}. {user.name}",
                value=get_text(interaction.guild_id, "rating_display", rating=rating),
                inline=False
            )
    
    view = PaginationView(page, total_pages, interaction.guild_id)
    await interaction.response.send_message(embed=embed, view=view)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or "custom_id" not in interaction.data:
        return

    custom_id = interaction.data["custom_id"]
    if custom_id.startswith(("prev_", "next_")):
        direction, current_page = custom_id.split("_")
        current_page = int(current_page)
        new_page = current_page - 1 if direction == "prev" else current_page + 1
        
        guild_ratings = load_guild_ratings(interaction.guild_id)
        sorted_ratings = sorted(guild_ratings.items(), key=lambda x: x[1], reverse=True)
        total_pages = (len(sorted_ratings) + 9) // 10
        
        start_idx = (new_page - 1) * 10
        end_idx = start_idx + 10
        page_users = sorted_ratings[start_idx:end_idx]
        
        embed = discord.Embed(
            title="🏆 Top Rated Users",
            description=f"Page {new_page}/{total_pages}",
            color=discord.Color.gold()
        )
        
        for i, (user_id, rating) in enumerate(page_users, start=start_idx + 1):
            user = interaction.guild.get_member(int(user_id))
            if user:
                embed.add_field(
                    name=f"#{i}. {user.name}",
                    value=f"Rating: {rating}",
                    inline=False
                )
        
        view = PaginationView(new_page, total_pages, interaction.guild_id)
        await interaction.response.edit_message(embed=embed, view=view)

@bot.tree.command(name="setupadmin", description="Set up the role that can manage ratings")
@commands.has_permissions(administrator=True)
async def setupadmin(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only administrators can use this command!", ephemeral=True)
        return

    admin_roles[interaction.guild_id] = role.id
    save_settings()  # <-- Save after change
    await interaction.response.send_message(f"Rating management role set to: {role.name}")

@bot.tree.command(name="setup", description="Set up the rating system and admin roles")
@commands.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction, rated_role: discord.Role, admin_role: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(get_text(interaction.guild_id, "no_permission"), ephemeral=True)
        return

    guild_settings[interaction.guild_id] = rated_role.id
    admin_roles[interaction.guild_id] = admin_role.id
    save_settings()  # <-- Save after change
    
    guild_ratings = load_guild_ratings(interaction.guild_id)
    for member in rated_role.members:
        if str(member.id) not in guild_ratings:
            guild_ratings[str(member.id)] = 0
    save_ratings(interaction.guild_id, guild_ratings)

    embed = discord.Embed(
        title="⚙️ Rating System Setup",
        description="System configuration has been updated",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="📊 Rated Role",
        value=f"{rated_role.mention}\nMembers with this role can receive ratings",
        inline=False
    )
    
    embed.add_field(
        name="👑 Admin Role",
        value=f"{admin_role.mention}\nMembers with this role can manage ratings",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Status",
        value="✅ Setup completed successfully\n📝 Initial ratings have been initialized",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)



@bot.tree.command(name="rank_setuprating", description="Set up the rating system role")
async def rank_setuprating(interaction: discord.Interaction, role: discord.Role):
    guild_settings[interaction.guild_id] = role.id
    save_settings() 
    await interaction.response.send_message(f"Rating system set up for role: {role.name}")
    
    guild_ratings = load_guild_ratings(interaction.guild_id)
    for member in role.members:
        if str(member.id) not in guild_ratings:
            guild_ratings[str(member.id)] = 0
    save_ratings(interaction.guild_id, guild_ratings)

@bot.tree.command(name="rank_addrating", description="Add rating points to a user")
async def rank_addrating(interaction: discord.Interaction, user: discord.Member, amount: int):
    if interaction.guild_id not in admin_roles:
        await interaction.response.send_message("Admin role not set up! Ask an administrator to use /rank_setupadmin first.", ephemeral=True)
        return

    admin_role = interaction.guild.get_role(admin_roles[interaction.guild_id])
    if admin_role not in interaction.user.roles:
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return

    if interaction.guild_id not in guild_settings:
        await interaction.response.send_message("Rating system not set up! Use /rank_setuprating first.", ephemeral=True)
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

@bot.tree.command(name="rank_rmrating", description="Remove rating points from a user")
async def rank_rmrating(interaction: discord.Interaction, user: discord.Member, amount: int):
    if interaction.guild_id not in admin_roles:
        await interaction.response.send_message("Admin role not set up! Ask an administrator to use /rank_setupadmin first.", ephemeral=True)
        return
    
    admin_role = interaction.guild.get_role(admin_roles[interaction.guild_id])
    if admin_role not in interaction.user.roles:
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return

    if interaction.guild_id not in guild_settings:
        await interaction.response.send_message("Rating system not set up! Use /rank_setuprating first.", ephemeral=True)
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

@bot.tree.command(name="rank_rating", description="Check user's rating")
async def rank_rating(interaction: discord.Interaction, user: discord.Member):
    guild_ratings = load_guild_ratings(interaction.guild_id)
    
    if str(user.id) not in guild_ratings:
        await interaction.response.send_message(
            get_text(interaction.guild_id, "user_no_rating", user=user.name)
        )
        return
    
    embed = discord.Embed(
        title=get_text(interaction.guild_id, "rating_info_title"),
        color=discord.Color.blue()
    )
    embed.add_field(
        name=get_text(interaction.guild_id, "user_field", user=user.name), 
        value=user.mention, 
        inline=True
    )
    embed.add_field(
        name=get_text(interaction.guild_id, "rating_field"), 
        value=get_text(
            interaction.guild_id, 
            "rating_display", 
            rating=guild_ratings[str(user.id)]
        ), 
        inline=True
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rank_top", description="Shows top rated users (10 per page)")
async def rank_top(interaction: discord.Interaction, page: int = 1):
    guild_ratings = load_guild_ratings(interaction.guild_id)
    
    if not guild_ratings:
        await interaction.response.send_message(get_text(interaction.guild_id, "no_ratings"))
        return
    
    sorted_ratings = sorted(guild_ratings.items(), key=lambda x: x[1], reverse=True)
    total_pages = (len(sorted_ratings) + 9) // 10  
    
    if page < 1 or page > total_pages:
        await interaction.response.send_message(
            get_text(interaction.guild_id, "invalid_page", total_pages=total_pages),
            ephemeral=True
        )
        return
    
    start_idx = (page - 1) * 10
    end_idx = start_idx + 10
    page_users = sorted_ratings[start_idx:end_idx]
    
    embed = discord.Embed(
        title=get_text(interaction.guild_id, "top_users_title"),
        description=get_text(interaction.guild_id, "page_display", current=page, total=total_pages),
        color=discord.Color.gold()
    )
    
    for i, (user_id, rating) in enumerate(page_users, start=start_idx + 1):
        user = interaction.guild.get_member(int(user_id))
        if user:
            embed.add_field(
                name=f"#{i}. {user.name}",
                value=get_text(interaction.guild_id, "rating_display", rating=rating),
                inline=False
            )
    
    view = PaginationView(page, total_pages, interaction.guild_id)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="rank_setupadmin", description="Set up the role that can manage ratings")
@commands.has_permissions(administrator=True)
async def rank_setupadmin(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only administrators can use this command!", ephemeral=True)
        return

    admin_roles[interaction.guild_id] = role.id
    save_settings()  # <-- Save after change
    await interaction.response.send_message(f"Rating management role set to: {role.name}")

@bot.tree.command(name="rank_setup", description="Set up the rating system and admin roles")
@commands.has_permissions(administrator=True)
async def rank_setup(interaction: discord.Interaction, rated_role: discord.Role, admin_role: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(get_text(interaction.guild_id, "no_permission"), ephemeral=True)
        return

    guild_settings[interaction.guild_id] = rated_role.id
    admin_roles[interaction.guild_id] = admin_role.id
    save_settings()  # <-- Save after change
    
    guild_ratings = load_guild_ratings(interaction.guild_id)
    for member in rated_role.members:
        if str(member.id) not in guild_ratings:
            guild_ratings[str(member.id)] = 0
    save_ratings(interaction.guild_id, guild_ratings)

    embed = discord.Embed(
        title="⚙️ Rating System Setup",
        description="System configuration has been updated",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="📊 Rated Role",
        value=f"{rated_role.mention}\nMembers with this role can receive ratings",
        inline=False
    )
    
    embed.add_field(
        name="👑 Admin Role",
        value=f"{admin_role.mention}\nMembers with this role can manage ratings",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Status",
        value="✅ Setup completed successfully\n📝 Initial ratings have been initialized",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

def load_language_settings():
    """Load language settings from file"""
    if not os.path.exists('config'):
        os.makedirs('config')
    try:
        with open('config/language_settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_language_settings(settings):
    """Save language settings to file"""
    if not os.path.exists('config'):
        os.makedirs('config')
    with open('config/language_settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

def get_text(guild_id, key, **kwargs):
    """Get translated text for given key and guild"""
    lang = guild_languages.get(str(guild_id), DEFAULT_LANG)
    
    if lang not in LANGUAGES or key not in LANGUAGES[lang]:
        text = LANGUAGES["en"].get(key, f"Missing translation: {key}")
    else:
        text = LANGUAGES[lang][key]
    
    return text.format(**kwargs) if kwargs else text

@bot.tree.command(name="setlang", description="Set the bot language (en/ru)")
@commands.has_permissions(administrator=True)
async def setlang(interaction: discord.Interaction, lang: str):
    if lang not in LANGUAGES:
        supported_langs = ", ".join(LANGUAGES.keys())
        await interaction.response.send_message(
            f"Unsupported language. Available languages: {supported_langs}",
            ephemeral=True
        )
        return

    guild_languages[str(interaction.guild_id)] = lang
    
    save_settings()
    
    embed = discord.Embed(
        title=get_text(interaction.guild_id, "language_title"),
        description=get_text(interaction.guild_id, "language_description"),
        color=discord.Color.green()
    )
    
    flag = "🇬🇧" if lang == "en" else "🇷🇺"
    language_name = "English" if lang == "en" else "Русский"
    
    embed.add_field(
        name=get_text(interaction.guild_id, "language_updated"),
        value=f"{flag} {language_name}",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

def load_settings():
    """Load all settings from files"""
    if not os.path.exists('config'):
        os.makedirs('config')
    
    try:
        with open('config/settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return {
                'guild_settings': settings.get('guild_settings', {}),
                'admin_roles': settings.get('admin_roles', {}),
                'guild_languages': settings.get('guild_languages', {})
            }
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'guild_settings': {},
            'admin_roles': {},
            'guild_languages': {}
        }

def save_settings():
    """Save all settings to file"""
    if not os.path.exists('config'):
        os.makedirs('config')
    
    settings = {
        'guild_settings': guild_settings,
        'admin_roles': admin_roles,
        'guild_languages': guild_languages
    }
    
    with open('config/settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

def load_bank():
    if not os.path.exists('bank'):
        os.makedirs('bank')
    try:
        with open('bank/bank.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_bank(data):
    if not os.path.exists('bank'):
        os.makedirs('bank')
    with open('bank/bank.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

BANKER_ROLE_NAME = "🤑 Банкир"
CITIZEN_ROLE_NAME = "🎭 Горожанин"

def get_card_by_nickname(bank, nickname):
    for card, info in bank.items():
        if info["nickname"].lower() == nickname.lower():
            return card, info
    return None, None

def get_card_by_userid(bank, user_id):
    for card, info in bank.items():
        if info["user_id"] == str(user_id):
            return card, info
    return None, None

@bot.tree.command(name="bank_createcard", description="Create a bank card (for citizens)")
async def bank_createcard(interaction: discord.Interaction, nickname: str):
    citizen_role = get_citizen_role(interaction.guild)
    if not citizen_role or citizen_role not in interaction.user.roles:
        embed = discord.Embed(
            description="You must have the citizen role to create a card.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    bank = load_bank()
    card, _ = get_card_by_userid(bank, interaction.user.id)
    if card:
        embed = discord.Embed(
            description=f"You already have a card: {card}",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    card_number = str(100000 + len(bank))
    bank[card_number] = {
        "user_id": str(interaction.user.id),
        "nickname": nickname,
        "balance": 0,
        "blocked": False
    }
    save_bank(bank)
    embed = discord.Embed(
        title="Card Created!",
        description=f"Your card number: `{card_number}`",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="bank_mycard", description="Find out your card number")
async def bank_mycard(interaction: discord.Interaction):
    bank = load_bank()
    card, info = get_card_by_userid(bank, interaction.user.id)
    if card:
        embed = discord.Embed(
            title="Your Card",
            color=discord.Color.blue()
        )
        embed.add_field(name="Card Number", value=f"`{card}`", inline=False)
        embed.add_field(name="Nickname", value=info['nickname'], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            description="You don't have a card yet. Use `/bank_createcard` to get one.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="bank_balance", description="View balance (by card number or nickname)")
async def bank_balance(interaction: discord.Interaction, card_or_nickname: str = None):
    bank = load_bank()
    if not card_or_nickname:
        card, info = get_card_by_userid(bank, interaction.user.id)
    else:
        card, info = bank.get(card_or_nickname), bank.get(card_or_nickname)
        if not info:
            card, info = get_card_by_nickname(bank, card_or_nickname)
    if info:
        if info["blocked"]:
            embed = discord.Embed(
                description="This account is blocked.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="Account Balance",
                color=discord.Color.gold()
            )
            embed.add_field(name="Card Number", value=f"`{card}`", inline=True)
            embed.add_field(name="Balance", value=f"{info['balance']}", inline=True)
            embed.add_field(name="Nickname", value=info['nickname'], inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            description="Card not found.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="bank_transfer", description="Transfer money to another card/nickname")
async def bank_transfer(interaction: discord.Interaction, amount: int, to_card_or_nickname: str, message: str = ""):
    bank = load_bank()
    from_card, from_info = get_card_by_userid(bank, interaction.user.id)
    if not from_info:
        embed = discord.Embed(
            description="You don't have a card.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if from_info["blocked"]:
        embed = discord.Embed(
            description="Your account is blocked.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if from_info["balance"] < amount:
        embed = discord.Embed(
            description="Insufficient funds.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    to_card, to_info = bank.get(to_card_or_nickname), bank.get(to_card_or_nickname)
    if not to_info:
        to_card, to_info = get_card_by_nickname(bank, to_card_or_nickname)
    if not to_info:
        embed = discord.Embed(
            description="Recipient card not found.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if to_info["blocked"]:
        embed = discord.Embed(
            description="Recipient account is blocked.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    from_info["balance"] -= amount
    to_info["balance"] += amount
    save_bank(bank)
    embed = discord.Embed(
        title="Transfer Successful",
        color=discord.Color.green()
    )
    embed.add_field(name="Amount", value=f"{amount}", inline=True)
    embed.add_field(name="To", value=f"{to_info['nickname']} (`{to_card}`)", inline=True)
    if message:
        embed.add_field(name="Message", value=message, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="bank_topup", description="Top up a player's account (banker only)")
async def bank_topup(interaction: discord.Interaction, amount: int, card_or_nickname: str):
    banker_role = get_banker_role(interaction.guild)
    if not banker_role or banker_role not in interaction.user.roles:
        embed = discord.Embed(
            description="Only bankers can use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    bank = load_bank()
    card, info = bank.get(card_or_nickname), bank.get(card_or_nickname)
    if not info:
        card, info = get_card_by_nickname(bank, card_or_nickname)
    if not info:
        embed = discord.Embed(
            description="Card not found.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if info["blocked"]:
        embed = discord.Embed(
            description="Account is blocked.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    info["balance"] += amount
    save_bank(bank)
    embed = discord.Embed(
        title="Top Up Successful",
        color=discord.Color.green()
    )
    embed.add_field(name="Card", value=f"`{card}`", inline=True)
    embed.add_field(name="Amount Added", value=f"{amount}", inline=True)
    embed.add_field(name="New Balance", value=f"{info['balance']}", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="bank_block", description="Block a player's account (banker only)")
async def bank_block(interaction: discord.Interaction, card_or_nickname: str):
    banker_role = get_banker_role(interaction.guild)
    if not banker_role or banker_role not in interaction.user.roles:
        embed = discord.Embed(
            description="Only bankers can use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    bank = load_bank()
    card, info = bank.get(card_or_nickname), bank.get(card_or_nickname)
    if not info:
        card, info = get_card_by_nickname(bank, card_or_nickname)
    if not info:
        embed = discord.Embed(
            description="Card not found.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    info["blocked"] = True
    save_bank(bank)
    embed = discord.Embed(
        title="Card Blocked",
        description=f"Card `{card}` has been blocked.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="bank_unlock", description="Unlock a blocked card (banker only)")
async def bank_unlock(interaction: discord.Interaction, card_or_nickname: str):
    banker_role = get_banker_role(interaction.guild)
    if not banker_role or banker_role not in interaction.user.roles:
        embed = discord.Embed(
            description="Only bankers can use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    bank = load_bank()
    card, info = bank.get(card_or_nickname), bank.get(card_or_nickname)
    if not info:
        card, info = get_card_by_nickname(bank, card_or_nickname)
    if not info:
        embed = discord.Embed(
            description="Card not found.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not info["blocked"]:
        embed = discord.Embed(
            description="Card is not blocked.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    info["blocked"] = False
    save_bank(bank)
    embed = discord.Embed(
        title="Card Unlocked",
        description=f"Card `{card}` has been unlocked.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="bank_delete", description="Delete a card (user or banker)")
async def bank_delete(interaction: discord.Interaction, card_or_nickname: str = None):
    bank = load_bank()
    banker_role = discord.utils.get(interaction.user.roles, name=BANKER_ROLE_NAME)
    if card_or_nickname:
        card, info = bank.get(card_or_nickname), bank.get(card_or_nickname)
        if not info:
            card, info = get_card_by_nickname(bank, card_or_nickname)
        if not info:
            embed = discord.Embed(
                description="Card not found.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if not banker_role and info["user_id"] != str(interaction.user.id):
            embed = discord.Embed(
                description="You can only delete your own card.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
    else:
        card, info = get_card_by_userid(bank, interaction.user.id)
        if not info:
            embed = discord.Embed(
                description="You don't have a card to delete.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

    del bank[card]
    save_bank(bank)
    embed = discord.Embed(
        title="Card Deleted",
        description=f"Card `{card}` has been deleted.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="bank_list", description="List all cards (banker only)")
async def bank_list(interaction: discord.Interaction):
    banker_role = discord.utils.get(interaction.user.roles, name=BANKER_ROLE_NAME)
    if not banker_role:
        embed = discord.Embed(
            description="Only bankers can use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    bank = load_bank()
    if not bank:
        embed = discord.Embed(
            description="No cards found.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    embed = discord.Embed(
        title="All Cards",
        color=discord.Color.blue()
    )
    for card, info in bank.items():
        status = "Blocked" if info["blocked"] else "Active"
        embed.add_field(
            name=f"Card: {card}",
            value=f"Nickname: {info['nickname']}\nBalance: {info['balance']}\nStatus: {status}",
            inline=False
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="bank_setroles", description="Set banker and citizen roles for the banking system")
@commands.has_permissions(administrator=True)
async def bank_setroles(
    interaction: discord.Interaction,
    banker_role: discord.Role,
    citizen_role: discord.Role
):
    if "bank_roles" not in guild_settings:
        guild_settings["bank_roles"] = {}
    guild_settings["bank_roles"][str(interaction.guild_id)] = {
        "banker_role_id": banker_role.id,
        "citizen_role_id": citizen_role.id
    }
    save_settings()
    
    bank_roles[str(interaction.guild_id)] = {
        "banker_role_id": banker_role.id,
        "citizen_role_id": citizen_role.id
    }
    embed = discord.Embed(
        title="Bank Roles Set",
        color=discord.Color.green()
    )
    embed.add_field(name="Banker Role", value=banker_role.mention, inline=False)
    embed.add_field(name="Citizen Role", value=citizen_role.mention, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


def get_banker_role(guild):
    roles = bank_roles.get(str(guild.id)) or guild_settings.get("bank_roles", {}).get(str(guild.id), {})
    return guild.get_role(roles.get("banker_role_id"))

def get_citizen_role(guild):
    roles = bank_roles.get(str(guild.id)) or guild_settings.get("bank_roles", {}).get(str(guild.id), {})
    return guild.get_role(roles.get("citizen_role_id"))


def initialize_bank_roles():
    global bank_roles
    bank_roles = guild_settings.get("bank_roles", {}).copy()



def graceful_shutdown(*args):
    save_settings()
    print("Bot data saved. Shutting down.")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_shutdown)  
signal.signal(signal.SIGTERM, graceful_shutdown) 

bot.run(token)
