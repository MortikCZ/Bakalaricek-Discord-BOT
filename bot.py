import discord
from discord.ext import commands, tasks
import datetime
from datetime import datetime, timedelta
from bakapiv2 import BakapiUser
import json
from collections import defaultdict
import os

with open('config.json') as config_file:
    config = json.load(config_file)

BOT_TOKEN = config["bot"]["token"]
BAKALARI_USERNAME = config["bakalari"]["username"]
BAKALARI_PASSWORD = config["bakalari"]["password"]
BAKALARI_URL = config["bakalari"]["url"]
SUBSTITUTIONS_CHANNEL_ID = config["discord"]["substitutions_channel_id"] if "discord" in config else None
SUBST_CHANGE_CHANNEL_ID = config["discord"]["subst_change_channel_id"] if "discord" in config else None

bakalari_user = BakapiUser(url=BAKALARI_URL, username=BAKALARI_USERNAME, password=BAKALARI_PASSWORD)

intents = discord.Intents.all() 

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    substitutions_embed.start()
    daily_timetable_embed.start()
    substitutions_notify.start()
    if 'status' in config['bot']:
        await bot.change_presence(activity=discord.Game(name=config['bot']['status']))

CONFIG_FILE = 'config.json'

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)

CURRENT_WEEK_FILE = 'current_week_substitutions.json'
NEXT_WEEK_FILE = 'next_week_substitutions.json'

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

STATUS_FILE = 'week_change_status.json'

def load_week_change_status():
    if not os.path.exists(STATUS_FILE):
        save_week_change_status(True)
    with open(STATUS_FILE, 'r') as file:
        return json.load(file).get('week_changed', False)

def save_week_change_status(status):
    with open(STATUS_FILE, 'w') as file:
        json.dump({'week_changed': status}, file)

@tasks.loop(minutes=30)
async def daily_timetable_embed():
    config = load_config()
    if 'discord' not in config or 'timetable_channel_id' not in config['discord']:
        return
    channel_id = config['discord']['timetable_channel_id']
    channel = bot.get_channel(channel_id)
    if channel is None:
        return

    current_date = datetime.today().date()
    if current_date.weekday() > 4: 
        current_date = get_next_weekday(current_date)

    current_date_str = current_date.strftime("%Y-%m-%d")
    current_date_display = current_date.strftime("%d.%m.")

    timetable = bakalari_user.get_timetable_actual(date=current_date_str)

    subjects = {subject['Id']: subject['Name'] for subject in timetable['Subjects']}
    teachers = {teacher['Id']: teacher['Name'] for teacher in timetable['Teachers']}

    hodiny = "\U0001F552"
    embed = discord.Embed(title=f"{hodiny} Aktuální rozvrh ({current_date_display})", color=0x02a2e2)

    vlajka_startu = "\U0001F6A9"
    vlajka_cile = "\U0001F3C1"
    kniha = "\U0001F4DA"
    ucitel = "\U0001F468\u200D\U0001F3EB"
    for day in timetable['Days']:
        if day['Date'].split('T')[0] == current_date_str:
            for atom in day['Atoms']:
                for hour in timetable['Hours']:
                    if hour['Id'] == atom['HourId']:
                        subject_name = subjects.get(atom['SubjectId'], 'Unknown')
                        teacher_name = teachers.get(atom['TeacherId'], 'Unknown') if atom['TeacherId'] else 'Unknown'
                        if subject_name == 'Unknown' and teacher_name == 'Unknown':
                            continue 
                        embed.add_field(name=f"Hodina č.{hour['Caption']}", 
                                        value=f"{vlajka_startu}: {hour['BeginTime']}\n{vlajka_cile}: {hour['EndTime']}\n{kniha}: {subject_name}\n{ucitel}: {teacher_name}", 
                                        inline=False)

    now = datetime.now()
    embed.set_footer(text=f"Poslední update: {now.strftime('%d.%m. %H:%M:%S')}")

    if 'timetable_message_id' in config['discord'] and config['discord']['timetable_message_id'] is not None:
        try:
            message_id = config['discord']['timetable_message_id']
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
        except discord.NotFound:
            message = await channel.send(embed=embed)
            config['discord']['timetable_message_id'] = message.id
            save_config(config)
    else:
        message = await channel.send(embed=embed)
        config['discord']['timetable_message_id'] = message.id
        save_config(config)

def get_next_weekday(date):
    while date.weekday() >= 5:  
        date += timedelta(days=1)
    return date

