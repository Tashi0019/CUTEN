import os
import json
import random
from datetime import datetime
import discord
from discord.ext import commands
from keep_alive import keep_alive

keep_alive()

SUGGESTION_CHANNEL_ID = 1506046070533128473
DISCUSSION_CHANNEL_ID = 1508502264703090779
POINTS_FILE = "points.json"
DAILY_MESSAGES_GOAL = 30
DAILY_MESSAGES_REWARD = 20

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged on as {bot.user}!")


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


def add_message_progress(user_id):
    data = load_points()
    user_id = str(user_id)
    today = get_today()

    if user_id not in data:
        data[user_id] = {
            "points": 0,
            "daily_messages": 0,
            "last_day": today,
            "daily_done": False
        }

    if data[user_id]["last_day"] != today:
        data[user_id]["daily_messages"] = 0
        data[user_id]["last_day"] = today
        data[user_id]["daily_done"] = False

    if not data[user_id]["daily_done"]:
        data[user_id]["daily_messages"] += 1

        if data[user_id]["daily_messages"] >= DAILY_MESSAGES_GOAL:
            data[user_id]["points"] += DAILY_MESSAGES_REWARD
            data[user_id]["daily_done"] = True
            save_points(data)
            return True

    save_points(data)
    return False


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

        await message.reply(embed=embed, mention_author=False)
        return

    if "تاشيرو" in message.content.lower():
        replies = [
            "اذا ما رديت عليك اعرف اني مشغول او انك غثيث !",
            "تم استدعاء تاشيرو، انتظر لين يفك الزحمة.",
            "وصلت الرسالة، الباقي على مزاج تاشيرو."
        ]

        await message.reply(
            f"{random.choice(replies)}\n\n<@1044310877429575682>",
            mention_author=False
        )

    if "نيرف" in message.content.lower():
        replies = [
            "اذ شفت رسالتك برد عليك يا كيوتن ! <a:noih10:1509687143809941515> :>",
            "نيرف استلم البلاغ، انتظر الرد. <a:02_nekopat:1512152074262024355> :>",
            "تم منشن نيرف، عاد الله يعينك على الرد. <a:AA_CatBoy_Hug:1509700761431441478>:>"
        ]

        await message.reply(
            f"{random.choice(replies)}\n\n<@944222907385643050>",
            mention_author=False
        )

    if message.channel.id == SUGGESTION_CHANNEL_ID:
        try:
            await message.delete()
        except:
            pass

        await message.channel.send(
            f"📮 {message.author.mention} لإرسال اقتراح جديد استخدم `/اقتراح` ثم اختر نوع الاقتراح.",
            delete_after=8
        )
        return

    completed = add_message_progress(message.author.id)

    if completed:
        await message.channel.send(
            f"{message.author.mention} أنجزت المهمة اليومية!\n"
            f"حصلت على {DAILY_MESSAGES_REWARD} نقطة"
        )

    await bot.process_commands(message)


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

    embed.set_image(url="https://i.imgur.com/bDKuCUM.png")
    embed.set_thumbnail(url="https://i.imgur.com/eRsBDQQ.jpeg")

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
    await interaction.response.send_modal(SuggestionModal(النوع.value))
@bot.tree.command(name="نقاطي", description="عرض نقاطك")
async def نقاطي(interaction: discord.Interaction):
    data = load_points()
    user_id = str(interaction.user.id)

    points = data.get(user_id, {}).get("points", 0)
    messages = data.get(user_id, {}).get("daily_messages", 0)
    done = data.get(user_id, {}).get("daily_done", False)

    status = "مكتملة" if done else f"{messages}/{DAILY_MESSAGES_GOAL}"

    await interaction.response.send_message(
        f"نقاطك: **{points}**\n"
        f"مهمة الرسائل اليومية: **{status}**",
        ephemeral=True
    )


@bot.tree.command(name="المهام", description="عرض المهام اليومية")
async def المهام(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"المهام اليومية:\n"
        f"أرسل {DAILY_MESSAGES_GOAL} رسالة وخذ {DAILY_MESSAGES_REWARD} نقطة",
        ephemeral=True
    )


@bot.tree.command(name="توب_النقاط", description="عرض أكثر الأعضاء نقاطًا")
async def توب_النقاط(interaction: discord.Interaction):
    data = load_points()

    sorted_users = sorted(
        data.items(),
        key=lambda item: item[1].get("points", 0),
        reverse=True
    )[:10]

    if not sorted_users:
        await interaction.response.send_message("ما فيه نقاط للحين.", ephemeral=True)
        return

    text = ""

    for index, (user_id, info) in enumerate(sorted_users, start=1):
        text += f"{index}. <@{user_id}> — **{info.get('points', 0)}** نقطة\n"

    await interaction.response.send_message(
        f"توب النقاط:\n{text}"
    )

bot.run(os.getenv("TOKEN"))
