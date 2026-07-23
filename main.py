import os
import json
import random
import asyncio
import time
from datetime import datetime
import discord
from discord.ext import commands
from keep_alive import keep_alive

keep_alive()

SUGGESTION_CHANNEL_ID = 1506046070533128473
DISCUSSION_CHANNEL_ID = 1508502264703090779
TEST_CHANNEL_ID = 1514958945213747260
NOTIFY_CHANNEL_ID = 1515796308818923756
SHOP_REQUESTS_CHANNEL_ID = 1515147902140547113
COIN_EMOJI = "<:cutecoin:1515057427920322682>"
COMMANDS_CHANNEL_ID = 1506045404322730195
DAILY_REWARD_MIN = 10
DAILY_REWARD_MAX = 30
POINTS_FILE = "points.json"
EVENT_FILE = "event_state.json"
TASK_RESET_SECONDS = 2 * 60 * 60
DAILY_MESSAGES_GOAL = 30

DAILY_CHANNEL_ID = 1506045466238783508
PHOTO_CHANNEL_ID = 1506045452141727754
GAMES_CHANNEL_ID = 1506045433816813638

VOICE_REQUIRED_SECONDS = 10 * 60

LEVEL_REWARDS = {
    1506787978029039636: (10, 30),   # لفل 5
    1506787834428788956: (15, 35),   # لفل 10
    1506788177195696169: (20, 40),   # لفل 15
    1506788259542335528: (25, 45),   # لفل 20
    1506788312835424327: (30, 50),   # لفل 25
    1506788441571065986: (35, 55),   # لفل 30
    1506788493161005167: (40, 60),   # لفل 35
    1506788542196744232: (45, 70),   # لفل 40
    1506788592490512536: (50, 80),   # لفل 45
    1506788704264388731: (60, 100),  # لفل 50
}

voice_sessions = {}

# حماية من سبام Discord API / Global Rate Limits
send_lock = asyncio.Lock()
reply_cooldowns = {}

def cooldown_ready(key, seconds):
    now = time.time()
    last = reply_cooldowns.get(key, 0)
    if now - last < seconds:
        return False
    reply_cooldowns[key] = now
    return True

async def safe_send(channel, *args, **kwargs):
    """يرسل الرسائل بهدوء ويمنع طيحة البوت وقت الـ Rate Limit."""
    async with send_lock:
        try:
            message = await channel.send(*args, **kwargs)
            await asyncio.sleep(2)
            return message
        except discord.HTTPException as e:
            print(f"[safe_send] Discord blocked/rate limited send: {e}")
            await asyncio.sleep(10)
            return None

async def safe_reply(message, *args, **kwargs):
    async with send_lock:
        try:
            reply = await message.reply(*args, **kwargs)
            await asyncio.sleep(2)
            return reply
        except discord.HTTPException as e:
            print(f"[safe_reply] Discord blocked/rate limited reply: {e}")
            await asyncio.sleep(10)
            return None

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    # لا نسوي sync كل تشغيل عشان ما نضغط Discord API إذا Render أعاد التشغيل.
    # إذا احتجت مزامنة، استخدم أمر !sync يدويًا مرة وحدة فقط.
    print(f"Logged on as {bot.user}!")


@bot.check
async def commands_channel_only(ctx):
    """الأعضاء يستخدمون أوامر ! في شات الأوامر فقط، والإدارة تقدر تستخدمها بأي مكان."""
    if ctx.author.guild_permissions.administrator:
        return True

    if ctx.channel.id != COMMANDS_CHANNEL_ID:
        try:
            await ctx.reply(
                f"❌ استخدم أوامر البوت في <#{COMMANDS_CHANNEL_ID}>.",
                delete_after=5,
                mention_author=False
            )
        except discord.HTTPException:
            pass
        return False

    return True


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.CheckFailure):
        return

    raise error