@tasks.loop(minutes=30)
async def substitutions_embed():
    config = load_config()
    if 'discord' not in config or 'substitutions_channel_id' not in config['discord']:
        return
    channel_id = config['discord']['substitutions_channel_id']
    channel = bot.get_channel(channel_id)
    if channel is None:
        return

    today = datetime.now()
    if today.weekday() >= 5: 
        today = get_next_weekday(today)

    substitutions = bakalari_user.get_substitutions()
    week_number = today.isocalendar()[1]
    embed = discord.Embed(title=f"Změny v rozvrhu ({week_number}.týden)", color=0x02a2e2)

    changes_by_date = defaultdict(list)
    for change in substitutions['Changes']:
        date_string = change['Day']
        date_object = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        if date_object.isocalendar()[1] != week_number:
            continue
        date = f"{date_object.strftime('%d.%m.')}"

        hour_number = f"🕑 {change['Hours']}"
        description = change['Description']
        changes_by_date[date].append(f"{hour_number} - {description}")

    for date, changes in changes_by_date.items():
        embed.add_field(name=date, value="\n".join(changes), inline=False)

    now = datetime.now()
    embed.set_footer(text=f"Poslední update: {now.strftime('%d.%m. %H:%M:%S')}")

    if 'subst_message_id' in config['discord'] and config['discord']['subst_message_id'] is not None:
        try:
            message_id = config['discord']['subst_message_id']
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
        except discord.NotFound:
            message = await channel.send(embed=embed)
            config['discord']['subst_message_id'] = message.id
            save_config(config)
    else:
        message = await channel.send(embed=embed)
        config['discord']['subst_message_id'] = message.id
        save_config(config)

@tasks.loop(minutes=30)
async def substitutions_notify():
    current_date = datetime.today().date()

    if current_date.weekday() == 0 and datetime.now().hour == 23 and datetime.now().minute >= 30:  
        save_week_change_status(False) 

    week_changed = load_week_change_status()
    if current_date.weekday() == 0 and not week_changed:
        week_change
        save_week_change_status(True) 
    
    global current_week_substitutions, next_week_substitutions
    next_week_date = current_date + timedelta(days=(7 - current_date.weekday()))

    substitutions = bakalari_user.get_substitutions()
    current_week_subs = {change['Day']: change for change in substitutions['Changes'] if datetime.fromisoformat(change['Day'].replace("Z", "+00:00")).isocalendar()[1] == current_date.isocalendar()[1]}
    next_week_subs = {change['Day']: change for change in substitutions['Changes'] if datetime.fromisoformat(change['Day'].replace("Z", "+00:00")).isocalendar()[1] == next_week_date.isocalendar()[1]}

    current_week_data = load_json(CURRENT_WEEK_FILE)
    next_week_data = load_json(NEXT_WEEK_FILE)

    new_changes = [change for day, change in current_week_subs.items() if day not in current_week_data or current_week_data[day] != change]
    new_next_week_changes = [change for day, change in next_week_subs.items() if day not in next_week_data or next_week_data[day] != change]

    if new_changes:
        channel = bot.get_channel(SUBST_CHANGE_CHANNEL_ID)
        role_id = config['discord']['subst_change_role_id']
        role_mention = f"<@&{role_id}>"
        for change in new_changes:
            date = change['Day'].split('T')[0]
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.")
            hour_number = f"🕑 {change['Hours']}"
            description = change['Description']
            message = (
                f"{role_mention}\n"
                f"# Nová změna v rozvrhu!\n"
                f"**Datum:** {formatted_date}\n"
                f"**Číslo hodiny:** {hour_number}\n"
                f"**Popis:** {description}"
            )
            await channel.send(message)

    if new_next_week_changes:
        channel = bot.get_channel(SUBST_CHANGE_CHANNEL_ID)
        role_id = config['discord']['subst_change_role_id']
        role_mention = f"<@&{role_id}>"
        for change in new_next_week_changes:
            date = change['Day'].split('T')[0]
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.")
            hour_number = f"🕑 {change['Hours']}"
            description = change['Description']
            message = (
                f"{role_mention}\n"
                f"# Změna v rozvrhu pro příští týden!\n"
                f"**Datum:** {formatted_date}\n"
                f"**Číslo hodiny:** {hour_number}\n"
                f"**Popis:** {description}"
            )
            await channel.send(message)

    save_json(CURRENT_WEEK_FILE, current_week_subs)
    save_json(NEXT_WEEK_FILE, next_week_subs)

def week_change(ctx):
    if os.path.exists(CURRENT_WEEK_FILE):
        os.remove(CURRENT_WEEK_FILE)
    if os.path.exists(NEXT_WEEK_FILE):
        os.rename(NEXT_WEEK_FILE, CURRENT_WEEK_FILE)
    next_week_subs = bakalari_user.get_substitutions()
    next_week_date = datetime.today().date() + timedelta(days=(7 - datetime.today().date().weekday()))
    next_week_subs = {change['Day']: change for change in next_week_subs['Changes'] if datetime.fromisoformat(change['Day'].replace("Z", "+00:00")).isocalendar()[1] == next_week_date.isocalendar()[1]}
    save_json(NEXT_WEEK_FILE, next_week_subs)
    
@bot.command()
@commands.has_permissions(administrator=True)
async def status(ctx, *, new_status: str):
    await bot.change_presence(activity=discord.Game(name=new_status))
    config = load_config()
    config['bot']['status'] = new_status
    save_config(config)
    await ctx.send(f"Status: {new_status}")

@status.error
async def status_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Pro tuto akci nemáš dostatečná oprávnění.")

bot.run(BOT_TOKEN)