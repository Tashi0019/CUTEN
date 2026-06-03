import discord
from discord.ext import commands

from keep_alive import keep_alive

keep_alive()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}!")


@bot.command()
async def setup(ctx):

    embed = discord.Embed(
        title="💎cuten",
        description="أهلًا فيك في كيوتن\nاستخدم الأزرار بالأسفل للتعرف على سيرفرنا ومميزاته",
        color=0xb7c9ff
    )

    embed.set_image(
        url="https://i.imgur.com/bDKuCUM.png"
    )

    embed.set_thumbnail(
        url="https://i.imgur.com/eRsBDQQ.jpeg"
    )

    view = discord.ui.View(timeout=None)

    # ---------------- نبذة عنا ----------------

    about_button = discord.ui.Button(
        label="نبذة عنا 📖",
        style=discord.ButtonStyle.secondary
    )

    async def about_callback(interaction):

        await interaction.response.send_message(
            (
                "> 🎀 **سيرفر كيوتن | Cuten 🎀**\n"
                "> •———————• 🧸 •———————•\n"
                "> مرحباً بكم في عالمنا.. مكاننا مو مجرد سيرفر، هو المساحة الدافئة اللي تجمعنا كل يوم ✨ هنا صممنا مجتمع مريح لكل شخص حاب يفضفض، يسولف، أو يشارك يومياته بكل عفوية.\n"
                "> 🪐 **ليش إحنا هنا؟**\n"
                "> 💬 **سوالف وراحة:** مكانك المثالي للاسترخاء والفضفضة بعد يوم طويل.\n"
                "> 🤝 **احترام متبادل:** أساسنا هو التقدير والود بين الكل، بدون رسميات وبكل احترام.\n"
                "> ☕ **أجواء رايقة:** شاركنا اهتماماتك، صورك، أو مجرد وجودك اللطيف معنا.\n"
                "> •———————• 🤍 •———————•\n"
                "> **خذ لك كوب قهوة ونوّرنا بالشات.. مساحتك الآمنة بانتظارك! 💖**\n"
            ),
            ephemeral=True
        )

    about_button.callback = about_callback
    view.add_item(about_button)

    # ---------------- القوانين ----------------

    rules_button = discord.ui.Button(
        label="القوانين📜",
        style=discord.ButtonStyle.secondary
    )

    async def rules_callback(interaction):

        await interaction.response.send_message(
            "📜 **قوانين مجتمع كيوتن | Cuten Rules** 📜\n•———————• 🧸 •———————•\nيا هلا فيكم بنور السيرفر! ✨\nعشان تظل مساحتنا آمنة، مريحة، ومليانة طاقة إيجابية للكل، حطينا هالقوانين البسيطة. التزامك فيها يعكس ذوقك ولطفك، ويساعدنا نحافظ على بيئة محترمة تجمعنا على الخير والسوالف الحلوة.\n**الرجاء الاطلاع على البنود أدناه والالتزام بها لضمان وقت ممتع للجميع: 👇**\nhttps://discord.com/channels/1506043098285867188/1506045317555163166/1506708096687538308",
            ephemeral=True
        )

    rules_button.callback = rules_callback
    view.add_item(rules_button)

    # ---------------- دعوة السيرفر ----------------

    invite_button = discord.ui.Button(
        label="دعوة سيرفر 📩",
        style=discord.ButtonStyle.secondary
    )

    async def invite_callback(interaction):

        await interaction.response.send_message(
            "🔗 **رابط دعوة سيرفر كيوتن | Cuten Invite Link** 🔗\n•———————• 🧸 •———————•\nيا هلا فيكم بنور السيرفر! ✨\nإذا حبيتوا تنضموا لعائلتنا الحلوة، تفضلوا الرابط أدناه وانضموا لرحلتنا الممتعة في عالم كيوتن: 👇\nhttps://discord.gg/cuten",
            ephemeral=True
        )

    invite_button.callback = invite_callback
    view.add_item(invite_button)

    # ---------------- السيرفرات ----------------

    server_button = discord.ui.Button(
        label="سيرفراتنا 🌐",
        style=discord.ButtonStyle.secondary
    )

    async def server_callback(interaction):
        content = (
            "🤝 شركاء النجاح | Our Partners 🤝\n"
            "•———————• 🧸 •———————•\n\n"

            "يا هلا والله! ✨\n"
            "هنا نعتز ونفتخر بصداقتنا مع سيرفرات ومجتمعات رهيبة "
            "تشاركنا نفس الشغف والروح اللطيفة.\n"
            "هالمساحة مخصصة لدعم حلفائنا اللي نعتبرهم جزء من عائلتنا الكبيرة 💖\n\n"

            "خذوا لكم لفة ونوّروهم في سيرفراتهم 👇\n\n"

                        " السيرفر الاول"
            "https://discord.gg/ang-els\n\n"
                           
                           
                    
            " السيرفر الثاني"
            "https://discord.gg/SWGnQh3rdV\n\n"
        )

        await interaction.response.send_message(content, ephemeral=True)


    server_button.callback = server_callback
    view.add_item(server_button)

    # ---------------- البوست ----------------

    boost_button = discord.ui.Button(
        label="مميزات البوست🚀",
        style=discord.ButtonStyle.secondary
    )

    async def boost_callback(interaction):

        await interaction.response.send_message(
      (
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
            "> **شكراً لكل شخص يدعمنا ويساهم في رسم ابتسامة على مجتمعنا! 🍵**\n"
        ),
            ephemeral=True)
        

    boost_button.callback = boost_callback
    view.add_item(boost_button)

    # ---------------- اللفلات ----------------

    levels_button = discord.ui.Button(
        label="مميزات اللفل📈",
        style=discord.ButtonStyle.secondary
    )

    async def levels_callback(interaction):

        await interaction.response.send_message(
              (
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
        "> **شدّوا الحيل في الشات ونورونا بسوالفكم الحلوة عشان توصلون لأعلى اللفلات! 🫂✨**"
    ),
            ephemeral=True
        )

    levels_button.callback = levels_callback
    view.add_item(levels_button)

    # ---------------- المساعدة ----------------

    help_button = discord.ui.Button(
        label="مساعدة ❓",
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

    await ctx.send(embed=embed, view=view)

tag_button = discord.ui.Button(
    label="مميزات التاق:126: ",
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
        "شكراً لأنكم تخلون عالمنا ألطف وأجمل بوجودكم ودعمكم المستمر لينا ♡\n",
        ephemeral=True
    )

import os

bot.run(os.getenv("TOKEN"))