def load_points():
    try:
        with open(POINTS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except:
        return {}


def save_points(data):
    with open(POINTS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def get_today():
    return datetime.now().strftime("%Y-%m-%d")


def load_event_state():
    try:
        with open(EVENT_FILE, "r", encoding="utf-8") as file:
            state = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        state = {"active": False, "started_at": None}

    state.setdefault("active", False)
    state.setdefault("started_at", None)
    return state


def save_event_state(state):
    with open(EVENT_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=4)


def is_event_active():
    return bool(load_event_state().get("active", False))


def reward_balance_key():
    return "event_coins" if is_event_active() else "coins"


def get_user_data(data, user_id):
    user_id = str(user_id)
    today = get_today()

    if user_id not in data:
        data[user_id] = {
            "coins": 0,
            "event_coins": 0,
            "last_day": today,
            "task_reset_at": time.time(),
            "daily_gift_day": "",
            "gamble_day": today,
            "gamble_uses": 0,
            "tasks": {
                "messages": 0,
                "photo": False,
                "reactions": 0,
                "games": 0,
                "voice": 0
            },
            "completed_tasks": []
        }

    user_data = data[user_id]

    if "coins" not in user_data:
        user_data["coins"] = user_data.get("points", 0)

    if "event_coins" not in user_data:
        user_data["event_coins"] = 0

    if "daily_gift_day" not in user_data:
        user_data["daily_gift_day"] = ""

    if "gamble_day" not in user_data:
        user_data["gamble_day"] = today

    if "gamble_uses" not in user_data:
        user_data["gamble_uses"] = 0

    # لعبة الحظ متاحة مرتين فقط كل يوم
    if user_data.get("gamble_day") != today:
        user_data["gamble_day"] = today
        user_data["gamble_uses"] = 0

    if "task_reset_at" not in user_data:
        user_data["task_reset_at"] = time.time()

    if "tasks" not in user_data:
        user_data["tasks"] = {
            "messages": 0,
            "photo": False,
            "reactions": 0,
            "games": 0,
            "voice": 0
        }

    if "completed_tasks" not in user_data:
        user_data["completed_tasks"] = []

    # الرسائل والفويس فقط تتجدد كل ساعتين
    if time.time() - float(user_data.get("task_reset_at", 0)) >= TASK_RESET_SECONDS:
        user_data["task_reset_at"] = time.time()
        user_data["tasks"]["messages"] = 0
        user_data["tasks"]["voice"] = 0
        user_data["completed_tasks"] = [
            task for task in user_data["completed_tasks"]
            if task not in ("messages", "voice")
        ]

    # الصورة والتفاعل والألعاب تتجدد عند بداية يوم جديد
    if user_data.get("last_day") != today:
        user_data["last_day"] = today
        user_data["tasks"]["photo"] = False
        user_data["tasks"]["reactions"] = 0
        user_data["tasks"]["games"] = 0
        user_data["completed_tasks"] = [
            task for task in user_data["completed_tasks"]
            if task not in ("photo", "reactions", "games")
        ]

    return user_data

def get_reward_range(member):
    reward_min = DAILY_REWARD_MIN
    reward_max = DAILY_REWARD_MAX

    for role in member.roles:
        if role.id in LEVEL_REWARDS:
            role_min, role_max = LEVEL_REWARDS[role.id]
            if role_max > reward_max:
                reward_min = role_min
                reward_max = role_max

    return reward_min, reward_max


def format_reward_message(member, task_title, reward, luck_bonus):
    text = (
        f"{member.mention} أنجزت مهمة {task_title}!\n"
        f"حصلت على **{reward} Cute Coin {COIN_EMOJI}**"
    )

    if luck_bonus:
        text += f"\n🍀 بونس حظ: **+{luck_bonus} Cute Coin {COIN_EMOJI}**"

    return text


async def send_task_notification(guild, member, task_title, reward, luck_bonus):
    """يرسل إشعار إنجاز المهمة في روم الإشعارات فقط."""
    if not guild:
        return

    channel = guild.get_channel(NOTIFY_CHANNEL_ID) or bot.get_channel(NOTIFY_CHANNEL_ID)

    if not channel:
        return

    try:
        await safe_send(channel, format_reward_message(member, task_title, reward, luck_bonus))
    except discord.HTTPException:
        # لو ديسكورد عطانا Rate Limit لا نخلي البوت يطيح
        pass


async def require_commands_channel_interaction(interaction: discord.Interaction):
    """الأعضاء يستخدمون أوامر السلاش في شات الأوامر فقط، والإدارة تقدر تستخدمها بأي مكان."""
    if interaction.user.guild_permissions.administrator:
        return True

    if interaction.channel and interaction.channel.id != COMMANDS_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ استخدم هذا الأمر في <#{COMMANDS_CHANNEL_ID}>.",
            ephemeral=True
        )
        return False

    return True


def complete_task(member, task_name):
    data = load_points()
    user = get_user_data(data, member.id)

    if task_name in user["completed_tasks"]:
        save_points(data)
        return 0, 0

    reward_min, reward_max = get_reward_range(member)
    reward = random.randint(reward_min, reward_max)

    luck_bonus = 0
    if random.randint(1, 100) <= 10:
        luck_bonus = random.randint(5, 20)

    user[reward_balance_key()] += reward + luck_bonus
    user["completed_tasks"].append(task_name)

    save_points(data)
    return reward, luck_bonus


def add_counter_task_progress(member, task_key, goal):
    data = load_points()
    user = get_user_data(data, member.id)

    if task_key in user["completed_tasks"]:
        save_points(data)
        return 0, 0

    user["tasks"][task_key] += 1

    if user["tasks"][task_key] >= goal:
        reward_min, reward_max = get_reward_range(member)
        reward = random.randint(reward_min, reward_max)

        luck_bonus = 0
        if random.randint(1, 100) <= 10:
            luck_bonus = random.randint(5, 20)

        user[reward_balance_key()] += reward + luck_bonus
        user["completed_tasks"].append(task_key)

        save_points(data)
        return reward, luck_bonus

    save_points(data)
    return 0, 0


def set_photo_task_done(member):
    data = load_points()
    user = get_user_data(data, member.id)

    if "photo" in user["completed_tasks"]:
        save_points(data)
        return 0, 0

    user["tasks"]["photo"] = True

    reward_min, reward_max = get_reward_range(member)
    reward = random.randint(reward_min, reward_max)

    luck_bonus = 0
    if random.randint(1, 100) <= 10:
        luck_bonus = random.randint(5, 20)

    user[reward_balance_key()] += reward + luck_bonus
    user["completed_tasks"].append("photo")

    save_points(data)
    return reward, luck_bonus


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.strip() == "كيوتن":
        guild = message.guild

        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        created_at = discord.utils.format_dt(guild.created_at, style="D")

        embed = discord.Embed(
            title="🎀 𝗖𝘂𝘁𝗲𝗻 𝗭𝗼𝗻𝗲 🎀",
            description=(
                "✨ **أهلاً بك في عالم كيوتن** ✨\n"
                "مجتمع لطيف، سوالف، فعاليات، وأجواء رايقة.\n\n"

                "╭───・🧸 معلومات المجتمع・───╮\n"
                f"👥 **كل الأعضاء:** {guild.member_count}\n"
                f"👤 **الأعضاء الحقيقيين:** {humans}\n"
                f"🤖 **البوتات:** {bots}\n"
                f"🟢 **المتصلين الآن:** {online}\n"
                f"👑 **المالك:** {guild.owner.mention}\n"
                f"📅 **تأسس السيرفر:** {created_at}\n"
                "╰────────────────────╯\n\n"

                "╭───・📁 معلومات الرومات・───╮\n"
                f"💬 **رومات كتابية:** {text_channels}\n"
                f"🎙️ **رومات صوتية:** {voice_channels}\n"
                f"🗂️ **الأقسام:** {categories}\n"
                f"📌 **كل الرومات:** {len(guild.channels)}\n"
                "╰────────────────────╯\n\n"

                "╭───・🌸 الدعم والتجميل・───╮\n"
                f"🚀 **عدد البوستات:** {guild.premium_subscription_count}\n"
                f"💎 **مستوى البوست:** {guild.premium_tier}\n"
                f"🎭 **عدد الرتب:** {len(guild.roles)}\n"
                f"😺 **الإيموجيات:** {len(guild.emojis)}\n"
                f"🎨 **الستيكرات:** {len(guild.stickers)}\n"
                "╰────────────────────╯\n\n"

                "💖 **شكراً لكونك جزء من عائلة كيوتن**"
            ),
            color=0xCE44DB
        )

        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        if guild.banner:
            embed.set_image(url=guild.banner.url)

        embed.set_footer(text="Cuten Server Information")

        await safe_reply(message, embed=embed, mention_author=False)
        return

    if message.content.strip().lower() == "تاشيرو":
        # رد واحد كل 60 ثانية على مستوى السيرفر، عشان السبام ما يبند البوت من Discord API.
        if not cooldown_ready(f"tashiro:{message.guild.id if message.guild else message.channel.id}", 60):
            return

        replies = [
            ("text", "اذا ما رديت عليك اعرف اني مشغول او انك غثيث !"),
            ("text", "اسفين تاشيرو على ازعاجك بس اتمنى انك ترد على الكيوت ذا <:2heeh:1509687414921363467>"),
            ("gif", "https://cdn.discordapp.com/attachments/1508502008720789565/1513995625052508250/tenor.gif")
        ]

        reply_type, content = random.choice(replies)
        await safe_send(message.channel, f"{content}\n\n<@1044310877429575682>")
        return

    if message.content.strip().lower() == "نيرف":
        # رد واحد كل 60 ثانية على مستوى السيرفر، عشان السبام ما يبند البوت من Discord API.
        if not cooldown_ready(f"nerv:{message.guild.id if message.guild else message.channel.id}", 60):
            return

        replies = [
            ("text", "اذ شفت رسالتك برد عليك يا كيوتن !"),
            ("text", "لحظات وارد عليك يا كيوتن."),
            ("gif", "https://cdn.discordapp.com/attachments/1508502008720789565/1513995624419430621/tenor_2.gif"),
            ("gif", "https://cdn.discordapp.com/attachments/1508502008720789565/1513995624750776513/tenor_1.gif"),
        ]

        reply_type, content = random.choice(replies)
        await safe_send(message.channel, f"{content}\n\n<@944222907385643050>")
        return

    if message.channel.id == SUGGESTION_CHANNEL_ID:
        try:
            await message.delete()
        except:
            pass

        if cooldown_ready(f"suggestion_warn:{message.author.id}", 30):
            await safe_send(
                message.channel,
                f"📮 {message.author.mention} لإرسال اقتراح جديد استخدم `/اقتراح` ثم اختر نوع الاقتراح.",
                delete_after=8
            )
        return

    if message.channel.id == DAILY_CHANNEL_ID:
        reward, bonus = add_counter_task_progress(message.author, "reactions", 3)
        if reward:
            await send_task_notification(message.guild, message.author, "اليوميات", reward, bonus)

    reward, bonus = add_counter_task_progress(message.author, "messages", DAILY_MESSAGES_GOAL)
    if reward:
        await send_task_notification(message.guild, message.author, "الرسائل", reward, bonus)
    if message.channel.id == PHOTO_CHANNEL_ID and message.attachments:
        reward, bonus = set_photo_task_done(message.author)
        if reward:
            await send_task_notification(message.guild, message.author, "الصور", reward, bonus)

    if message.channel.id == GAMES_CHANNEL_ID:
        reward, bonus = add_counter_task_progress(message.author, "games", 5)
        if reward:
            await send_task_notification(message.guild, message.author, "شات الألعاب", reward, bonus)

    await bot.process_commands(message)
    
@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    if reaction.message.channel.id != DAILY_CHANNEL_ID:
        return

    guild = reaction.message.guild
    member = guild.get_member(user.id)

    if not member:
        return

    reward, bonus = add_counter_task_progress(member, "reactions", 3)

    if reward:
        await send_task_notification(guild, member, "التفاعل", reward, bonus)


@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    if before.channel is None and after.channel is not None:
        voice_sessions[member.id] = datetime.now()

    if before.channel is not None and after.channel is None:
        start_time = voice_sessions.pop(member.id, None)

        if not start_time:
            return

        seconds = (datetime.now() - start_time).total_seconds()

        if seconds >= VOICE_REQUIRED_SECONDS:
            reward, bonus = complete_task(member, "voice")

            if reward:
                await send_task_notification(member.guild, member, "الفويس", reward, bonus)


@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"✅ تم مزامنة {len(synced)} أمر")


@bot.tree.command(name="setup", description="إرسال لوحة تعريف السيرفر")
async def setup(interaction: discord.Interaction):

    embed = discord.Embed(
        title="<a:fku:1509688683643666472> cuten",
        description="أهلًا فيك في كيوتن\nاستخدم الأزرار بالأسفل للتعرف على سيرفرنا ومميزاته",
        color=0xCE44DB
    )

    embed.set_image(url="https://cdn.discordapp.com/attachments/1514958945213747260/1519701270057717770/31F4E062-4DEE-471C-8AC7-B95B703D35BC.gif?ex=6a3e8399&is=6a3d3219&hm=e0cfc030ec44c899ab3ee094b18834e8ec230c4ecc7d5cd1988d6f67a2c1e304")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1514958945213747260/1519700317095198800/48290B92-733D-4D63-81AA-A835F4A2D1F1.gif?ex=6a3e82b6&is=6a3d3136&hm=4074ef87ee0a08f4926de17584f35e9c58727450cedc906041cb784ade4721f2&")

    view = discord.ui.View(timeout=None)

    about_button = discord.ui.Button(
        label="نبذة عنا",
        emoji="<a:A_:1449356217674764399>",
        style=discord.ButtonStyle.secondary
    )

    async def about_callback(interaction):
        await interaction.response.send_message(
            "> 🎀 **سيرفر كيوتن | Cuten 🎀**\n"
            "> •———————• 🧸 •———————•\n"
            "> مرحباً بكم في عالمنا.. مكاننا مو مجرد سيرفر، هو المساحة الدافئة اللي تجمعنا كل يوم ✨ هنا صممنا مجتمع مريح لكل شخص حاب يفضفض، يسولف، أو يشارك يومياته بكل عفوية.\n"
            "> 🪐 **ليش إحنا هنا؟**\n"
            "> 💬 **سوالف وراحة:** مكانك المثالي للاسترخاء والفضفضة بعد يوم طويل.\n"
            "> 🤝 **احترام متبادل:** أساسنا هو التقدير والود بين الكل، بدون رسميات وبكل احترام.\n"
            "> ☕ **أجواء رايقة:** شاركنا اهتماماتك، صورك، أو مجرد وجودك اللطيف معنا.\n"
            "> •———————• 🤍 •———————•\n"
            "> **خذ لك كوب قهوة ونوّرنا بالشات.. مساحتك الآمنة بانتظارك! 💖**",
            ephemeral=True
        )

    about_button.callback = about_callback
    view.add_item(about_button)

    rules_button = discord.ui.Button(
        label="القوانين",
        emoji="<a:6bonk:1509687959086043166>",
        style=discord.ButtonStyle.secondary
    )

    async def rules_callback(interaction):
        await interaction.response.send_message(
            "📜 **قوانين مجتمع كيوتن | Cuten Rules** 📜\n"
            "•———————• 🧸 •———————•\n"
            "يا هلا فيكم بنور السيرفر! ✨\n"
            "عشان تظل مساحتنا آمنة، مريحة، ومليانة طاقة إيجابية للكل، حطينا هالقوانين البسيطة. التزامك فيها يعكس ذوقك ولطفك، ويساعدنا نحافظ على بيئة محترمة تجمعنا على الخير والسوالف الحلوة.\n"
            "**الرجاء الاطلاع على البنود أدناه والالتزام بها لضمان وقت ممتع للجميع: 👇**\n"
            "https://discord.com/channels/1506043098285867188/1506045317555163166/1506708096687538308",
            ephemeral=True
        )

    rules_button.callback = rules_callback
    view.add_item(rules_button)

    invite_button = discord.ui.Button(
        label="دعوة سيرفر",
        emoji="<a:heart:1511835528876654723>",
        style=discord.ButtonStyle.secondary
    )

    async def invite_callback(interaction):
        await interaction.response.send_message(
            "🔗 **رابط دعوة سيرفر كيوتن | Cuten Invite Link** 🔗\n"
            "•———————• 🧸 •———————•\n"
            "يا هلا فيكم بنور السيرفر! ✨\n"
            "إذا حبيتوا تنضموا لعائلتنا الحلوة، تفضلوا الرابط أدناه وانضموا لرحلتنا الممتعة في عالم كيوتن: 👇\n"
            "https://discord.gg/cuten",
            ephemeral=True
        )

    invite_button.callback = invite_callback
    view.add_item(invite_button)

    server_button = discord.ui.Button(
        label="سيرفراتنا",
        emoji="<:wow:1509681789302603886>",
        style=discord.ButtonStyle.secondary
    )

    async def server_callback(interaction):
        await interaction.response.send_message(
            "🤝 شركاء النجاح | Our Partners 🤝\n"
            "•———————• 🧸 •———————•\n\n"
            "يا هلا والله! ✨\n"
            "هنا نعتز ونفتخر بصداقتنا مع سيرفرات ومجتمعات رهيبة تشاركنا نفس الشغف والروح اللطيفة.\n"
            "هالمساحة مخصصة لدعم حلفائنا اللي نعتبرهم جزء من عائلتنا الكبيرة 💖\n\n"
            "خذوا لكم لفة ونوّروهم في سيرفراتهم 👇\n\n"
            "السيرفر الاول\n"
            "https://discord.gg/ang-els\n\n"
            "السيرفر الثاني\n"
            "https://discord.gg/R2CnxvNFUJ",
            ephemeral=True
        )

    server_button.callback = server_callback
    view.add_item(server_button)

    boost_button = discord.ui.Button(
        label="مميزات البوست",
        emoji="<:emoji_87:1476137223161380934>",
        style=discord.ButtonStyle.secondary
    )

    async def boost_callback(interaction):
        await interaction.response.send_message(
            "> 🔮 **مـمـيـزات الـبـوسـت | Booster Perks** 🔮\n"
            "> ‏•———————• 🧸 •———————•\n"
            "> دعمكم هو اللي يخلي سيرفر **كيوتن** يكبـر ويتميّز! ✨ لـكل شخـص حـاب يدعمنـا بـ (Boost) ويساعدنـا نـطوّر المـكان، هـذي هـدايـا ومميـزات خـاصـة تقديراً للطفـكم وجـودكـم معنـا:\n"
            "> ✨ **【 مميزات البوست الواحد | 1x Boost 】**\n"
            "> 🛡️ رول خـاص فيك بالـسيرفر بدون لون (Booster Role).\n"
            "> 💖 ألوان حصرية ومميزة لاسمك في الشات.\n"
            "> 📸 قـدرة على رفـع صـور ومـلفـات بدون الحاجة للحصول على لفل.\n"
            "> 👑 **【 مميزات البوستين | 2x Boost 】**\n"
            "> ✨ كـل مميـزات البـوست الواحـد +\n"
            "> 🎭 رول خـاص بـإسم مـن إختيـارك ولـون مـن ذوقـك.\n"
            "> 💬 صـلاحيـة تغييـر النـك نـيم (Nickname) الخاص فيك بـأي وقت.\n"
            "> 📢 صـلاحيـة النـشر في خـانـة الصـور والميـمز بـدون قيـود.\n"
            "> ⭐ أولـويـة الدخـول والـمشـاركـة في الفعـاليـات والجوائز.\n"
            "> 💐 صلاحية الكتابة في روم الداعمين فقط ! .\n"
            "> ‏•———————• 🤍 •———————•\n"
            "> **شكراً لكل شخص يدعمنا ويساهم في رسم ابتسامة على مجتمعنا! 🍵**",
            ephemeral=True
        )

    boost_button.callback = boost_callback
    view.add_item(boost_button)

    levels_button = discord.ui.Button(
        label="مميزات اللفل",
        emoji="<a:6celebrate:1509687911732351046>",
        style=discord.ButtonStyle.secondary
    )

    async def levels_callback(interaction):
        await interaction.response.send_message(
            "📈 **مميزات اللفل| Levels System** 📈\n"
            "\n> 🏆 **مـمـيـزات الـلـفـلات | Level Roles Perks** 🏆\n"
            "> ‏•———————• 🧸 •———————•\n"
            "> تفاعلكم وسوالفكم هي اللي تحوّلي السيرفر لبيتنا الثاني! ✨ وتقديراً لكل شخص يتفاعل معنا ويقضي وقته في **كيوتن**، سوينا لكم نظام لـفـلات مميز يعطيك رولات وصلاحيات كل ما زاد تفاعلك:\n"
            "> ⭐ **【 <@&1506787978029039636> 】**\n"
            "> 🏷️ رول مميز يثبت بداية تفاعلك معنا + إمكانية استخدام الإيموجيات والستيكرات الخارجية (External Emojis).\n"
            "> ⭐ **【 <@&1506787834428788956> 】**\n"
            "> 📸 صلاحية إرسال الصور والمقاطع في الشات العام.\n"
            "> ⭐ **【 <@&1506788177195696169> 】**\n"
            "> 🔗 صلاحية نشر الروابط (Links) بـشكل آمن .\n"
            "> ⭐ **【 <@&1506788259542335528> 】**\n"
            "> 🎙️ صلاحية استخدام الـ (Soundboard) والأصوات داخل الرومات الصوتية.\n"
            "> 🏅 **【 <@&1506788312835424327> 】**\n"
            "> 🛡️ رول مميز ب اسم من اختيارك (بدون لون).\n"
            "> 🏅 **【 <@&1506788441571065986> 】**\n"
            "> 💬 صلاحية تغيير النك نيم (Nickname) الخاص فيك بـنفسك.\n"
            "> 🏅 **【 <@&1506788493161005167> 】**\n"
            "> الحصول على اولوية المشاركة في الفعاليات !.\n"
            "> 👑 **【 <@&1506788542196744232> 】**\n"
            "> ✨ صلاحية الدخول لـروم كبار الشخصيات (VIP Chat).\n"
            "> 👑 **【 <@&1506788592490512536> 】**\n"
            "> 🎙️ صلاحية الأولوية في الكلام (Priority Speaker) داخل الرومات الصوتية والفعاليات.\n"
            "> 🏆 **【 <@&1506788704264388731> 】**\n"
            "> 🎭 رول خـاص بـإسم مـن إختيـارك ولـون مـن ذوقـك يثبت إنك من أساطير السيرفر!\n"
            "> ‏•———————• 🤍 •———————•\n"
            "> **شدّوا الحيل في الشات ونورونا بسوالفكم الحلوة عشان توصلون لأعلى اللفلات! 🫂✨**",
            ephemeral=True
        )

    levels_button.callback = levels_callback
    view.add_item(levels_button)

    help_button = discord.ui.Button(
        label="مساعدة",
        emoji="<a:noih10:1509687143809941515>",
        style=discord.ButtonStyle.secondary
    )

    async def help_callback(interaction):
        await interaction.response.send_message(
            "❓ **مساعدة | Help** ❓\n"
            "•———————• 🧸 •———————•\n"
            "يا هلا فيكم بنور السيرفر! ✨\n"
            "إذا حبيتوا مساعدة أو لديك أسئلة، تفضلوا في أي وقت نحن هنا لنساعدكم.\n"
            "https://discord.com/channels/1506043098285867188/1506046052040704040",
            ephemeral=True
        )

    help_button.callback = help_callback
    view.add_item(help_button)

    tag_button = discord.ui.Button(
        label="مميزات التاق",
        emoji="<a:6Love:1509687854681424033>",
        style=discord.ButtonStyle.secondary
    )

    async def tag_callback(interaction):
        await interaction.response.send_message(
            "## 🎀 ┃ 𝗖𝘂𝘁𝗲𝗻 𝗧𝗮𝗴 • دعم السيرفر بالتاق\n"
            "**يا هلا والله بالكيوتين الحلوين، ✨🌸**\n"
            "حابين نكافئ كل شخص لطيف يفتخر بوجوده معنا في **Cuten Zone** ويحب يزين بروفايله بـ تاق السيرفر الجميل جنب اسمه! 💕\n"
            "كل اللي عليك تسويه، تحط التاق اللطيف هذا جنب اسمك في الديسكورد مباشرة\n"
            "### 🧸 ┃ المزايا والهدايا اللطيفة (سهلة وبسيطة):\n"
            "**👑 رتبة مميزة:** رتبة ** 🎀 ┃ <@&1510089783484088421>  ** بلون وردي يجنن يميّزك بقائمة الأعضاء.\n"
            " **💞 شات الداعمين:** دخول تلقائي لروم خاص لحاملي التاق (روم سوالف ورايق).\n"
            "* **📸 صلاحيات حصرية:** تقدر تنزل صور ومقاطع في الشات العام (بدون ما تحتاج لفل عالي).\n"
            "### 🍰 ┃ كيف تستلم مكافأتك اللطيفة؟\n"
            "أول ما تحط التاق جنب اسمك، شرفنا في روم \n"
            "**[ 💌 ┃ <#1506046052040704040>  ]** وبنعطيها لك بثانية! 🎈\n"
            "شكراً لأنكم تخلون عالمنا ألطف وأجمل بوجودكم ودعمكم المستمر لينا ♡",
            ephemeral=True
        )

    tag_button.callback = tag_callback
    view.add_item(tag_button)

    await interaction.response.send_message(embed=embed, view=view)


class AdminReplyModal(discord.ui.Modal, title="رد الإدارة على الاقتراح"):
    reply = discord.ui.TextInput(
        label="اكتب رد الإدارة",
        placeholder="مثال: تم قبول الفكرة وراح نشتغل عليها قريبًا",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=800
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]

        embed.add_field(
            name="💬 رد الإدارة",
            value=f"{self.reply.value}\n\nبواسطة: {interaction.user.mention}",
            inline=False
        )

        embed.color = 0xF8BBD0
        await interaction.response.edit_message(embed=embed)


class SuggestionVoteView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.yes_votes = set()
        self.no_votes = set()

    async def update_embed(self, interaction):
        embed = interaction.message.embeds[0]

        embed.set_field_at(
            3,
            name="📊 التصويت",
            value=f"✅ {len(self.yes_votes)} | ❌ {len(self.no_votes)}",
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="موافق", emoji="✅", style=discord.ButtonStyle.success)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            await interaction.response.send_message("❌ ما تقدر تصوّت على اقتراحك.", ephemeral=True)
            return

        user_id = interaction.user.id

        if user_id in self.yes_votes:
            self.yes_votes.remove(user_id)
        else:
            self.yes_votes.add(user_id)
            self.no_votes.discard(user_id)

        await self.update_embed(interaction)

    @discord.ui.button(label="غير موافق", emoji="❌", style=discord.ButtonStyle.danger)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            await interaction.response.send_message("❌ ما تقدر تصوّت على اقتراحك.", ephemeral=True)
            return

        user_id = interaction.user.id

        if user_id in self.no_votes:
            self.no_votes.remove(user_id)
        else:
            self.no_votes.add(user_id)
            self.yes_votes.discard(user_id)

        await self.update_embed(interaction)

    @discord.ui.button(label="المصوتين", emoji="📋", style=discord.ButtonStyle.primary)
    async def voters_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        yes_list = "\n".join([f"<@{user_id}>" for user_id in self.yes_votes]) or "لا يوجد"
        no_list = "\n".join([f"<@{user_id}>" for user_id in self.no_votes]) or "لا يوجد"

        await interaction.response.send_message(
            f"✅ **الموافقين:**\n{yes_list}\n\n"
            f"❌ **غير الموافقين:**\n{no_list}",
            ephemeral=True
        )

    @discord.ui.button(label="رد الإدارة", emoji="💬", style=discord.ButtonStyle.secondary)
    async def admin_reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ هذا الزر للإدارة فقط.", ephemeral=True)
            return

        await interaction.response.send_modal(AdminReplyModal())

    @discord.ui.button(label="تم الاقتراح", emoji="🛠️", style=discord.ButtonStyle.secondary)
    async def done_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ هذا الزر للإدارة فقط.", ephemeral=True)
            return

        embed = interaction.message.embeds[0]
        embed.color = 0x57F287

        embed.add_field(
            name="✅ الحالة",
            value=f"تم اعتماد الاقتراح بواسطة {interaction.user.mention}",
            inline=False
        )

        button.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)


class SuggestionModal(discord.ui.Modal, title="إرسال اقتراح"):
    suggestion = discord.ui.TextInput(
        label="اكتب اقتراحك هنا",
        placeholder="مثال: سووا فعالية رعب يوم الجمعة",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    def __init__(self, suggestion_type):
        super().__init__()
        self.suggestion_type = suggestion_type

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(SUGGESTION_CHANNEL_ID)
        discussion_channel = interaction.guild.get_channel(DISCUSSION_CHANNEL_ID)

        embed = discord.Embed(
            title="✨ اقتراح جديد | Cuten Zone ✨",
            color=0xCE44DB
        )

        embed.add_field(name="📂 نوع الاقتراح", value=self.suggestion_type, inline=False)
        embed.add_field(name="📝 الاقتراح", value=self.suggestion.value, inline=False)
        embed.add_field(name="👤 صاحب الاقتراح", value=interaction.user.mention, inline=False)
        embed.add_field(name="📊 التصويت", value="✅ 0 | ❌ 0", inline=False)

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Cuten Suggestions System")

        suggestion_message = await channel.send(
            embed=embed,
            view=SuggestionVoteView(interaction.user.id)
        )

        if discussion_channel:
            await discussion_channel.send(
                f"📌 **اقتراح جديد للنقاش**\n"
                f"👤 صاحب الاقتراح: {interaction.user.mention}\n"
                f"📂 نوع الاقتراح: {self.suggestion_type}\n"
                f"🔗 رابط الاقتراح: {suggestion_message.jump_url}",
                embed=embed
            )

        await interaction.response.send_message(
            "✅ تم إرسال اقتراحك بنجاح!",
            ephemeral=True
        )


@bot.tree.command(name="اقتراح", description="إرسال اقتراح للسيرفر")
@discord.app_commands.choices(
    النوع=[
        discord.app_commands.Choice(name="🎉 فعاليات", value="🎉 فعاليات"),
        discord.app_commands.Choice(name="🤖 بوتات", value="🤖 بوتات"),
        discord.app_commands.Choice(name="💬 رومات", value="💬 رومات"),
        discord.app_commands.Choice(name="🎨 تصميم", value="🎨 تصميم"),
        discord.app_commands.Choice(name="🛠️ إدارة", value="🛠️ إدارة"),
        discord.app_commands.Choice(name="✨ أخرى", value="✨ أخرى"),
    ]
)
async def اقتراح(interaction: discord.Interaction, النوع: discord.app_commands.Choice[str]):
    if not await require_commands_channel_interaction(interaction):
        return

    await interaction.response.send_modal(SuggestionModal(النوع.value))
@bot.command(name="رصيدي")
async def رصيدي(ctx):
    data = load_points()
    user = get_user_data(data, ctx.author.id)
    event_active = is_event_active()
    balance_key = "event_coins" if event_active else "coins"
    coins = user.get(balance_key, 0)
    save_points(data)

    balance_name = "نقطة فعالية" if event_active else "Cute Coin"
    title = "🎉 رصيد الفعالية" if event_active else "💰 رصيدك"
    embed = discord.Embed(
        title=title,
        description=f"{ctx.author.mention}\n\nمعك **{coins} {balance_name} {COIN_EMOJI}**",
        color=0xCE44DB
    )

    await ctx.reply(embed=embed, mention_author=False)


@bot.command(name="مهامي")
async def مهامي(ctx):
    data = load_points()
    user = get_user_data(data, ctx.author.id)
    tasks = user["tasks"]
    completed = user["completed_tasks"]
    save_points(data)

    messages_status = "مكتملة" if "messages" in completed else f"{tasks['messages']}/{DAILY_MESSAGES_GOAL}"
    photo_status = "مكتملة" if "photo" in completed else "غير مكتملة"
    daily_status = "مكتملة" if "reactions" in completed else f"{tasks['reactions']}/3"
    games_status = "مكتملة" if "games" in completed else f"{tasks['games']}/5"
    voice_status = "مكتملة" if "voice" in completed else "10 دقائق"

    remaining = max(0, TASK_RESET_SECONDS - int(time.time() - float(user.get("task_reset_at", time.time()))))
    hours, remainder = divmod(remaining, 3600)
    minutes = remainder // 60

    embed = discord.Embed(
        title="🎯 مهامك المتجددة",
        description=(
            f"💬 **الرسائل:** {messages_status}\n"
            f"📸 **صورة في <#{PHOTO_CHANNEL_ID}>:** {photo_status}\n"
            f"💞 **تفاعل في <#{DAILY_CHANNEL_ID}>:** {daily_status}\n"
            f"🎮 **رسائل في <#{GAMES_CHANNEL_ID}>:** {games_status}\n"
            f"🎙️ **الفويس:** {voice_status}\n\n"
            f"🎁 **المكافأة:** حسب لفلك + احتمال بونس حظ\n"
            f"⏳ **التجديد بعد:** {hours} ساعة و {minutes} دقيقة\n"
            f"{COIN_EMOJI} **الرصيد الحالي:** {'نقاط الفعالية' if is_event_active() else 'Cute Coin'}"
        ),
        color=0xCE44DB
    )

    await ctx.reply(embed=embed, mention_author=False)

@bot.command(name="هدية")
async def هدية(ctx):
    if is_event_active():
        await ctx.reply("🎉 الهدية اليومية متوقفة أثناء الفعالية؛ التجميع يكون من المهام فقط.", mention_author=False)
        return

    data = load_points()
    user = get_user_data(data, ctx.author.id)
    today = get_today()

    if user.get("daily_gift_day") == today:
        await ctx.reply("أخذت هديتك اليومية اليوم، ارجع بكرا.", mention_author=False)
        save_points(data)
        return

    reward = random.randint(10, 60)

    lucky_text = ""
    if random.randint(1, 100) <= 8:
        bonus = random.randint(20, 80)
        reward += bonus
        lucky_text = f"\n🍀 حظك رهيب! بونس إضافي **+{bonus} Cute Coin {COIN_EMOJI}**"

    user["coins"] += reward
    user["daily_gift_day"] = today
    save_points(data)

    embed = discord.Embed(
        title="🎁 هديتك اليومية",
        description=(
            f"{ctx.author.mention}\n\n"
            f"حصلت على **{reward} Cute Coin {COIN_EMOJI}**"
            f"{lucky_text}"
        ),
        color=0xCE44DB
    )

    await ctx.reply(embed=embed, mention_author=False)



@bot.command(name="أوامر")
async def اوامر(ctx):
    embed = discord.Embed(
        title="📜 أوامر Cute Coin",
        description=(
            f"{COIN_EMOJI} **أوامر الأعضاء**\n"
            "`!رصيدي` — يعرض رصيدك من Cute Coin\n"
            "`!مهامي` — يعرض مهامك اليومية\n"
            "`!هدية` — تستلم هديتك اليومية\n"
            "`/تحويل` — تحول Cute Coin لعضو آخر\n"
            "`/توب_الكوينز` — يعرض التوب الأصلي أو توب الفعالية تلقائيًا\n"
            "`/حالة_الفعالية` — يعرض حالة الفعالية\n\n"
            "🛡️ **أوامر الإدارة**\n"
            "`/تعويض_الجميع` — يعطي كل الأعضاء مبلغ تعويض\n"
            "`!تعويض_الجميع المبلغ` — نفس أمر التعويض لكن بأمر عادي\n"
            "`/بدء_الفعالية` — يبدأ رصيد فعالية منفصل\n"
            "`/انهاء_الفعالية` — يعلن النتائج ويحذف نقاط الفعالية فقط\n\n"
            "🛒 **المتجر**\n"
            "تقدر تشتري من لوحة المتجر بالأزرار بعد ما ترسلها الإدارة.\n\n"

        ),
        color=0xCE44DB
    )
    embed.set_footer(text="Cuten Cute Coin System")
    await ctx.reply(embed=embed, mention_author=False)


SHOP_REQUESTS_CHANNEL_ID = 1508502264703090779
COIN_EMOJI = "<:cutecoin:1515057427920322682>"
SHOP_IMAGE_URL = "https://i.imgur.com/WdTt5xZ.png"

SHOP_ITEMS = {
    "color": {
        "name": "🎨 لون خاص",
        "price": 2000,
        "desc": "اطلب لون خاص باسمك",
        "modal": True
    },
    "rank": {
        "name": "🏷️ رتبة خاصة",
        "price": 5000,
        "desc": "اطلب رتبة خاصة باسم ولون من اختيارك",
        "modal": True
    },
    "clan": {
        "name": "👥 كلان خاص",
        "price": 15000,
        "desc": "افتح كلان خاص لك ولأعضاءك",
        "modal": True
    },
    "gamble": {
        "name": "🎲 تصيب أو تخيب",
        "price": 200,
        "desc": "ممكن تكسب أضعافها وممكن تخسرها",
        "modal": False
    }
}


class ShopDetailsModal(discord.ui.Modal):
    def __init__(self, item_key, item):
        super().__init__(title=f"تفاصيل الطلب | {item['name']}")
        self.item_key = item_key
        self.item = item

        if item_key == "color":
            self.detail1 = discord.ui.TextInput(
                label="اللون المطلوب",
                placeholder="مثال: وردي فاتح أو #FF69B4",
                required=True,
                max_length=100
            )
            self.add_item(self.detail1)

        elif item_key == "rank":
            self.detail1 = discord.ui.TextInput(
                label="اسم الرتبة",
                placeholder="مثال: أمير كيوتن",
                required=True,
                max_length=100
            )
            self.detail2 = discord.ui.TextInput(
                label="لون الرتبة",
                placeholder="مثال: بنفسجي أو #B388FF",
                required=True,
                max_length=100
            )
            self.add_item(self.detail1)
            self.add_item(self.detail2)

        elif item_key == "clan":
            self.detail1 = discord.ui.TextInput(
                label="اسم الكلان",
                placeholder="مثال: Cuten Stars",
                required=True,
                max_length=100
            )
            self.detail2 = discord.ui.TextInput(
                label="لون الكلان",
                placeholder="مثال: أحمر غامق أو #8B0000",
                required=True,
                max_length=100
            )
            self.detail3 = discord.ui.TextInput(
                label="أعضاء الكلان",
                placeholder="اكتب 5 أعضاء بالمنشن أو الأسماء",
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=500
            )
            self.add_item(self.detail1)
            self.add_item(self.detail2)
            self.add_item(self.detail3)

    async def on_submit(self, interaction: discord.Interaction):
        if is_event_active():
            await interaction.response.send_message("❌ المتجر متوقف أثناء الفعالية، ونقاط الفعالية ما تنصرف.", ephemeral=True)
            return

        data = load_points()
        user = get_user_data(data, interaction.user.id)
        price = self.item["price"]

        if user["coins"] < price:
            await interaction.response.send_message(
                f"❌ رصيدك ما يكفي.\nمعك **{user['coins']} {COIN_EMOJI}**",
                ephemeral=True
            )
            return

        user["coins"] -= price
        save_points(data)

        if self.item_key == "color":
            details = f"🎨 **اللون المطلوب:** {self.detail1.value}"

        elif self.item_key == "rank":
            details = (
                f"🏷️ **اسم الرتبة:** {self.detail1.value}\n"
                f"🎨 **لون الرتبة:** {self.detail2.value}"
            )

        elif self.item_key == "clan":
            details = (
                f"👥 **اسم الكلان:** {self.detail1.value}\n"
                f"🎨 **لون الكلان:** {self.detail2.value}\n"
                f"👤 **أعضاء الكلان:**\n{self.detail3.value}"
            )

        request_channel = interaction.guild.get_channel(SHOP_REQUESTS_CHANNEL_ID)

        if request_channel:
            embed = discord.Embed(
                title="🛒 طلب شراء جديد",
                description=(
                    f"👤 **العضو:** {interaction.user.mention}\n"
                    f"📦 **المنتج:** {self.item['name']}\n"
                    f"💰 **السعر:** {price} {COIN_EMOJI}\n"
                    f"💳 **الرصيد بعد الشراء:** {user['coins']} {COIN_EMOJI}\n\n"
                    f"📋 **تفاصيل الطلب:**\n{details}"
                ),
                color=0xCE44DB
            )
            await request_channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ تم إرسال طلبك للإدارة، انتظر التسليم.",
            ephemeral=True
        )


class ConfirmPurchaseView(discord.ui.View):
    def __init__(self, user_id, item_key):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.item_key = item_key

    @discord.ui.button(label="تأكيد الشراء", emoji="✅", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if is_event_active():
            await interaction.response.send_message("❌ المتجر متوقف أثناء الفعالية، ونقاط الفعالية ما تنصرف.", ephemeral=True)
            return

        if interaction.user.id != self.user_id:
            await interaction.response.send_message("هذا الطلب مو لك.", ephemeral=True)
            return

        item = SHOP_ITEMS[self.item_key]

        if item["modal"]:
            await interaction.response.send_modal(ShopDetailsModal(self.item_key, item))
            return

        data = load_points()
        user = get_user_data(data, interaction.user.id)
        price = item["price"]

        if self.item_key == "gamble" and user.get("gamble_uses", 0) >= 2:
            save_points(data)
            await interaction.response.edit_message(
                content="❌ استخدمت لعبة **تصيب أو تخيب** مرتين اليوم. ارجع بكرا عشان تلعب من جديد.",
                embed=None,
                view=None
            )
            return

        if user["coins"] < price:
            await interaction.response.edit_message(
                content=f"❌ رصيدك ما يكفي.\nمعك **{user['coins']} {COIN_EMOJI}**",
                embed=None,
                view=None
            )
            return

        user["coins"] -= price

        if self.item_key == "gamble":
            user["gamble_uses"] = user.get("gamble_uses", 0) + 1
            user["gamble_day"] = get_today()

        result = random.choice(["lose", "win", "big_win", "jackpot"])

        if result == "lose":
            reward = 0
            result_text = "❌ خسرت وما رجع لك شيء."
        elif result == "win":
            reward = random.randint(300, 600)
            user["coins"] += reward
            result_text = f"✅ ربحت **{reward} {COIN_EMOJI}**"
        elif result == "big_win":
            reward = random.randint(700, 1200)
            user["coins"] += reward
            result_text = f"🔥 فوز قوي! ربحت **{reward} {COIN_EMOJI}**"
        else:
            reward = random.randint(1500, 3000)
            user["coins"] += reward
            result_text = f"💎 جاكبوت! ربحت **{reward} {COIN_EMOJI}**"

        save_points(data)

        await interaction.response.edit_message(
            content=(
                f"🎲 **تصيب أو تخيب**\n\n"
                f"{result_text}\n"
                f"رصيدك الآن: **{user['coins']} {COIN_EMOJI}**\n"
                f"محاولاتك اليوم: **{user.get('gamble_uses', 0)}/2**"
            ),
            embed=None,
            view=None
        )

    @discord.ui.button(label="إلغاء", emoji="❌", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("هذا الطلب مو لك.", ephemeral=True)
            return

        await interaction.response.edit_message(
            content="تم إلغاء عملية الشراء.",
            embed=None,
            view=None
        )


class ShopSelect(discord.ui.Select):
    def __init__(self):
        options = []

        for key, item in SHOP_ITEMS.items():
            options.append(
                discord.SelectOption(
                    label=f"{item['name']} - {item['price']}",
                    description=item["desc"],
                    value=key
                )
            )

        super().__init__(
            placeholder="🛒 اختر عنصر من المتجر",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if is_event_active():
            await interaction.response.send_message("❌ المتجر متوقف أثناء الفعالية، ونقاط الفعالية ما تنصرف.", ephemeral=True)
            return

        item_key = self.values[0]
        item = SHOP_ITEMS[item_key]

        data = load_points()
        user = get_user_data(data, interaction.user.id)

        balance = user["coins"]
        after = balance - item["price"]

        after_text = f"{after} {COIN_EMOJI}" if after >= 0 else "رصيدك لا يكفي"

        embed = discord.Embed(
            title="🛒 تأكيد الشراء",
            description=(
                f"📦 **المنتج:** {item['name']}\n"
                f"📝 **الوصف:** {item['desc']}\n\n"
                f"💰 **السعر:** {item['price']} {COIN_EMOJI}\n"
                f"💳 **رصيدك الحالي:** {balance} {COIN_EMOJI}\n"
                f"📉 **رصيدك بعد الشراء:** {after_text}"
            ),
            color=0xCE44DB
        )

        await interaction.response.send_message(
            embed=embed,
            view=ConfirmPurchaseView(interaction.user.id, item_key),
            ephemeral=True
        )


class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ShopSelect())


class MainShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="المتجر", emoji="🛒", style=discord.ButtonStyle.primary)
    async def shop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛒 متجر الأعضاء | Cuten Zone Market",
            description=(
                f"استبدل {COIN_EMOJI} **Cute Coin** بمميزات حصرية داخل السيرفر!\n\n"
                f"🎨 **لون خاص** - 2000 {COIN_EMOJI}\n"
                f"🏷️ **رتبة خاصة** - 5000 {COIN_EMOJI}\n"
                f"👥 **كلان خاص** - 15000 {COIN_EMOJI}\n"
                f"🎲 **تصيب أو تخيب** - 200 {COIN_EMOJI}"
            ),
            color=0xCE44DB
        )

        await interaction.response.send_message(
            embed=embed,
            view=ShopView(),
            ephemeral=True
        )


@bot.tree.command(name="متجر", description="إرسال لوحة متجر Cute Coin")
async def متجر(interaction: discord.Interaction):

    if not await require_commands_channel_interaction(interaction):
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ هذا الأمر للإدارة فقط.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🛒 متجر الأعضاء",
        description=(
            f"استبدل {COIN_EMOJI} **Cute Coin** بمميزات حصرية داخل كيوتن!\n\n"
            "اضغط زر المتجر بالأسفل لعرض المنتجات."
        ),
        color=0xCE44DB
    )

    embed.set_image(url=SHOP_IMAGE_URL)
    embed.set_footer(text="Cuten Zone Market")

    await interaction.response.send_message(embed=embed, view=MainShopView())



@bot.tree.command(name="تعويض_الجميع", description="إعطاء Cute Coin لكل أعضاء السيرفر كتعويض")
@discord.app_commands.describe(
    الكمية="كمية الكوينز لكل عضو",
    السبب="سبب التعويض، اختياري"
)
async def تعويض_الجميع(
    interaction: discord.Interaction,
    الكمية: int,
    السبب: str = "تعويض من الإدارة"
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ هذا الأمر للإدارة فقط.",
            ephemeral=True
        )
        return

    if الكمية <= 0:
        await interaction.response.send_message(
            "❌ لازم الكمية تكون أكبر من صفر.",
            ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True)

    data = load_points()
    count = 0

    for member in interaction.guild.members:
        if member.bot:
            continue

        user = get_user_data(data, member.id)
        user["coins"] += الكمية
        count += 1

    save_points(data)

    embed = discord.Embed(
        title="🎁 تعويض جماعي",
        description=(
            f"تم توزيع **{الكمية} Cute Coin {COIN_EMOJI}** لكل عضو.\n"
            f"👥 عدد المستفيدين: **{count}**\n"
            f"📝 السبب: {السبب}"
        ),
        color=0x57F287
    )

    await interaction.followup.send(
        content="@everyone",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(everyone=True)
    )


@bot.command(name="تعويض_الجميع")
async def تعويض_الجميع_امر(ctx, الكمية: int = None, *, السبب: str = "تعويض من الإدارة"):
    if not ctx.author.guild_permissions.administrator:
        await ctx.reply("❌ هذا الأمر للإدارة فقط.", mention_author=False)
        return

    if الكمية is None or الكمية <= 0:
        await ctx.reply("❌ اكتب الأمر كذا: `!تعويض_الجميع 1000`", mention_author=False)
        return

    data = load_points()
    count = 0

    for member in ctx.guild.members:
        if member.bot:
            continue

        user = get_user_data(data, member.id)
        user["coins"] += الكمية
        count += 1

    save_points(data)

    embed = discord.Embed(
        title="🎁 تعويض جماعي",
        description=(
            f"تم توزيع **{الكمية} Cute Coin {COIN_EMOJI}** لكل عضو.\n"
            f"👥 عدد المستفيدين: **{count}**\n"
            f"📝 السبب: {السبب}"
        ),
        color=0x57F287
    )

    await ctx.send(
        content="@everyone",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(everyone=True)
    )

@bot.tree.command(name="اعطاء_كوينز", description="إعطاء Cute Coin لعضو")
@discord.app_commands.describe(
    العضو="العضو المراد إعطاؤه الكوينز",
    الكمية="كمية الكوينز"
)
async def اعطاء_كوينز(
    interaction: discord.Interaction,
    العضو: discord.Member,
    الكمية: int
):

    if not await require_commands_channel_interaction(interaction):
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ هذا الأمر للإدارة فقط.",
            ephemeral=True
        )
        return

    if الكمية <= 0:
        await interaction.response.send_message(
            "❌ لازم الكمية تكون أكبر من صفر.",
            ephemeral=True
        )
        return

    data = load_points()
    user = get_user_data(data, العضو.id)

    user["coins"] += الكمية

    save_points(data)

    embed = discord.Embed(
        title="💰 تم إعطاء كوينز",
        description=(
            f"👤 العضو: {العضو.mention}\n"
            f"➕ الكمية: {الكمية} {COIN_EMOJI}\n"
            f"💳 الرصيد الجديد: {user['coins']} {COIN_EMOJI}"
        ),
        color=0x57F287
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="سحب_كوينز", description="سحب Cute Coin من عضو")
@discord.app_commands.describe(
    العضو="العضو المراد السحب منه",
    الكمية="كمية الكوينز"
)
async def سحب_كوينز(
    interaction: discord.Interaction,
    العضو: discord.Member,
    الكمية: int
):

    if not await require_commands_channel_interaction(interaction):
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ هذا الأمر للإدارة فقط.",
            ephemeral=True
        )
        return

    if الكمية <= 0:
        await interaction.response.send_message(
            "❌ لازم الكمية تكون أكبر من صفر.",
            ephemeral=True
        )
        return

    data = load_points()
    user = get_user_data(data, العضو.id)

    if user["coins"] < الكمية:
        await interaction.response.send_message(
            f"❌ رصيد العضو ما يكفي.\nرصيده الحالي: **{user['coins']} {COIN_EMOJI}**",
            ephemeral=True
        )
        return

    user["coins"] -= الكمية
    save_points(data)

    embed = discord.Embed(
        title="💸 تم سحب كوينز",
        description=(
            f"👤 العضو: {العضو.mention}\n"
            f"➖ الكمية: {الكمية} {COIN_EMOJI}\n"
            f"💳 الرصيد الجديد: {user['coins']} {COIN_EMOJI}"
        ),
        color=0xED4245
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="تحويل", description="تحويل Cute Coin لعضو آخر")
@discord.app_commands.describe(
    العضو="العضو اللي تبي تحول له",
    الكمية="كمية الكوينز"
)
async def تحويل(
    interaction: discord.Interaction,
    العضو: discord.Member,
    الكمية: int
):

    if not await require_commands_channel_interaction(interaction):
        return

    if is_event_active():
        await interaction.response.send_message(
            "❌ التحويل متوقف أثناء الفعالية حتى تظل نقاط المنافسة عادلة.",
            ephemeral=True
        )
        return

    if العضو.bot:
        await interaction.response.send_message(
            "❌ ما تقدر تحول لبوت.",
            ephemeral=True
        )
        return

    if العضو.id == interaction.user.id:
        await interaction.response.send_message(
            "❌ ما تقدر تحول لنفسك.",
            ephemeral=True
        )
        return

    if الكمية <= 0:
        await interaction.response.send_message(
            "❌ لازم الكمية تكون أكبر من صفر.",
            ephemeral=True
        )
        return

    data = load_points()
    sender = get_user_data(data, interaction.user.id)
    receiver = get_user_data(data, العضو.id)

    if sender["coins"] < الكمية:
        await interaction.response.send_message(
            f"❌ رصيدك ما يكفي.\nرصيدك الحالي: **{sender['coins']} {COIN_EMOJI}**",
            ephemeral=True
        )
        return

    sender["coins"] -= الكمية
    receiver["coins"] += الكمية
    save_points(data)

    embed = discord.Embed(
        title="💸 تحويل Cute Coin",
        description=(
            f"✅ تم تحويل **{الكمية} {COIN_EMOJI}**\n\n"
            f"من: {interaction.user.mention}\n"
            f"إلى: {العضو.mention}"
        ),
        color=0xCE44DB
    )

    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="توب_الكوينز", description="عرض أغنى أعضاء السيرفر")
async def توب_الكوينز(interaction: discord.Interaction):

    if not await require_commands_channel_interaction(interaction):
        return

    data = load_points()
    event_active = is_event_active()
    balance_key = "event_coins" if event_active else "coins"

    members_data = []

    for user_id, user_data in data.items():
        member = interaction.guild.get_member(int(user_id))

        if member:
            members_data.append(
                (member, user_data.get(balance_key, 0))
            )

    members_data.sort(key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="🏆 توب الفعالية" if event_active else "🏆 لوحة أثرياء كيوتن",
        description="أعلى الأعضاء في نقاط الفعالية 🎉" if event_active else "أغنى أعضاء السيرفر حالياً 💰",
        color=0xCE44DB
    )

    medals = ["🥇", "🥈", "🥉"]

    text = ""

    for i, (member, coins) in enumerate(members_data[:10]):

        if i < 3:
            rank = medals[i]
        else:
            rank = f"`#{i+1}`"

        text += (
            f"{rank} {member.mention}\n"
            f"**{coins:,}** {COIN_EMOJI}\n\n"
        )

    if not text:
        text = "لا يوجد بيانات."

    embed.add_field(
        name="📊 الترتيب",
        value=text,
        inline=False
    )

    embed.set_footer(
        text=f"عدد الأعضاء المصنفين: {len(members_data)}"
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="بدء_الفعالية", description="بدء فعالية النقاط المنفصلة وتصفير نقاط الفعالية")
async def بدء_الفعالية(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر للإدارة فقط.", ephemeral=True)
        return

    state = load_event_state()
    if state.get("active"):
        await interaction.response.send_message("❌ الفعالية شغالة بالفعل.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    data = load_points()
    count = 0
    now = time.time()

    for member in interaction.guild.members:
        if member.bot:
            continue
        user = get_user_data(data, member.id)
        user["event_coins"] = 0
        user["task_reset_at"] = now
        user["tasks"] = {"messages": 0, "photo": False, "reactions": 0, "games": 0, "voice": 0}
        user["completed_tasks"] = []
        count += 1

    save_points(data)
    save_event_state({"active": True, "started_at": datetime.now().isoformat()})

    embed = discord.Embed(
        title="🎉 بدأت فعالية Cute Coin",
        description=(
            "تم تصفير **نقاط الفعالية فقط** لجميع الأعضاء.\n"
            "الأرصدة الأصلية محفوظة ولن تتغير.\n"
            "المهام تتجدد كل **ساعتين**، والمتجر والتحويل متوقفان أثناء الفعالية.\n\n"
            f"👥 تم تجهيز **{count}** عضو."
        ),
        color=0xF8BBD0
    )
    await interaction.followup.send(content="@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))


@bot.tree.command(name="انهاء_الفعالية", description="إنهاء الفعالية وحذف نقاطها دون لمس الرصيد الأصلي")
async def انهاء_الفعالية(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر للإدارة فقط.", ephemeral=True)
        return

    state = load_event_state()
    if not state.get("active"):
        await interaction.response.send_message("❌ ما فيه فعالية شغالة حالياً.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    data = load_points()
    ranking = []

    for user_id, user_data in data.items():
        member = interaction.guild.get_member(int(user_id))
        points = int(user_data.get("event_coins", 0))
        if member and not member.bot:
            ranking.append((member, points))

    ranking.sort(key=lambda item: item[1], reverse=True)
    top_five = ranking[:5]
    result_text = ""
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for index, (member, points) in enumerate(top_five):
        result_text += f"{medals[index]} {member.mention} — **{points:,}** نقطة\n"
    if not result_text:
        result_text = "لا توجد نتائج."

    # بعد حفظ النتائج في الرسالة نحذف نقاط الفعالية فقط.
    for user_data in data.values():
        user_data["event_coins"] = 0

    save_points(data)
    save_event_state({"active": False, "started_at": None})

    embed = discord.Embed(
        title="🏁 انتهت فعالية Cute Coin",
        description=(
            f"**النتائج النهائية:**\n{result_text}\n"
            "تم حذف جميع نقاط الفعالية، والأرصدة الأصلية بقيت كما كانت بدون أي إضافة أو خصم."
        ),
        color=0x57F287
    )
    await interaction.followup.send(content="@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))


@bot.tree.command(name="حالة_الفعالية", description="عرض حالة فعالية النقاط")
async def حالة_الفعالية(interaction: discord.Interaction):
    if not await require_commands_channel_interaction(interaction):
        return

    state = load_event_state()
    if state.get("active"):
        text = "✅ الفعالية شغالة الآن.\nالمهام تتجدد كل ساعتين، والرصيد الأصلي محفوظ."
        color = 0x57F287
    else:
        text = "⛔ لا توجد فعالية شغالة حالياً."
        color = 0xED4245

    await interaction.response.send_message(embed=discord.Embed(title="🎉 حالة الفعالية", description=text, color=color))


bot.run(os.getenv("TOKEN"))