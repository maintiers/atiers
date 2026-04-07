import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv  # Добавьте эту строку

# Загружаем переменные из .env файла
load_dotenv()

# ========== ТОКЕН ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ==========
TOKEN = os.getenv("DISCORD_BOT_TOKEN2")
if TOKEN is None:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    exit(1)

# ========== НАСТРОЙКИ ==========
GUILD_ID = None
QUALIFIED_COOLDOWN_DAYS = 7
HIGH_COOLDOWN_DAYS = 14
MIN_TICKET_DAYS = 3

# Файлы для хранения данных
QUEUE_FILE = "queue.json"
ACTIVE_TESTERS_FILE = "active_testers.json"
TICKETS_FILE = "tickets.json"
TESTER_STATS_FILE = "tester_stats.json"
QUALIFIED_COOLDOWNS_FILE = "qualified_cooldowns.json"
HIGH_COOLDOWNS_FILE = "high_cooldowns.json"
SUPPORT_TICKETS_FILE = "support_tickets.json"
STAFF_APPLICATIONS_FILE = "staff_applications.json"
MESSAGE_IDS_FILE = "message_ids.json"


def load_data(file_name, default=None):
    if default is None:
        default = [] if file_name == QUEUE_FILE else {}

    if os.path.exists(file_name):
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default


def save_data(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ========== ЗАГРУЗКА ДАННЫХ ==========
# Загружаем очередь как список
_raw_queue = load_data(QUEUE_FILE, [])
if isinstance(_raw_queue, dict):
    # Если старый формат (словарь), конвертируем в список
    queue_data = []
    for guild_id, users in _raw_queue.items():
        queue_data.extend(users)
else:
    queue_data = _raw_queue if isinstance(_raw_queue, list) else []

# Загружаем остальные данные
active_testers = load_data(ACTIVE_TESTERS_FILE, {})
tickets_data = load_data(TICKETS_FILE, {})
tester_stats = load_data(TESTER_STATS_FILE, {})
qualified_cooldowns = load_data(QUALIFIED_COOLDOWNS_FILE, {})
high_cooldowns = load_data(HIGH_COOLDOWNS_FILE, {})
user_data = load_data("user_data.json", {})
support_tickets = load_data(SUPPORT_TICKETS_FILE, {})
staff_applications = load_data(STAFF_APPLICATIONS_FILE, {})
message_ids = load_data(MESSAGE_IDS_FILE, {})


# ========== ФУНКЦИИ СОХРАНЕНИЯ ==========
def save_queue():
    save_data(QUEUE_FILE, queue_data)


def save_active_testers():
    save_data(ACTIVE_TESTERS_FILE, active_testers)


def save_tickets():
    save_data(TICKETS_FILE, tickets_data)


def save_tester_stats():
    save_data(TESTER_STATS_FILE, tester_stats)


def save_qualified_cooldowns():
    save_data(QUALIFIED_COOLDOWNS_FILE, qualified_cooldowns)


def save_high_cooldowns():
    save_data(HIGH_COOLDOWNS_FILE, high_cooldowns)


def save_user_data():
    save_data("user_data.json", user_data)


def save_support_tickets():
    save_data(SUPPORT_TICKETS_FILE, support_tickets)


def save_staff_applications():
    save_data(STAFF_APPLICATIONS_FILE, staff_applications)


def save_message_ids():
    save_data(MESSAGE_IDS_FILE, message_ids)


# ========== НАСТРОЙКИ РОЛЕЙ И КАНАЛОВ ==========
ROLE_WHITELIST = "WhiteList"
ROLE_TESTER = "Verified Tester"
ROLE_SENIOR_TESTER = "Senior Tester"
ROLE_MEMBER = "Участник"
ROLE_MODERATOR = "Moderator"
ROLE_ADMINISTRATOR = "Administrator"
ROLE_HT2 = "HT2"
ROLE_LT2 = "LT2"
ROLE_HT3 = "HT3"
ROLE_LT3 = "LT3"
ROLE_HT4 = "HT4"
ROLE_LT4 = "LT4"
ROLE_HT5 = "HT5"
ROLE_LT5 = "LT5"

# Порядок тиров
TIER_ORDER = ["LT5", "HT5", "LT4", "HT4", "LT3", "HT3", "LT2", "HT2"]
TIER_ROLES = [
    ROLE_LT5,
    ROLE_HT5,
    ROLE_LT4,
    ROLE_HT4,
    ROLE_LT3,
    ROLE_HT3,
    ROLE_LT2,
    ROLE_HT2,
]

CHANNEL_QUEUE = "🕐・очередь"
CHANNEL_TESTING = "📌・тестирование"
CHANNEL_TESTER_COMMANDS = "verified-command"
CHANNEL_SENIOR_COMMANDS = "senior-command"
CHANNEL_QUALIFIED_RESULTS = "🥈・результаты"
CHANNEL_HIGH_RESULTS = "🏆・высокие-результаты"
CHANNEL_TESTER_MONTH = "⚔️・лидербодр"
CHANNEL_VERIFICATION = "✔️・верификация"
CHANNEL_SUPPORT = "📁・поддержка"
CHANNEL_STAFF = "👥・стафф"
CHANNEL_STAFF_APPLICATIONS = "👥・заявки-стафф"

QUALIFIED_TIERS = ["LT5", "HT5", "LT4", "HT4", "LT3"]
HIGH_TIERS = ["HT3", "LT2", "HT2"]

# Список серверов
SERVERS = [
    {"name": "msl.su", "flag": "🇷🇺", "address": "msl.su"},
    {
        "name": "femboymc.joinserver.ru",
        "flag": "🇷🇺",
        "address": "femboymc.joinserver.ru",
    },
    {"name": "tavix.su", "flag": "🇷🇺", "address": "tavix.su"},
    {"name": "mc.aormio.ru", "flag": "🇷🇺", "address": "mc.aormio.ru"},
    {"name": "worst-practice.ru", "flag": "🇷🇺", "address": "worst-practice.ru"},
]

# Роли для отслеживания в канале стафа
STAFF_ROLES = [ROLE_ADMINISTRATOR, ROLE_MODERATOR, ROLE_SENIOR_TESTER, ROLE_TESTER]

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# ========== ФУНКЦИИ ==========
def get_tier_index(tier_name):
    if tier_name in TIER_ORDER:
        return TIER_ORDER.index(tier_name)
    return -1


async def remove_lower_tiers(member, new_tier):
    new_idx = get_tier_index(new_tier)
    if new_idx == -1:
        return

    for tier_role_name in TIER_ROLES:
        tier_idx = get_tier_index(tier_role_name)
        if tier_idx != -1 and tier_idx < new_idx:
            role = discord.utils.get(member.guild.roles, name=tier_role_name)
            if role and role in member.roles:
                try:
                    await member.remove_roles(role)
                except:
                    pass


def has_lt3_role(member):
    """Проверяет наличие роли LT3 или выше (HT3, LT2, HT2)"""
    allowed_roles = [ROLE_LT3, ROLE_HT3, ROLE_LT2, ROLE_HT2]
    for role_name in allowed_roles:
        role = discord.utils.get(member.roles, name=role_name)
        if role:
            return True
    return False


def has_high_tier(member):
    """Проверяет наличие тира выше LT3 (HT3, LT2, HT2)"""
    high_tiers = ["HT3", "LT2", "HT2"]
    for tier in high_tiers:
        role = discord.utils.get(member.roles, name=tier)
        if role and role in member.roles:
            return True
    return False


def can_take_qualified_test(user_id):
    user = None
    for guild in bot.guilds:
        user = guild.get_member(int(user_id))
        if user:
            break
    if user and has_lt3_role(user):
        return True, None

    if user_id not in qualified_cooldowns:
        return True, None

    last_test = datetime.fromisoformat(qualified_cooldowns[user_id])
    if datetime.now() - last_test < timedelta(days=QUALIFIED_COOLDOWN_DAYS):
        next_available = last_test + timedelta(days=QUALIFIED_COOLDOWN_DAYS)
        return False, next_available
    return True, None


def set_qualified_cooldown(user_id):
    qualified_cooldowns[user_id] = datetime.now().isoformat()
    save_qualified_cooldowns()


def set_high_cooldown(user_id):
    high_cooldowns[user_id] = datetime.now().isoformat()
    save_high_cooldowns()


async def get_channel(guild, channel_name):
    for channel in guild.text_channels:
        if channel.name == channel_name:
            return channel
    return None


async def get_role(guild, role_name):
    for role in guild.roles:
        if role.name == role_name:
            return role
    return None


async def find_bot_message(channel, limit=100):
    """Ищет последнее сообщение бота в канале по истории."""
    try:
        async for msg in channel.history(limit=limit):
            if msg.author == bot.user:
                return msg
    except Exception:
        pass
    return None


async def edit_or_create_message(
    channel, guild_id, key, embed, view=None, auto_create=True
):
    """
    Пытается найти и отредактировать существующее сообщение бота.
    Порядок: сохранённый ID → история канала → создать новое (если auto_create=True).
    Сохраняет ID найденного/нового сообщения в message_ids.json.
    """
    guild_id_str = str(guild_id)
    saved_id = message_ids.get(guild_id_str, {}).get(key)

    async def _save_id(msg_id):
        if guild_id_str not in message_ids:
            message_ids[guild_id_str] = {}
        message_ids[guild_id_str][key] = msg_id
        save_message_ids()

    async def _do_edit(msg):
        if view is not None:
            await msg.edit(embed=embed, view=view)
        else:
            await msg.edit(embed=embed)

    # 1. Пробуем по сохранённому ID
    if saved_id:
        try:
            msg = await channel.fetch_message(saved_id)
            await _do_edit(msg)
            return msg
        except Exception:
            pass

    # 2. Ищем по истории канала
    hist_msg = await find_bot_message(channel)
    if hist_msg:
        try:
            await _do_edit(hist_msg)
            await _save_id(hist_msg.id)
            return hist_msg
        except Exception:
            pass

    # 3. Создаём новое сообщение (только если разрешено)
    if not auto_create:
        return None

    try:
        if view is not None:
            msg = await channel.send(embed=embed, view=view)
        else:
            msg = await channel.send(embed=embed)
        await _save_id(msg.id)
        return msg
    except Exception as e:
        print(f"[!] Не удалось создать сообщение в {channel.name}: {e}")
        return None


async def update_queue_display(guild=None):
    guilds = [guild] if guild else bot.guilds
    for guild in guilds:
        testing_channel = await get_channel(guild, CHANNEL_TESTING)
        if not testing_channel:
            continue

        embed = discord.Embed(
            title="📋 **СИСТЕМА ТЕСТИРОВАНИЯ**", color=discord.Color.blue()
        )

        # queue_data теперь список, а не словарь
        guild_queue = queue_data  # Просто список пользователей

        if not guild_queue:
            embed.add_field(
                name="📋 ОЧЕРЕДЬ", value="В очереди никого нет", inline=False
            )
        else:
            queue_list = []
            for i, user_id in enumerate(guild_queue, 1):
                user = guild.get_member(int(user_id))
                if user:
                    queue_list.append(f"{i}. {user.mention}")
                else:
                    queue_list.append(f"{i}. <@{user_id}> (не на сервере)")
            embed.add_field(
                name="📋 ОЧЕРЕДЬ", value="\n".join(queue_list), inline=False
            )
            embed.set_footer(text=f"Всего в очереди: {len(guild_queue)}")

        guild_testers = active_testers.get(str(guild.id), [])
        if guild_testers:
            testers_list = []
            for user_id in guild_testers:
                user = guild.get_member(int(user_id))
                if user:
                    testers_list.append(f"• {user.mention}")
            embed.add_field(
                name="🟢 АКТИВНЫЕ ТЕСТЕРЫ",
                value="\n".join(testers_list) if testers_list else "Нет",
                inline=False,
            )
        else:
            embed.add_field(
                name="🟢 АКТИВНЫЕ ТЕСТЕРЫ", value="Нет активных тестеров", inline=False
            )

        await edit_or_create_message(
            testing_channel, guild.id, "testing_message_id", embed
        )


async def update_tester_month_display(guild=None):
    guilds = [guild] if guild else bot.guilds
    for guild in guilds:
        month_channel = await get_channel(guild, CHANNEL_TESTER_MONTH)
        if not month_channel:
            continue

        if not tester_stats:
            embed = discord.Embed(
                title="🏆 **ТИР-ТЕСТЕР МЕСЯЦА**",
                description="Пока нет проведённых тестов",
                color=discord.Color.gold(),
            )
        else:
            sorted_testers = sorted(
                tester_stats.items(), key=lambda x: x[1].get("count", 0), reverse=True
            )

            testers_list = []
            for i, (user_id, stats) in enumerate(sorted_testers, 1):
                user = guild.get_member(int(user_id))
                count = stats.get("count", 0)
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
                if user:
                    testers_list.append(f"{medal} {user.mention} — **{count}** тестов")
                else:
                    testers_list.append(f"{medal} <@{user_id}> — **{count}** тестов")

            embed = discord.Embed(
                title="🏆 **ТИР-ТЕСТЕР МЕСЯЦА**",
                description="\n".join(testers_list) if testers_list else "Нет данных",
                color=discord.Color.gold(),
            )
            embed.set_footer(
                text=f"Статистика за текущий месяц | Всего тестов: {sum(s.get('count', 0) for s in tester_stats.values())}"
            )

        await edit_or_create_message(
            month_channel, guild.id, "tester_month_message_id", embed
        )


def add_test_to_tester(tester_id):
    current_month = datetime.now().strftime("%Y-%m")

    if tester_id not in tester_stats:
        tester_stats[tester_id] = {"count": 0, "last_month": current_month}

    if tester_stats[tester_id].get("last_month") != current_month:
        tester_stats[tester_id]["count"] = 0
        tester_stats[tester_id]["last_month"] = current_month

    tester_stats[tester_id]["count"] += 1
    save_tester_stats()


async def send_staff_announcement(member, role_name, is_add=True):
    """Отправляет сообщение в канал стафа при выдаче или снятии роли (только на сервере участника)"""
    guild = member.guild
    staff_channel = await get_channel(guild, CHANNEL_STAFF)
    if not staff_channel:
        return

    if role_name == ROLE_ADMINISTRATOR:
        emoji = "👑"
        title = "Administrator"
    elif role_name == ROLE_MODERATOR:
        emoji = "🛡️"
        title = "Moderator"
    elif role_name == ROLE_SENIOR_TESTER:
        emoji = "⭐"
        title = "Senior Tester"
    elif role_name == ROLE_TESTER:
        emoji = "✅"
        title = "Verified Tester"
    else:
        return

    if is_add:
        embed = discord.Embed(
            title=f"{emoji} **{title}**",
            description=f"{member.mention}\nУчастник -> {title}\nСпасибо тебе за участие ❤️",
            color=discord.Color.gold(),
        )
    else:
        embed = discord.Embed(
            title=f"{emoji} **{title}**",
            description=f"{member.mention}\n{title} -> Участник\nРоль снята.",
            color=discord.Color.red(),
        )
    await staff_channel.send(embed=embed)


# ========== НОВАЯ СИСТЕМА ВЕРИФИКАЦИИ (С ВВОДОМ НИКА) ==========
class VerificationModal(discord.ui.Modal, title="✅ ВЕРИФИКАЦИЯ"):
    nickname = discord.ui.TextInput(
        label="Ваш игровой никнейм",
        placeholder="Введите никнейм, который хотите видеть на сервере...",
        required=True,
        max_length=32,
        min_length=2,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)
            new_nickname = self.nickname.value.strip()

            # Проверяем, не верифицирован ли уже пользователь
            member_role = await get_role(interaction.guild, ROLE_MEMBER)
            if member_role and member_role in interaction.user.roles:
                embed = discord.Embed(
                    title="⚠️ **ВНИМАНИЕ**",
                    description="Вы уже прошли верификацию!",
                    color=discord.Color.orange(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Сохраняем ник в базу данных
            if user_id not in user_data:
                user_data[user_id] = {}
            user_data[user_id]["nickname"] = new_nickname
            user_data[user_id]["verified_at"] = datetime.now().isoformat()
            save_user_data()

            # Пытаемся изменить никнейм пользователя
            nickname_changed = False
            try:
                await interaction.user.edit(nick=new_nickname)
                nickname_changed = True
            except discord.Forbidden:
                print(f"❌ Нет прав для изменения ника {interaction.user.name}")
            except Exception as e:
                print(f"❌ Ошибка при изменении ника: {e}")

            # Выдаём роль участника
            member_role_obj = await get_role(interaction.guild, ROLE_MEMBER)
            role_given = False
            if member_role_obj:
                try:
                    await interaction.user.add_roles(member_role_obj)
                    role_given = True
                except Exception as e:
                    print(f"Ошибка выдачи роли: {e}")

            # Создаём embed с результатом
            embed = discord.Embed(
                title="✅ **ВЕРИФИКАЦИЯ ПРОЙДЕНА!**",
                description=f"{interaction.user.mention}, вы успешно прошли верификацию!",
                color=discord.Color.green(),
            )

            if nickname_changed:
                embed.add_field(
                    name="📝 Новый никнейм", value=f"`{new_nickname}`", inline=True
                )
            else:
                embed.add_field(
                    name="⚠️ Никнейм не изменён",
                    value="У бота нет прав на изменение ников. Обратитесь к администратору.",
                    inline=False,
                )
                embed.color = discord.Color.orange()

            if role_given:
                embed.add_field(
                    name="🎭 Выдана роль", value=member_role_obj.mention, inline=True
                )
            else:
                embed.add_field(
                    name="⚠️ Ошибка",
                    value="Не удалось выдать роль! Обратитесь к администратору.",
                    inline=False,
                )
                embed.color = discord.Color.orange()

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Ошибка верификации: {e}")
            if not interaction.response.is_done():
                embed = discord.Embed(
                    title="❌ **ОШИБКА ВЕРИФИКАЦИИ**",
                    description=f"Произошла ошибка: {e}\nОбратитесь к администратору.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)


class VerificationButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✅ Верификация",
        style=discord.ButtonStyle.success,
        custom_id="verify_button",
    )
    async def verify_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            # Проверяем, не верифицирован ли уже пользователь
            member_role = await get_role(interaction.guild, ROLE_MEMBER)
            if member_role and member_role in interaction.user.roles:
                embed = discord.Embed(
                    title="⚠️ **ВНИМАНИЕ**",
                    description="Вы уже прошли верификацию!",
                    color=discord.Color.orange(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Открываем модальное окно для ввода ника
            modal = VerificationModal()
            await interaction.response.send_modal(modal)

        except Exception as e:
            print(f"Ошибка: {e}")
            if not interaction.response.is_done():
                embed = discord.Embed(
                    title="❌ **ОШИБКА**",
                    description=f"Произошла ошибка: {e}",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)


# ========== СИСТЕМА ТИКЕТОВ ПОДДЕРЖКИ ==========
class SupportTicketModal(discord.ui.Modal, title="📝 СОЗДАНИЕ ТИКЕТА"):
    reason = discord.ui.TextInput(
        label="Причина обращения",
        placeholder="Опишите вашу проблему...",
        required=True,
        max_length=500,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):
        category = None
        for cat in interaction.guild.categories:
            if cat.name == "🎫 Тикеты поддержки":
                category = cat
                break

        if not category:
            category = await interaction.guild.create_category("🎫 Тикеты поддержки")

        ticket_number = len(support_tickets) + 1
        channel_name = f"тикет-{interaction.user.name}-{ticket_number}"

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                read_messages=False
            ),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
        }

        support_role = await get_role(interaction.guild, ROLE_TESTER)
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            )

        channel = await category.create_text_channel(
            channel_name, overwrites=overwrites
        )

        support_tickets[str(ticket_number)] = {
            "user_id": str(interaction.user.id),
            "channel_id": channel.id,
            "reason": self.reason.value,
            "status": "open",
            "created_at": datetime.now().isoformat(),
        }
        save_support_tickets()

        embed = discord.Embed(
            title="🎫 **ТИКЕТ СОЗДАН**",
            description=f"**Пользователь:** {interaction.user.mention}\n"
            f"**Причина:** {self.reason.value}\n\n"
            f"Опишите подробно вашу проблему. Администрация скоро свяжется с вами.\n\n"
            f"Для закрытия тикета используйте кнопку ниже.",
            color=discord.Color.blue(),
        )

        close_view = CloseSupportTicketView(ticket_number, channel.id)
        await channel.send(embed=embed, view=close_view)

        await interaction.response.send_message(
            f"✅ Тикет создан! Перейдите в {channel.mention}", ephemeral=True
        )


class SupportTicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📩 Создать тикет",
        style=discord.ButtonStyle.primary,
        custom_id="support_ticket",
    )
    async def support_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = SupportTicketModal()
        await interaction.response.send_modal(modal)


class CloseSupportTicketView(discord.ui.View):
    def __init__(self, ticket_id, channel_id):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.channel_id = channel_id

    @discord.ui.button(
        label="🔒 Закрыть тикет", style=discord.ButtonStyle.danger, emoji="🔒"
    )
    async def close_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if str(self.ticket_id) in support_tickets:
            support_tickets[str(self.ticket_id)]["status"] = "closed"
            support_tickets[str(self.ticket_id)]["closed_at"] = (
                datetime.now().isoformat()
            )
            save_support_tickets()

        await interaction.response.send_message(
            "🗑️ Тикет будет закрыт через 5 секунд..."
        )
        await asyncio.sleep(5)
        await interaction.channel.delete()


# ========== СИСТЕМА ЗАЯВОК В СТАФ ==========
class StaffApplicationModal(discord.ui.Modal, title="📝 ЗАЯВКА В СТАФ"):
    reason = discord.ui.TextInput(
        label="Почему вы хотите стать Verified Tester?",
        placeholder="Опишите ваш опыт, причины и что вы можете дать серверу...",
        required=True,
        max_length=1000,
        style=discord.TextStyle.paragraph,
    )

    experience = discord.ui.TextInput(
        label="Ваш опыт тестирования",
        placeholder="Были ли вы раньше тестером на других серверах?",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)

            if not has_lt3_role(interaction.user):
                embed = discord.Embed(
                    title="❌ **ДОСТУП ЗАПРЕЩЁН**",
                    description="У вас нет роли **LT3** или выше!\n\n"
                    "Заявки в стаф могут подавать только игроки с тиром **LT3** и выше.\n"
                    "Доступные тиры: LT3, HT3, LT2, HT2",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            for app in staff_applications.values():
                if app.get("user_id") == user_id and app.get("status") == "pending":
                    embed = discord.Embed(
                        title="❌ **ЗАЯВКА УЖЕ ЕСТЬ**",
                        description="У вас уже есть активная заявка!\nДождитесь рассмотрения текущей заявки.",
                        color=discord.Color.red(),
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

            category = None
            for cat in interaction.guild.categories:
                if cat.name == "📋 Стафф-заявки":
                    category = cat
                    break

            if not category:
                category = await interaction.guild.create_category("📋 Стафф-заявки")

            application_number = len(staff_applications) + 1
            channel_name = f"заявка-{interaction.user.name}-{application_number}"

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False
                ),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
                interaction.guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
            }

            admin_role = await get_role(interaction.guild, ROLE_ADMINISTRATOR)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                )

            channel = await category.create_text_channel(
                channel_name, overwrites=overwrites
            )

            staff_applications[str(application_number)] = {
                "user_id": user_id,
                "channel_id": channel.id,
                "reason": self.reason.value,
                "experience": self.experience.value,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
            }
            save_staff_applications()

            embed = discord.Embed(
                title="📝 **НОВАЯ ЗАЯВКА В СТАФ**",
                description=f"**Заявитель:** {interaction.user.mention}\n"
                f"**Никнейм:** `{user_data.get(user_id, {}).get('nickname', 'Не указан')}`\n\n"
                f"**Почему хочет стать Verified Tester:**\n{self.reason.value}\n\n"
                f"**Опыт тестирования:**\n{self.experience.value if self.experience.value else 'Не указан'}\n\n"
                f"**Статус:** ⏳ Ожидает рассмотрения",
                color=discord.Color.blue(),
            )
            embed.set_footer(text=f"Заявка #{application_number}")

            view = StaffApplicationView(
                application_number, channel.id, interaction.user.id
            )
            await channel.send(embed=embed, view=view)

            admin_role_obj = await get_role(interaction.guild, ROLE_ADMINISTRATOR)
            if admin_role_obj:
                await channel.send(
                    f"{admin_role_obj.mention} Новая заявка в стаф! Требуется рассмотрение."
                )

            embed_response = discord.Embed(
                title="✅ **ЗАЯВКА СОЗДАНА**",
                description=f"Ваша заявка успешно создана!\nПерейдите в {channel.mention} для отслеживания статуса.\n\n**Ожидайте рассмотрения.**",
                color=discord.Color.green(),
            )
            await interaction.response.send_message(
                embed=embed_response, ephemeral=True
            )

        except Exception as e:
            print(f"Ошибка при создании заявки: {e}")
            if not interaction.response.is_done():
                embed_error = discord.Embed(
                    title="❌ **ОШИБКА**",
                    description=f"Не удалось создать заявку.\nОшибка: {e}",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(
                    embed=embed_error, ephemeral=True
                )


class StaffApplicationView(discord.ui.View):
    def __init__(self, app_id, channel_id, user_id):
        super().__init__(timeout=None)
        self.app_id = app_id
        self.channel_id = channel_id
        self.user_id = user_id

    @discord.ui.button(
        label="✅ Принять заявку", style=discord.ButtonStyle.success, emoji="✅"
    )
    async def accept_app(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        admin_role = await get_role(interaction.guild, ROLE_ADMINISTRATOR)

        if not admin_role or admin_role not in interaction.user.roles:
            embed = discord.Embed(
                title="❌ **НЕТ ПРАВ**",
                description="Принимать заявки может только администратор сервера!",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        app = staff_applications.get(str(self.app_id))
        if not app or app.get("status") != "pending":
            embed = discord.Embed(
                title="❌ **ОШИБКА**",
                description="Заявка уже рассмотрена!",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        app["status"] = "accepted"
        app["reviewed_by"] = str(interaction.user.id)
        app["reviewed_at"] = datetime.now().isoformat()
        save_staff_applications()

        tester_role = await get_role(interaction.guild, ROLE_TESTER)
        user = interaction.guild.get_member(int(self.user_id))

        if user and tester_role:
            await user.add_roles(tester_role)
            await send_staff_announcement(user, ROLE_TESTER, is_add=True)

        embed = discord.Embed(
            title="✅ **ЗАЯВКА ОДОБРЕНА**",
            description=f"**Заявитель:** {user.mention if user else 'Пользователь'}\n"
            f"**Рассмотрел:** {interaction.user.mention}\n\n"
            f"Поздравляем! Вы приняты в команду стафа.\n"
            f"Вам выдана роль **Verified Tester**.\n\n"
            f"*Канал будет удалён через 10 секунд*",
            color=discord.Color.green(),
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(
            "✅ Заявка принята! Канал будет удалён через 10 секунд.", ephemeral=True
        )

        await interaction.message.edit(view=None)
        await asyncio.sleep(10)
        try:
            await interaction.channel.delete()
        except:
            pass

    @discord.ui.button(
        label="❌ Отклонить заявку", style=discord.ButtonStyle.danger, emoji="❌"
    )
    async def deny_app(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        admin_role = await get_role(interaction.guild, ROLE_ADMINISTRATOR)

        if not admin_role or admin_role not in interaction.user.roles:
            embed = discord.Embed(
                title="❌ **НЕТ ПРАВ**",
                description="Отклонять заявки может только администратор сервера!",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        app = staff_applications.get(str(self.app_id))
        if not app or app.get("status") != "pending":
            embed = discord.Embed(
                title="❌ **ОШИБКА**",
                description="Заявка уже рассмотрена!",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        app["status"] = "denied"
        app["reviewed_by"] = str(interaction.user.id)
        app["reviewed_at"] = datetime.now().isoformat()
        save_staff_applications()

        embed = discord.Embed(
            title="❌ **ЗАЯВКА ОТКЛОНЕНА**",
            description=f"**Заявитель:** <@{self.user_id}>\n"
            f"**Рассмотрел:** {interaction.user.mention}\n\n"
            f"К сожалению, ваша заявка отклонена.\n"
            f"Вы можете подать новую заявку позже.\n\n"
            f"*Канал будет удалён через 10 секунд*",
            color=discord.Color.red(),
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(
            "❌ Заявка отклонена! Канал будет удалён через 10 секунд.", ephemeral=True
        )

        await interaction.message.edit(view=None)
        await asyncio.sleep(10)
        try:
            await interaction.channel.delete()
        except:
            pass

    @discord.ui.button(
        label="⏳ Отложить", style=discord.ButtonStyle.secondary, emoji="⏳"
    )
    async def postpone_app(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        admin_role = await get_role(interaction.guild, ROLE_ADMINISTRATOR)

        if not admin_role or admin_role not in interaction.user.roles:
            embed = discord.Embed(
                title="❌ **НЕТ ПРАВ**",
                description="Откладывать заявки может только администратор сервера!",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="⏳ **ЗАЯВКА ОТЛОЖЕНА**",
            description=f"**Заявитель:** <@{self.user_id}>\n"
            f"**Рассмотрит:** {interaction.user.mention}\n\n"
            f"Заявка отложена на рассмотрение.",
            color=discord.Color.blue(),
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(
            "✅ Заявка отложена. Вы можете вернуться к ней позже.", ephemeral=True
        )


class StaffApplicationButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📝 Подать заявку в стаф",
        style=discord.ButtonStyle.primary,
        custom_id="staff_application_button",
    )
    async def staff_application(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not has_lt3_role(interaction.user):
            embed = discord.Embed(
                title="❌ **ДОСТУП ЗАПРЕЩЁН**",
                description="У вас нет роли **LT3** или выше!\n\n"
                "Заявки в стаф могут подавать только игроки с тиром **LT3** и выше.\n"
                "Доступные тиры: LT3, HT3, LT2, HT2",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        for app in staff_applications.values():
            if (
                app.get("user_id") == str(interaction.user.id)
                and app.get("status") == "pending"
            ):
                embed = discord.Embed(
                    title="❌ **ЗАЯВКА УЖЕ ЕСТЬ**",
                    description="У вас уже есть активная заявка!\nДождитесь рассмотрения текущей заявки.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        modal = StaffApplicationModal()
        await interaction.response.send_modal(modal)


# ========== МОДАЛЬНОЕ ОКНО ДЛЯ ОЧЕРЕДИ ==========
class QueueModal(discord.ui.Modal, title="📋 ВСТУПЛЕНИЕ В ОЧЕРЕДЬ"):
    nickname = discord.ui.TextInput(
        label="Ваш игровой никнейм",
        placeholder="Введите ваш никнейм...",
        required=True,
        max_length=50,
    )

    server = discord.ui.TextInput(
        label="Предпочитаемый сервер",
        placeholder="msl.su, femboymc.joinserver.ru, tavix.su, mc.aormio.ru, worst-practice.ru",
        required=True,
        max_length=100,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)

            member_role = await get_role(interaction.guild, ROLE_MEMBER)
            if member_role and member_role not in interaction.user.roles:
                await interaction.response.send_message(
                    "❌ Вы не прошли верификацию! Пройдите верификацию в канале #верификация",
                    ephemeral=True,
                )
                return

            # Проверяем, есть ли у пользователя тир LT3 или выше
            if has_lt3_role(interaction.user):
                # Создаём высокий тест
                await create_high_test(interaction, interaction.user)
                return

            # Сохраняем данные пользователя
            user_data[user_id] = {
                "nickname": self.nickname.value,
                "server": self.server.value,
                "registered_at": datetime.now().isoformat(),
            }
            save_user_data()

            # Проверяем КД
            can_test, next_available = can_take_qualified_test(user_id)
            if not can_test:
                await interaction.response.send_message(
                    f"❌ Вы не можете пройти квалифицированный тест до <t:{int(next_available.timestamp())}:F>!\n"
                    f"КД составляет {QUALIFIED_COOLDOWN_DAYS} дней.",
                    ephemeral=True,
                )
                return

            guild_id = str(interaction.guild.id)
            global queue_data

            # Проверяем, не в очереди ли уже
            if user_id in queue_data:
                await interaction.response.send_message(
                    "❌ Вы уже в очереди на этом сервере!", ephemeral=True
                )
                return

            # Проверяем, нет ли активного тикета
            for ticket in tickets_data.values():
                if (
                    ticket.get("user_id") == user_id
                    and ticket.get("status") == "open"
                    and ticket.get("guild_id", guild_id) == guild_id
                ):
                    await interaction.response.send_message(
                        "❌ У вас уже есть активный тест на этом сервере!",
                        ephemeral=True,
                    )
                    return

            # Добавляем в очередь
            queue_data.append(user_id)
            save_queue()

            # Выдаём роль WhiteList
            whitelist_role = await get_role(interaction.guild, ROLE_WHITELIST)
            if whitelist_role:
                await interaction.user.add_roles(whitelist_role)

            # Обновляем отображение очереди
            await update_queue_display(interaction.guild)

            # Находим позицию в очереди
            position = queue_data.index(user_id) + 1

            embed = discord.Embed(
                title="✅ **ВЫ В ОЧЕРЕДИ**",
                description=f"{interaction.user.mention}, вы добавлены в очередь на тестирование!\n\n"
                f"**Позиция в очереди:** {position}\n\n"
                f"Чтобы выйти из очереди, используйте `/leave`",
                color=discord.Color.green(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Ошибка в QueueModal: {e}")
            import traceback

            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Ошибка: {str(e)}", ephemeral=True
                )


# ========== КНОПКИ ==========
class QueueButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📋 Встать в очередь",
        style=discord.ButtonStyle.primary,
        custom_id="join_queue",
    )
    async def join_queue(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            member_role = await get_role(interaction.guild, ROLE_MEMBER)
            if member_role and member_role not in interaction.user.roles:
                await interaction.response.send_message(
                    "❌ Вы не прошли верификацию! Пройдите верификацию в канале #верификация",
                    ephemeral=True,
                )
                return

            if has_lt3_role(interaction.user):
                # Создаём высокий тест
                await create_high_test(interaction, interaction.user)
                return

            # Открываем модальное окно
            modal = QueueModal()
            await interaction.response.send_modal(modal)

        except Exception as e:
            print(f"Ошибка в QueueButton: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Ошибка: {str(e)}", ephemeral=True
                )


# Проверяет, может ли пользователь пройти квалифицированный тест
def can_take_qualified_test(user_id):
    """Проверяет, может ли пользователь пройти квалифицированный тест"""
    # Если у пользователя есть LT3+, он не проходит квалиф тесты
    user = None
    for guild in bot.guilds:
        user = guild.get_member(int(user_id))
        if user:
            break

    if user and has_lt3_role(user):
        return False, None

    if user_id not in qualified_cooldowns:
        return True, None

    last_test = datetime.fromisoformat(qualified_cooldowns[user_id])
    if datetime.now() - last_test < timedelta(days=QUALIFIED_COOLDOWN_DAYS):
        next_available = last_test + timedelta(days=QUALIFIED_COOLDOWN_DAYS)
        return False, next_available
    return True, None


# ========== КНОПКА ДЛЯ ВЗЯТИЯ ТИКЕТА ==========
class TakeTicketView(discord.ui.View):
    def __init__(self, ticket_id, channel_id):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.channel_id = channel_id

    @discord.ui.button(
        label="🎫 Взять тикет", style=discord.ButtonStyle.primary, emoji="🎫"
    )
    async def take_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # Проверяем, есть ли у пользователя роль тестера
        tester_role = await get_role(interaction.guild, ROLE_TESTER)
        senior_role = await get_role(interaction.guild, ROLE_SENIOR_TESTER)

        is_tester = tester_role and tester_role in interaction.user.roles
        is_senior = senior_role and senior_role in interaction.user.roles

        if not is_tester and not is_senior:
            await interaction.response.send_message(
                "❌ У вас нет прав на проведение тестов!", ephemeral=True
            )
            return

        ticket = tickets_data.get(str(self.ticket_id))
        if not ticket or ticket.get("status") != "open":
            await interaction.response.send_message(
                "❌ Тикет уже закрыт или не существует!", ephemeral=True
            )
            return

        # Обнов.�яем channel_id на всякий случай (если вдруг не совпадает)
        if ticket.get("channel_id") != self.channel_id:
            print(
                f"⚠️ Обновляем channel_id для тикета #{self.ticket_id}: {ticket.get('channel_id')} -> {self.channel_id}"
            )
            ticket["channel_id"] = self.channel_id
            save_tickets()

        # Назначаем тестера
        ticket["tester_id"] = str(interaction.user.id)
        ticket["waiting_for_tester"] = False
        save_tickets()

        # Добавляем тестера в активные, если его там нет
        _gid = str(interaction.guild.id)
        _uid = str(interaction.user.id)
        if _gid not in active_testers:
            active_testers[_gid] = []
        if _uid not in active_testers[_gid]:
            active_testers[_gid].append(_uid)
            save_active_testers()
            await update_queue_display(interaction.guild)

        # Добавляем тестера в канал
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            # Добавляем права тестеру
            await channel.set_permissions(
                interaction.user, read_messages=True, send_messages=True
            )

            embed = discord.Embed(
                title="✅ **ТЕСТЕР НАЗНАЧЕН**",
                description=f"Тестирование проводит: {interaction.user.mention}\n\n"
                f"Проведите тестирование и используйте `/close` для завершения.\n\n"
                f"**Важно:** Для LT3+ тикетов минимальная длительность - {MIN_TICKET_DAYS} дня(ей).\n"
                f"Если тест пройден раньше, вы можете закрыть его командой `/close`.",
                color=discord.Color.green(),
            )
            await channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ Вы взяли тикет! Приступайте к тестированию.", ephemeral=True
        )

        # Удаляем кнопки
        await interaction.message.edit(view=None)


# ========== ФУНКЦИЯ ДЛЯ СОЗДАНИЯ ВЫСОКОГО ТЕСТА ==========
async def create_high_test(interaction: discord.Interaction, user: discord.Member):
    """Создаёт высокий тест для пользователя с тиром LT3+"""
    try:
        senior_role = await get_role(interaction.guild, ROLE_SENIOR_TESTER)
        user_id = str(user.id)

        # Проверяем КД на высокий тест
        if user_id in high_cooldowns:
            last_test = datetime.fromisoformat(high_cooldowns[user_id])
            if datetime.now() - last_test < timedelta(days=HIGH_COOLDOWN_DAYS):
                next_available = last_test + timedelta(days=HIGH_COOLDOWN_DAYS)
                embed = discord.Embed(
                    title="❌ **КД АКТИВНО**",
                    description=f"Вы не можете пройти высокий тест до <t:{int(next_available.timestamp())}:F>!\n"
                    f"КД составляет {HIGH_COOLDOWN_DAYS} дней.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Проверяем, есть ли уже активный тикет
        for ticket in tickets_data.values():
            if (
                ticket.get("user_id") == user_id
                and ticket.get("status") == "open"
                and ticket.get("guild_id") == str(interaction.guild.id)
            ):
                embed = discord.Embed(
                    title="❌ **АКТИВНЫЙ ТЕСТ**",
                    description="У вас уже есть активный тест! Дождитесь его завершения.",
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Определяем текущий тир пользователя
        current_tier = "Неизвестно"
        if discord.utils.get(user.roles, name=ROLE_LT3):
            current_tier = "LT3"
        elif discord.utils.get(user.roles, name=ROLE_HT3):
            current_tier = "HT3"
        elif discord.utils.get(user.roles, name=ROLE_LT2):
            current_tier = "LT2"
        elif discord.utils.get(user.roles, name=ROLE_HT2):
            current_tier = "HT2"

        user_info = user_data.get(user_id, {})
        nickname = user_info.get("nickname", user.display_name)
        server = user_info.get("server", "Не указан")

        # Создаём категорию для тестов
        category = None
        for cat in interaction.guild.categories:
            if cat.name == "Тесты":
                category = cat
                break

        if not category:
            category = await interaction.guild.create_category("Тесты")

        # Настраиваем права доступа
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                read_messages=False
            ),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        # Добавляем права для Senior Tester, если роль существует
        if senior_role:
            overwrites[senior_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            )

        # Создаём канал
        channel = await category.create_text_channel(
            f"тест-{user.name}", overwrites=overwrites
        )

        print(f"✅ Создан канал для высокого теста: {channel.name} (ID: {channel.id})")

        ticket_id = len(tickets_data) + 1
        tickets_data[str(ticket_id)] = {
            "user_id": user_id,
            "tester_id": None,  # Пока нет тестера
            "channel_id": channel.id,
            "guild_id": str(interaction.guild.id),
            "status": "open",
            "type": "high",
            "nickname": nickname,
            "server": server,
            "current_tier": current_tier,
            "created_at": datetime.now().isoformat(),
        }
        save_tickets()
        print(f"✅ Тикет #{ticket_id} сохранён с channel_id={channel.id}")

        # Создаём embed
        embed = discord.Embed(
            title="⭐ **ВЫСОКИЙ ТЕСТ**",
            description=f"**Тестируемый:** {user.mention}\n"
            f"**Никнейм:** `{nickname}`\n"
            f"**Предпочитаемый сервер:** `{server}`\n"
            f"**Текущий тир:** `{current_tier}`\n\n"
            f"Ожидает назначения тестера.\n\n"
            f"**Доступные тиры для выдачи:**\n{', '.join(HIGH_TIERS)}\n\n"
            f"**Минимальная длительность тикета:** {MIN_TICKET_DAYS} дня(ей)",
            color=discord.Color.gold(),
        )

        # Пингуем Senior Tester
        senior_role_obj = await get_role(interaction.guild, ROLE_SENIOR_TESTER)
        ping_message = ""
        if senior_role_obj:
            ping_message = f"{senior_role_obj.mention} Новый высокий тест для пользователя с тиром **{current_tier}**! Требуется тестер!\n"

        await channel.send(ping_message, embed=embed)

        # Добавляем кнопку для тестера, чтобы взять тикет
        view = TakeTicketView(ticket_id, channel.id)
        await channel.send(
            "🔘 **Кто будет проводить тест?** Нажмите на кнопку ниже, чтобы взять тикет.",
            view=view,
        )

        await update_queue_display(interaction.guild)

        await interaction.response.send_message(
            f"✅ У вас есть тир **{current_tier}**! Для вас создан высокий тест.\n{channel.mention}\nОжидайте назначения тестера.",
            ephemeral=True,
        )

    except Exception as e:
        print(f"Ошибка при создании высокого теста: {e}")
        import traceback

        traceback.print_exc()
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"❌ Ошибка при создании теста: {str(e)}", ephemeral=True
            )


# ========== КОМАНДА /nickname ==========
@bot.tree.command(name="nickname", description="Изменить свой никнейм на сервере")
async def change_nickname(interaction: discord.Interaction, nickname: str):
    user_id = str(interaction.user.id)

    if len(nickname) > 32:
        embed = discord.Embed(
            title="❌ **ОШИБКА**",
            description="Никнейм не может быть длиннее 32 символов!",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["nickname"] = nickname
    save_user_data()

    if not interaction.guild.me.guild_permissions.manage_nicknames:
        embed = discord.Embed(
            title="⚠️ **ОШИБКА ПРАВ**",
            description="❌ У бота нет права `manage_nicknames`!\n\n"
            "**Что делать:**\n"
            '1. Выдайте боту роль с правом **"Управлять никами"**\n'
            "2. Или переместите роль бота выше всех ролей, чьи ники нужно менять\n"
            "3. Затем используйте команду `/sync` для обновления\n\n"
            f"**Ваш никнейм `{nickname}` сохранён в базе данных,**\n"
            f"но не применён на сервере.",
            color=discord.Color.orange(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        await interaction.user.edit(nick=nickname)
        embed = discord.Embed(
            title="✅ **НИКНЕЙМ ИЗМЕНЁН**",
            description=f"Ваш новый никнейм: `{nickname}`",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ **ОШИБКА**",
            description="❌ У бота нет прав для изменения вашего никнейма!\n\n"
            "**Возможные причины:**\n"
            "• Ваша роль выше роли бота\n"
            "• У бота нет права `manage_nicknames`\n\n"
            f"**Ваш никнейм `{nickname}` сохранён в базе данных,**\n"
            f"но не применён на сервере.",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = discord.Embed(
            title="❌ **ОШИБКА**",
            description=f"Неизвестная ошибка: {e}",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ========== КОМАНДА /next ==========
@bot.tree.command(name="next", description="Создать тикет со следующим в очереди")
async def next_ticket(interaction: discord.Interaction):
    try:
        tester_role = await get_role(interaction.guild, ROLE_TESTER)
        senior_role = await get_role(interaction.guild, ROLE_SENIOR_TESTER)

        is_tester = tester_role and tester_role in interaction.user.roles
        is_senior = senior_role and senior_role in interaction.user.roles

        if not is_tester and not is_senior:
            await interaction.response.send_message(
                "❌ У вас нет прав на эту команду!", ephemeral=True
            )
            return

        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        if user_id not in active_testers.get(guild_id, []):
            await interaction.response.send_message(
                "❌ Вы не активны на этом сервере! Используйте `/start`", ephemeral=True
            )
            return

        global queue_data

        # Проверяем длину очереди
        if not queue_data or len(queue_data) == 0:
            await interaction.response.send_message(
                "❌ В очереди никого нет!", ephemeral=True
            )
            return

        # Проверяем, есть ли кто-то с тиром LT3 или выше в очереди
        high_tier_index = -1
        high_tier_user = None
        high_tier_name = None

        for i, uid in enumerate(queue_data):
            user = interaction.guild.get_member(int(uid))
            if user and has_lt3_role(user):
                high_tier_index = i
                high_tier_user = user
                if discord.utils.get(user.roles, name=ROLE_LT3):
                    high_tier_name = "LT3"
                elif discord.utils.get(user.roles, name=ROLE_HT3):
                    high_tier_name = "HT3"
                elif discord.utils.get(user.roles, name=ROLE_LT2):
                    high_tier_name = "LT2"
                elif discord.utils.get(user.roles, name=ROLE_HT2):
                    high_tier_name = "HT2"
                break

        # Если есть пользователь с тиром LT3 или выше
        if high_tier_index != -1 and high_tier_user:
            # Удаляем из очереди
            queue_data.pop(high_tier_index)
            save_queue()

            whitelist_role = await get_role(interaction.guild, ROLE_WHITELIST)
            if whitelist_role:
                await high_tier_user.remove_roles(whitelist_role)

            user_info = user_data.get(str(high_tier_user.id), {})
            nickname = user_info.get("nickname", "Не указан")
            server = user_info.get("server", "Не указан")

            # Создаём категорию для тестов
            category = None
            for cat in interaction.guild.categories:
                if cat.name == "Тесты":
                    category = cat
                    break

            if not category:
                category = await interaction.guild.create_category("Тесты")

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False
                ),
                high_tier_user: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
            }

            if senior_role:
                overwrites[senior_role] = discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                )

            channel = await category.create_text_channel(
                f"высокий-{high_tier_user.name}", overwrites=overwrites
            )

            ticket_id = len(tickets_data) + 1
            tickets_data[str(ticket_id)] = {
                "user_id": str(high_tier_user.id),
                "tester_id": str(interaction.user.id),
                "channel_id": channel.id,
                "guild_id": str(interaction.guild.id),
                "status": "open",
                "type": "high",
                "nickname": nickname,
                "server": server,
                "current_tier": high_tier_name,
                "created_at": datetime.now().isoformat(),
            }
            save_tickets()

            embed = discord.Embed(
                title="⭐ **ВЫСОКИЙ ТЕСТ**",
                description=f"**Тестируемый:** {high_tier_user.mention}\n"
                f"**Никнейм:** `{nickname}`\n"
                f"**Предпочитаемый сервер:** `{server}`\n"
                f"**Текущий тир:** `{high_tier_name}`\n"
                f"**Тестер:** {interaction.user.mention}\n\n"
                f"Проведите тестирование и используйте `/close` для завершения.\n\n"
                f"**Доступные тиры для выдачи:**\n{', '.join(HIGH_TIERS)}\n\n"
                f"**Минимальная длительность тикета:** {MIN_TICKET_DAYS} дня(ей)",
                color=discord.Color.gold(),
            )

            await channel.send(embed=embed)
            await update_queue_display(interaction.guild)

            await interaction.response.send_message(
                f"✅ Обнаружен пользователь с тиром **{high_tier_name}**! Тикет создан вне очереди.\n{channel.mention}",
                ephemeral=True,
            )
            return

        # Обычная очередь - берём первого
        target_user_id = queue_data.pop(0)
        save_queue()

        target_user = interaction.guild.get_member(int(target_user_id))
        if not target_user:
            await interaction.response.send_message(
                "❌ Пользователь не найден на сервере!", ephemeral=True
            )
            # Возвращаем обратно в очередь
            queue_data.insert(0, target_user_id)
            save_queue()
            return

        whitelist_role = await get_role(interaction.guild, ROLE_WHITELIST)
        if whitelist_role:
            await target_user.remove_roles(whitelist_role)

        user_info = user_data.get(target_user_id, {})
        nickname = user_info.get("nickname", "Не указан")
        server = user_info.get("server", "Не указан")

        # Создаём категорию для тестов
        category = None
        for cat in interaction.guild.categories:
            if cat.name == "Тесты":
                category = cat
                break

        if not category:
            category = await interaction.guild.create_category("Тесты")

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                read_messages=False
            ),
            target_user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
        }

        channel = await category.create_text_channel(
            f"тест-{target_user.name}", overwrites=overwrites
        )

        ticket_id = len(tickets_data) + 1
        tickets_data[str(ticket_id)] = {
            "user_id": target_user_id,
            "tester_id": str(interaction.user.id),
            "channel_id": channel.id,
            "guild_id": str(interaction.guild.id),
            "status": "open",
            "type": "qualified",
            "nickname": nickname,
            "server": server,
            "created_at": datetime.now().isoformat(),
        }
        save_tickets()

        embed = discord.Embed(
            title="🎫 **НАЧАЛО ТЕСТИРОВАНИЯ**",
            description=f"**Тестируемый:** {target_user.mention}\n"
            f"**Никнейм:** `{nickname}`\n"
            f"**Предпочитаемый сервер:** `{server}`\n"
            f"**Тестер:** {interaction.user.mention}\n"
            f"**Тип теста:** 📋 КВАЛИФИЦИРОВАННЫЙ\n\n"
            f"Проведите тестирование и используйте `/close` для завершения.\n\n"
            f"**Доступные тиры для выдачи:**\n{', '.join(QUALIFIED_TIERS)}",
            color=discord.Color.blue(),
        )
        await channel.send(embed=embed)

        await update_queue_display(interaction.guild)

        await interaction.response.send_message(
            f"✅ Тикет создан! {channel.mention}", ephemeral=True
        )

    except Exception as e:
        print(f"Ошибка в команде next: {e}")
        import traceback

        traceback.print_exc()
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Ошибка: {str(e)}", ephemeral=True
                )
        except:
            pass


# ========== КОМАНДЫ ДЛЯ ОБЫЧНЫХ ПОЛЬЗОВАТЕЛЕЙ ==========
@bot.tree.command(name="leave", description="Выйти из очереди на тестирование")
async def leave(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    global queue_data

    # Проверяем, есть ли пользователь в очереди
    if user_id not in queue_data:
        await interaction.response.send_message("❌ Вы не в очереди!", ephemeral=True)
        return

    queue_data.remove(user_id)
    save_queue()

    whitelist_role = await get_role(interaction.guild, ROLE_WHITELIST)
    if whitelist_role:
        await interaction.user.remove_roles(whitelist_role)

    await update_queue_display(interaction.guild)

    embed = discord.Embed(
        title="✅ **ВЫ ВЫШЛИ ИЗ ОЧЕРЕДИ**",
        description=f"{interaction.user.mention}, вы успешно вышли из очереди.",
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ========== КОМАНДЫ ДЛЯ ТЕСТЕРОВ ==========
@bot.tree.command(name="start", description="Стать готовым для тестирования")
async def start_testing(interaction: discord.Interaction):
    tester_role = await get_role(interaction.guild, ROLE_TESTER)
    if not tester_role or tester_role not in interaction.user.roles:
        await interaction.response.send_message(
            "❌ У вас нет роли тестера!", ephemeral=True
        )
        return

    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)
    if guild_id not in active_testers:
        active_testers[guild_id] = []
    if user_id in active_testers[guild_id]:
        await interaction.response.send_message(
            "❌ Вы уже в списке активных тестеров на этом сервере!", ephemeral=True
        )
        return

    active_testers[guild_id].append(user_id)
    save_active_testers()
    await update_queue_display(interaction.guild)

    embed = discord.Embed(
        title="✅ **ВЫ ГОТОВЫ К ТЕСТИРОВАНИЮ**",
        description=f"{interaction.user.mention}, вы добавлены в список активных тестеров!",
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="stop", description="Выйти из активных тестеров")
async def stop_testing(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)
    guild_testers = active_testers.get(guild_id, [])

    if user_id not in guild_testers:
        await interaction.response.send_message(
            "❌ Вы не в списке активных тестеров на этом сервере!", ephemeral=True
        )
        return

    guild_testers.remove(user_id)
    active_testers[guild_id] = guild_testers
    save_active_testers()
    await update_queue_display(interaction.guild)

    embed = discord.Embed(
        title="✅ **ВЫ ВЫШЛИ ИЗ АКТИВНЫХ ТЕСТЕРОВ**",
        description=f"{interaction.user.mention}, вы больше не отображаетесь как активный тестер.",
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


class TierSelect(discord.ui.Select):
    def __init__(self, ticket_id, test_type, no_cd_mode=False):
        self.ticket_id = ticket_id
        self.test_type = test_type
        self.no_cd_mode = no_cd_mode

        if test_type == "qualified":
            options = [
                discord.SelectOption(label="LT5", description="Low Tier 5", emoji="🥉"),
                discord.SelectOption(
                    label="HT5", description="High Tier 5", emoji="🥉"
                ),
                discord.SelectOption(label="LT4", description="Low Tier 4", emoji="🥈"),
                discord.SelectOption(
                    label="HT4", description="High Tier 4", emoji="🥈"
                ),
                discord.SelectOption(label="LT3", description="Low Tier 3", emoji="🥇"),
            ]
        else:
            options = [
                discord.SelectOption(
                    label="HT3", description="High Tier 3", emoji="⭐"
                ),
                discord.SelectOption(label="LT2", description="Low Tier 2", emoji="👑"),
                discord.SelectOption(
                    label="HT2", description="High Tier 2", emoji="👑"
                ),
            ]

        super().__init__(
            placeholder="Выберите тир",
            options=options,
            custom_id=f"tier_select_{ticket_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            selected_tier = self.values[0]
            ticket = tickets_data.get(str(self.ticket_id))

            if not ticket:
                await interaction.response.send_message(
                    "❌ Тикет не найден!", ephemeral=True
                )
                return

            user_id = ticket.get("user_id")
            tester_id = ticket.get("tester_id")
            test_type = ticket.get("type")
            target_user = interaction.guild.get_member(int(user_id))
            nickname = ticket.get("nickname", "Не указан")

            # Определяем предыдущий тир
            previous_tier = "Unranked"
            if target_user:
                for tier in TIER_ORDER:
                    role = discord.utils.get(interaction.guild.roles, name=tier)
                    if role and role in target_user.roles:
                        previous_tier = tier
                        break

            # Выдаём новую роль
            if target_user:
                await remove_lower_tiers(target_user, selected_tier)
                tier_role = await get_role(interaction.guild, selected_tier)
                if tier_role:
                    await target_user.add_roles(tier_role)

            # Устанавливаем КД
            if test_type == "qualified":
                if selected_tier == "LT3":
                    if user_id in qualified_cooldowns:
                        del qualified_cooldowns[user_id]
                        save_qualified_cooldowns()
                else:
                    if not self.no_cd_mode:
                        set_qualified_cooldown(user_id)
            elif test_type == "high":
                set_high_cooldown(user_id)

            # Обновляем статистику тестера
            add_test_to_tester(tester_id)
            await update_tester_month_display(interaction.guild)

            # Закрываем тикет
            ticket["status"] = "closed"
            ticket["tier"] = selected_tier
            ticket["closed_at"] = datetime.now().isoformat()
            if self.no_cd_mode:
                ticket["no_cd"] = True
            save_tickets()

            # Отправляем результат в канал результатов
            if test_type == "qualified":
                results_channel = await get_channel(
                    interaction.guild, CHANNEL_QUALIFIED_RESULTS
                )
            else:
                results_channel = await get_channel(
                    interaction.guild, CHANNEL_HIGH_RESULTS
                )

            if results_channel:
                embed = discord.Embed(
                    title=f"📊 Результат теста {nickname}", color=discord.Color.gold()
                )
                embed.add_field(
                    name="Игрок",
                    value=target_user.mention if target_user else user_id,
                    inline=False,
                )
                embed.add_field(
                    name="Тестер", value=interaction.user.mention, inline=True
                )
                embed.add_field(name="Никнейм", value=f"`{nickname}`", inline=True)
                embed.add_field(
                    name="Предыдущий тир", value=f"`{previous_tier}`", inline=True
                )
                embed.add_field(
                    name="Полученный тир", value=f"`{selected_tier}`", inline=True
                )
                await results_channel.send(embed=embed)

            # Удаляем канал
            channel = interaction.channel
            await interaction.response.send_message(
                f"✅ Тикет закрыт! Выдан тир: {selected_tier}"
            )
            await asyncio.sleep(2)
            await channel.delete()

        except Exception as e:
            print(f"Ошибка в TierSelect callback: {e}")
            import traceback

            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Ошибка: {str(e)}", ephemeral=True
                )


class TierSelectView(discord.ui.View):
    def __init__(self, ticket_id, test_type, no_cd_mode=False):
        super().__init__(timeout=None)
        self.add_item(TierSelect(ticket_id, test_type, no_cd_mode))


def is_ticket_old_enough(ticket):
    """Проверяет, достаточно ли стар тикет для закрытия (для LT3+ тикетов)"""
    test_type = ticket.get("type", "qualified")

    # Для квалифицированных тестов (не LT3+) - можно закрывать сразу
    if test_type != "high":
        return True, None

    # Для высоких тестов (LT3+) - проверяем возраст
    created_at = datetime.fromisoformat(ticket.get("created_at"))
    age = datetime.now() - created_at

    if age >= timedelta(days=MIN_TICKET_DAYS):
        return True, None
    else:
        remaining = timedelta(days=MIN_TICKET_DAYS) - age
        return False, remaining


@bot.tree.command(name="close", description="Закрыть тикет и выдать тир")
async def close_ticket(interaction: discord.Interaction):
    try:
        tester_role = await get_role(interaction.guild, ROLE_TESTER)
        senior_role = await get_role(interaction.guild, ROLE_SENIOR_TESTER)

        is_tester = tester_role and tester_role in interaction.user.roles
        is_senior = senior_role and senior_role in interaction.user.roles

        if not is_tester and not is_senior:
            await interaction.response.send_message(
                "❌ У вас нет прав на эту команду!", ephemeral=True
            )
            return

        # Ищем тикет по ID канала
        current_channel_id = interaction.channel.id
        print(
            f"🔍 Поиск тикета для канала {current_channel_id} ({interaction.channel.name})"
        )

        ticket_id = None
        found_ticket = None

        for tid, ticket in tickets_data.items():
            if (
                ticket.get("channel_id") == current_channel_id
                and ticket.get("status") == "open"
            ):
                ticket_id = tid
                found_ticket = ticket
                print(f"✅ Найден тикет #{tid}")
                break

        if not ticket_id:
            print(f"❌ Тикет не найден! Активные тикеты:")
            for tid, ticket in tickets_data.items():
                if ticket.get("status") == "open":
                    print(f"  - #{tid}: channel_id={ticket.get('channel_id')}")

            await interaction.response.send_message(
                "❌ Этот канал не является активным тикетом!", ephemeral=True
            )
            return

        ticket = found_ticket
        tester_id = ticket.get("tester_id")
        test_type = ticket.get("type", "qualified")

        # Проверяем, тот ли тестер закрывает (только для квалиф тестов)
        if test_type == "qualified" and str(interaction.user.id) != tester_id:
            await interaction.response.send_message(
                "❌ Только тестер, начавший тест, может его закрыть!", ephemeral=True
            )
            return

        # Для высоких тестов проверяем, что закрывает Senior Tester
        if test_type == "high" and not is_senior:
            await interaction.response.send_message(
                "❌ Высокие тесты могут закрывать только **Senior Tester**!",
                ephemeral=True,
            )
            return

        # Отключаем проверку возраста (если нужно вернуть - раскомментировать)
        # if test_type == "high":
        #     is_old_enough, remaining = is_ticket_old_enough(ticket)
        #     if not is_old_enough:
        #         hours = remaining.total_seconds() // 3600
        #         minutes = (remaining.total_seconds() % 3600) // 60
        #         await interaction.response.send_message(
        #             f"❌ **Тикет ещё слишком новый!**\n\n"
        #             f"Тикет будет доступен для закрытия через **{int(hours)}ч {int(minutes)}мин**.",
        #             ephemeral=True
        #         )
        #         return

        # Создаём меню выбора тира
        embed = discord.Embed(
            title="🎫 **ЗАКРЫТИЕ ТИКЕТА**",
            description=f"**Тип теста:** {'⭐ ВЫСОКИЙ' if test_type == 'high' else '📋 КВАЛИФИЦИРОВАННЫЙ'}\n\n"
            f"Выберите тир, который будет выдан тестируемому:",
            color=discord.Color.blue(),
        )

        view = TierSelectView(ticket_id, test_type, no_cd_mode=False)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        print(f"Ошибка в команде close: {e}")
        import traceback

        traceback.print_exc()
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"❌ Ошибка: {str(e)}", ephemeral=True
            )


@bot.tree.command(
    name="forceclose",
    description="ПРИНУДИТЕЛЬНО закрыть тикет БЕЗ проверки длительности (только для админов)",
)
async def force_close_ticket(interaction: discord.Interaction):
    """Принудительное закрытие тикета без проверки длительности (только для админов)"""

    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ **НЕТ ПРАВ**",
            description="Эта команда доступна только администраторам!",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    ticket_id = None
    for tid, ticket in tickets_data.items():
        if (
            ticket.get("channel_id") == interaction.channel.id
            and ticket.get("status") == "open"
        ):
            ticket_id = tid
            break

    if not ticket_id:
        embed = discord.Embed(
            title="❌ **ОШИБКА**",
            description="Этот канал не является активным тикетом!",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    ticket = tickets_data[ticket_id]
    test_type = ticket.get("type", "qualified")
    user_id = ticket.get("user_id")
    target_user = interaction.guild.get_member(int(user_id))

    whitelist_role = await get_role(interaction.guild, ROLE_WHITELIST)
    if whitelist_role and target_user:
        await target_user.remove_roles(whitelist_role)

    # Если это высокий тест, всё равно ставим КД
    if test_type == "high":
        set_high_cooldown(user_id)

    ticket["status"] = "closed"
    ticket["closed_by"] = str(interaction.user.id)
    ticket["closed_at"] = datetime.now().isoformat()
    ticket["force_closed"] = True
    save_tickets()

    embed = discord.Embed(
        title="✅ **ТИКЕТ ПРИНУДИТЕЛЬНО ЗАКРЫТ**",
        description=f"Тикет закрыт администратором {interaction.user.mention}\n"
        f"Роль WhiteList снята.\n"
        f"{'КД на высокий тест установлен.' if test_type == 'high' else ''}",
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await asyncio.sleep(3)
    await interaction.channel.delete()


@bot.tree.command(
    name="nokd",
    description="Закрыть тикет БЕЗ выдачи тира (только для Verified Tester, Senior Tester и админов)",
)
async def close_ticket_no_cd(interaction: discord.Interaction):
    # Проверяем роли
    tester_role = await get_role(interaction.guild, ROLE_TESTER)
    senior_role = await get_role(interaction.guild, ROLE_SENIOR_TESTER)

    is_tester = tester_role and tester_role in interaction.user.roles
    is_senior = senior_role and senior_role in interaction.user.roles
    is_admin = interaction.user.guild_permissions.administrator

    # Теперь проверяем: Verified Tester, Senior Tester или администратор
    if not is_tester and not is_senior and not is_admin:
        embed = discord.Embed(
            title="❌ **НЕТ ПРАВ**",
            description="У вас нет прав на использование этой команды!\n\n"
            "Требуются роли: **Verified Tester**, **Senior Tester** или **Администратор**",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    ticket_id = None
    for tid, ticket in tickets_data.items():
        if (
            ticket.get("channel_id") == interaction.channel.id
            and ticket.get("status") == "open"
        ):
            ticket_id = tid
            break

    if not ticket_id:
        embed = discord.Embed(
            title="❌ **ОШИБКА**",
            description="Этот канал не является активным тикетом!",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    ticket = tickets_data[ticket_id]
    test_type = ticket.get("type", "qualified")
    user_id = ticket.get("user_id")
    target_user = interaction.guild.get_member(int(user_id))

    # Проверяем минимальную длительность для LT3+ тикетов (кроме админов)
    if test_type == "high" and not is_admin:
        is_old_enough, remaining = is_ticket_old_enough(ticket)
        if not is_old_enough:
            hours = remaining.total_seconds() // 3600
            minutes = (remaining.total_seconds() % 3600) // 60
            await interaction.response.send_message(
                f"❌ **Тикет ещё слишком новый!**\n\n"
                f"Для LT3+ тикетов минимальная длительность - **{MIN_TICKET_DAYS} дня(ей)**.\n"
                f"Тикет будет доступен для закрытия через **{int(hours)}ч {int(minutes)}мин**.\n\n"
                f"Если тест пройден раньше, тикет останется активным до истечения этого времени.\n"
                f"Администратор может использовать команду `/forceclose` для принудительного закрытия.",
                ephemeral=True,
            )
            return

    whitelist_role = await get_role(interaction.guild, ROLE_WHITELIST)
    if whitelist_role and target_user:
        await target_user.remove_roles(whitelist_role)

    ticket["status"] = "closed"
    ticket["closed_by"] = str(interaction.user.id)
    ticket["closed_at"] = datetime.now().isoformat()
    ticket["no_tier"] = True
    save_tickets()

    embed = discord.Embed(
        title="✅ **ТИКЕТ ЗАКРЫТ**",
        description="Тикет закрыт без выдачи тира.\nРоль WhiteList снята.",
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await asyncio.sleep(3)
    await interaction.channel.delete()


# ========== КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ ==========
@bot.tree.command(
    name="remove_from_queue",
    description="Удалить пользователя из очереди (только для админов)",
)
async def remove_from_queue(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ У вас нет прав администратора!", ephemeral=True
        )
        return

    user_id = str(user.id)

    if user_id not in queue_data:
        await interaction.response.send_message(
            f"❌ {user.mention} не находится в очереди!", ephemeral=True
        )
        return

    queue_data.remove(user_id)
    save_queue()

    whitelist_role = await get_role(interaction.guild, ROLE_WHITELIST)
    if whitelist_role:
        await user.remove_roles(whitelist_role)

    await update_queue_display(interaction.guild)

    embed = discord.Embed(
        title="✅ **УДАЛЕН ИЗ ОЧЕРЕДИ**",
        description=f"{user.mention} удалён из очереди администратором {interaction.user.mention}",
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="clear_queue", description="Очистить всю очередь (только для админов)"
)
async def clear_queue(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ У вас нет прав администратора!", ephemeral=True
        )
        return

    global queue_data

    whitelist_role = await get_role(interaction.guild, ROLE_WHITELIST)
    for user_id in queue_data:
        user = interaction.guild.get_member(int(user_id))
        if user and whitelist_role:
            try:
                await user.remove_roles(whitelist_role)
            except:
                pass

    queue_data = []
    save_queue()
    await update_queue_display(interaction.guild)

    embed = discord.Embed(
        title="✅ **ОЧЕРЕДЬ ОЧИЩЕНА**",
        description=f"Очередь полностью очищена администратором {interaction.user.mention}",
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="close_user_ticket",
    description="Закрыть все активные тикеты пользователя (только для админов)",
)
async def close_user_ticket(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ У вас нет прав администратора!", ephemeral=True
        )
        return

    user_id = str(user.id)
    closed_tickets = []

    for ticket_id, ticket in list(tickets_data.items()):
        if ticket.get("user_id") == user_id and ticket.get("status") == "open":
            ticket["status"] = "closed"
            ticket["closed_by"] = str(interaction.user.id)
            ticket["closed_at"] = datetime.now().isoformat()

            channel_id = ticket.get("channel_id")
            if channel_id:
                channel = interaction.guild.get_channel(channel_id)
                if channel:
                    try:
                        await channel.delete()
                    except:
                        pass

            closed_tickets.append(ticket_id)

    save_tickets()

    if closed_tickets:
        embed = discord.Embed(
            title="✅ **ТИКЕТЫ ЗАКРЫТЫ**",
            description=f"Закрыто тикетов пользователя {user.mention}: **{len(closed_tickets)}**\n"
            f"Администратор: {interaction.user.mention}",
            color=discord.Color.green(),
        )
    else:
        embed = discord.Embed(
            title="ℹ️ **НЕТ АКТИВНЫХ ТИКЕТОВ**",
            description=f"У пользователя {user.mention} нет активных тикетов.",
            color=discord.Color.blue(),
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="list_queue", description="Показать текущую очередь (только для админов)"
)
async def list_queue(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ У вас нет прав администратора!", ephemeral=True
        )
        return

    if not queue_data:
        await interaction.response.send_message("📋 Очередь пуста!", ephemeral=True)
        return

    queue_list = []
    for i, user_id in enumerate(queue_data, 1):
        user = interaction.guild.get_member(int(user_id))
        if user:
            queue_list.append(f"{i}. {user.mention}")
        else:
            queue_list.append(f"{i}. <@{user_id}> (не на сервере)")

    embed = discord.Embed(
        title="📋 **ТЕКУЩАЯ ОЧЕРЕДЬ**",
        description="\n".join(queue_list),
        color=discord.Color.blue(),
    )
    embed.set_footer(text=f"Всего в очереди: {len(queue_data)}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="list_tickets", description="Показать все активные тикеты (только для админов)"
)
async def list_tickets(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ У вас нет прав администратора!", ephemeral=True
        )
        return

    open_tickets = []
    for ticket_id, ticket in tickets_data.items():
        if ticket.get("status") == "open":
            user_id = ticket.get("user_id")
            tester_id = ticket.get("tester_id")
            user = interaction.guild.get_member(int(user_id))
            tester = interaction.guild.get_member(int(tester_id)) if tester_id else None
            test_type = ticket.get("type", "qualified")
            nickname = ticket.get("nickname", "Не указан")
            created_at = datetime.fromisoformat(ticket.get("created_at"))

            # Проверяем возраст для высоких тикетов
            age_info = ""
            if test_type == "high":
                age = datetime.now() - created_at
                if age < timedelta(days=MIN_TICKET_DAYS):
                    remaining = timedelta(days=MIN_TICKET_DAYS) - age
                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    age_info = f" ⏳(мин.{hours}ч{minutes}мин)"
                else:
                    age_info = " ✅(можно закрыть)"

            open_tickets.append(
                f"**#{ticket_id}** | {user.mention if user else user_id} (`{nickname}`) | "
                f"Тестер: {tester.mention if tester else '?'} | "
                f"Тип: {'⭐ ВЫСОКИЙ' if test_type == 'high' else '📋 КВАЛИФ'}{age_info}"
            )

    if not open_tickets:
        await interaction.response.send_message(
            "📋 Активных тикетов нет!", ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🎫 **АКТИВНЫЕ ТИКЕТЫ**",
        description="\n".join(open_tickets),
        color=discord.Color.orange(),
    )
    embed.set_footer(
        text=f"Всего тикетов: {len(open_tickets)} | Для LT3+ тикетов мин. {MIN_TICKET_DAYS} дня(ей)"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="reset_cooldown", description="Сбросить КД пользователя (только для админов)"
)
async def reset_cooldown(
    interaction: discord.Interaction, user: discord.Member, test_type: str = "qualified"
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ У вас нет прав администратора!", ephemeral=True
        )
        return

    user_id = str(user.id)
    test_type = test_type.lower()

    embed = discord.Embed(color=discord.Color.green())

    if test_type == "qualified" or test_type == "квалиф":
        if user_id in qualified_cooldowns:
            del qualified_cooldowns[user_id]
            save_qualified_cooldowns()
            embed.title = "✅ **КД СБРОШЕН**"
            embed.description = f"КД на квалифицированные тесты пользователя {user.mention} успешно сброшен!"
        else:
            embed.title = "ℹ️ **НЕТ КД**"
            embed.description = f"У пользователя {user.mention} нет активного КД на квалифицированные тесты."
            embed.color = discord.Color.blue()
    elif test_type == "high" or test_type == "высокий":
        if user_id in high_cooldowns:
            del high_cooldowns[user_id]
            save_high_cooldowns()
            embed.title = "✅ **КД СБРОШЕН**"
            embed.description = (
                f"КД на высокие тесты пользователя {user.mention} успешно сброшен!"
            )
        else:
            embed.title = "ℹ️ **НЕТ КД**"
            embed.description = (
                f"У пользователя {user.mention} нет активного КД на высокие тесты."
            )
            embed.color = discord.Color.blue()
    else:
        embed.title = "❌ **ОШИБКА**"
        embed.description = "Укажите тип теста: `qualified` или `high`"
        embed.color = discord.Color.red()

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="reset_all_data",
    description="СБРОСИТЬ ВСЕ ДАННЫЕ (очередь, тикеты, КД, статистику)",
)
async def reset_all_data(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ У вас нет прав администратора!", ephemeral=True
        )
        return

    global \
        queue_data, \
        active_testers, \
        tickets_data, \
        qualified_cooldowns, \
        high_cooldowns, \
        tester_stats, \
        user_data, \
        support_tickets, \
        staff_applications

    # Очищаем все данные
    queue_data = []
    active_testers = {}
    tickets_data = {}
    support_tickets = {}
    staff_applications = {}
    qualified_cooldowns = {}
    high_cooldowns = {}
    tester_stats = {}
    user_data = {}

    # Сохраняем пустые данные в файлы
    save_queue()
    save_active_testers()
    save_tickets()
    save_support_tickets()
    save_staff_applications()
    save_qualified_cooldowns()
    save_high_cooldowns()
    save_tester_stats()
    save_user_data()

    # Снимаем роль WhiteList у всех
    whitelist_role = await get_role(interaction.guild, ROLE_WHITELIST)
    if whitelist_role:
        for member in interaction.guild.members:
            if whitelist_role in member.roles:
                try:
                    await member.remove_roles(whitelist_role)
                except:
                    pass

    # Обновляем отображение
    await update_queue_display(interaction.guild)
    await update_tester_month_display(interaction.guild)

    # Отправляем результат
    embed = discord.Embed(
        title="✅ **ВСЕ ДАННЫЕ СБРОШЕНЫ!**",
        description=f"Администратор: {interaction.user.mention}\n\n"
        f"**Было очищено:**\n"
        f"• Очередь\n"
        f"• Активные тестеры\n"
        f"• Все тикеты\n"
        f"• Все КД\n"
        f"• Статистика тестеров\n"
        f"• Данные пользователей\n"
        f"• Заявки в стаф\n"
        f"• Роли WhiteList у всех участников",
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ========== КОМАНДА ДЛЯ СОЗДАНИЯ СТРУКТУРЫ ==========
@bot.tree.command(name="setup_queues", description="Создать всю структуру для очередей")
async def setup_queues(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ У вас нет прав администратора!", ephemeral=True
        )
        return

    await interaction.response.send_message("🔄 Создаю структуру...", ephemeral=True)

    guild = interaction.guild

    roles_order = [
        (ROLE_HT2, discord.Color.pink(), True),
        (ROLE_LT2, discord.Color.teal(), True),
        (ROLE_HT3, discord.Color.orange(), True),
        (ROLE_LT3, discord.Color.gold(), True),
        (ROLE_HT4, discord.Color.red(), True),
        (ROLE_LT4, discord.Color.purple(), True),
        (ROLE_HT5, discord.Color.red(), True),
        (ROLE_LT5, discord.Color.purple(), True),
        (ROLE_SENIOR_TESTER, discord.Color.dark_green(), True),
        (ROLE_TESTER, discord.Color.green(), True),
        (ROLE_MODERATOR, discord.Color.blue(), True),
        (ROLE_ADMINISTRATOR, discord.Color.red(), True),
        (ROLE_MEMBER, discord.Color.blue(), True),
        (ROLE_WHITELIST, discord.Color.blue(), False),
    ]

    for role_name, color, hoist in roles_order:
        if not await get_role(guild, role_name):
            await guild.create_role(name=role_name, colour=color, hoist=hoist)

    tester_category = await guild.create_category("🛠️ Тестеры")

    tester_role = await get_role(guild, ROLE_TESTER)
    await guild.create_text_channel(
        CHANNEL_TESTER_COMMANDS,
        category=tester_category,
        overwrites={
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            tester_role: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
        },
    )

    senior_role = await get_role(guild, ROLE_SENIOR_TESTER)
    await guild.create_text_channel(
        CHANNEL_SENIOR_COMMANDS,
        category=tester_category,
        overwrites={
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            senior_role: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
        },
    )

    main_category = await guild.create_category("📋 Очереди и тесты")

    queue_channel = await guild.create_text_channel(
        CHANNEL_QUEUE, category=main_category
    )

    servers_text = "\n".join([f"   {s['flag']} `{s['address']}`" for s in SERVERS])

    embed = discord.Embed(
        title="📋 **ОЧЕРЕДЬ НА ТЕСТИРОВАНИЕ**",
        description=f"Нажмите на кнопку ниже, чтобы встать в очередь на тестирование.\n\n"
        f"⏱️ **КД квалифицированного теста:** {QUALIFIED_COOLDOWN_DAYS} дней\n"
        f"⏱️ **КД высокого теста:** {HIGH_COOLDOWN_DAYS} дней\n"
        f"⏱️ **Минимальная длительность LT3+ тикета:** {MIN_TICKET_DAYS} дня(ей)\n\n"
        f"**🌐 Доступные сервера:**\n{servers_text}\n\n"
        f"**🏆 Тиры для получения:**\n"
        f"• Квалифицированный тест: {', '.join(QUALIFIED_TIERS)}\n"
        f"• Высокий тест (после LT3): {', '.join(HIGH_TIERS)}\n\n"
        f"**⚠️ ВНИМАНИЕ:** Если у вас есть тир LT3 или выше (HT3, LT2, HT2), вы НЕ можете встать в очередь!",
        color=discord.Color.blue(),
    )
    msg = await queue_channel.send(embed=embed, view=QueueButton())

    # Сохраняем ID сообщения
    if str(guild.id) not in message_ids:
        message_ids[str(guild.id)] = {}
    message_ids[str(guild.id)]["queue_message_id"] = msg.id
    save_message_ids()

    testing_channel = await guild.create_text_channel(
        CHANNEL_TESTING, category=main_category
    )
    await guild.create_text_channel(CHANNEL_QUALIFIED_RESULTS, category=main_category)
    await guild.create_text_channel(CHANNEL_HIGH_RESULTS, category=main_category)
    month_channel = await guild.create_text_channel(
        CHANNEL_TESTER_MONTH, category=main_category
    )

    verification_channel = await guild.create_text_channel(
        CHANNEL_VERIFICATION, category=main_category
    )

    verify_embed = discord.Embed(
        title="✅ **ВЕРИФИКАЦИЯ**",
        description="Нажмите на кнопку ниже, чтобы пройти верификацию.\n\n"
        "**После верификации вы получите:**\n"
        "• Роль **Участник**\n"
        "• Ваш никнейм на сервере изменится на указанный",
        color=discord.Color.green(),
    )
    verify_msg = await verification_channel.send(
        embed=verify_embed, view=VerificationButton()
    )
    message_ids[str(guild.id)]["verification_message_id"] = verify_msg.id

    support_channel = await guild.create_text_channel(
        CHANNEL_SUPPORT, category=main_category
    )

    support_embed = discord.Embed(
        title="🎫 **ПОДДЕРЖКА**",
        description="**Нажми на кнопку ниже, чтобы создать обращение в поддержку.**\n\n"
        "**📋 ПО КАКИМ ВОПРОСАМ:**\n"
        "• Жалобы на участников\n"
        "• Жалобы на Verified Tester\n"
        "• Вопросы к администрации\n"
        "• Технические проблемы\n"
        "• Предложения по серверу\n\n"
        "⏱️ **Время ответа:** до 24 часов",
        color=discord.Color.blue(),
    )
    support_msg = await support_channel.send(
        embed=support_embed, view=SupportTicketButton()
    )
    message_ids[str(guild.id)]["support_message_id"] = support_msg.id

    staff_channel = await guild.create_text_channel(
        CHANNEL_STAFF, category=main_category
    )

    staff_embed = discord.Embed(
        title="👥 **СТАФ СЕРВЕРА**",
        description="Здесь будут публиковаться новые назначения и снятия стаффа.",
        color=discord.Color.gold(),
    )
    await staff_channel.send(embed=staff_embed)

    staff_applications_channel = await guild.create_text_channel(
        CHANNEL_STAFF_APPLICATIONS, category=main_category
    )

    staff_app_embed = discord.Embed(
        title="📝 **ЗАЯВКИ В СТАФ**",
        description="**Нажми на кнопку ниже, чтобы подать заявку на вступление в стаф.**\n\n"
        "**⚠️ ТРЕБОВАНИЯ:**\n"
        "• Наличие роли **LT3** или выше (LT3, HT3, LT2, HT2)\n"
        "• Активность на сервере\n"
        "• Знание правил сервера\n\n"
        "**📋 РОЛЬ, КОТОРУЮ МОЖНО ПОЛУЧИТЬ:**\n"
        "• Verified Tester\n\n"
        "⏱️ **Время рассмотрения:** до 7 дней\n"
        "👑 **Рассматривает заявки только администратор!**",
        color=discord.Color.purple(),
    )
    staff_app_msg = await staff_applications_channel.send(
        embed=staff_app_embed, view=StaffApplicationButton()
    )
    message_ids[str(guild.id)]["staff_applications_message_id"] = staff_app_msg.id

    save_message_ids()

    await update_queue_display(interaction.guild)
    await update_tester_month_display(interaction.guild)

    embed_result = discord.Embed(
        title="✅ **СТРУКТУРА СОЗДАНА!**",
        description="Все каналы и роли созданы!\n\n"
        f"**Важно:** Для LT3+ тикетов установлена минимальная длительность - **{MIN_TICKET_DAYS} дня(ей)**.\n"
        f"Тикеты можно закрыть командой `/close` только после истечения этого времени.\n"
        f"Для принудительного закрытия используйте `/forceclose` (только админы).",
        color=discord.Color.green(),
    )
    await interaction.edit_original_response(embed=embed_result)


# ========== СОБЫТИЕ ПРИ ДОБАВЛЕНИИ БОТА НА СЕРВЕР ==========
@bot.event
async def on_guild_join(guild: discord.Guild):
    print(f"✅ Бот добавлен на сервер: {guild.name}")

    bot_role = None
    for role in guild.roles:
        if role.name == "Bot" or role == guild.me.top_role:
            bot_role = role
            break

    if not bot_role:
        try:
            bot_role = await guild.create_role(
                name="Bot",
                permissions=discord.Permissions(
                    manage_nicknames=True,
                    manage_roles=True,
                    manage_channels=True,
                    manage_messages=True,
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True,
                    mention_everyone=True,
                    moderate_members=True,
                    move_members=True,
                    mute_members=True,
                    deafen_members=True,
                    kick_members=True,
                    ban_members=True,
                ),
                colour=discord.Color.blue(),
                hoist=True,
            )
            print(f"✅ Соз@�ана роль Bot с правами")
        except Exception as e:
            print(f"❌ Ошибка создания роли: {e}")

    if bot_role:
        try:
            roles = guild.roles
            roles_sorted = sorted(roles, key=lambda r: r.position, reverse=True)

            highest_role = None
            for role in roles_sorted:
                if role.name != "@everyone" and role != bot_role:
                    highest_role = role
                    break

            if highest_role and bot_role.position <= highest_role.position:
                await bot_role.edit(position=highest_role.position + 1)
                print(f"✅ Роль бота поднята выше {highest_role.name}")
        except Exception as e:
            print(f"❌ Ошибка поднятия роли: {e}")

    try:
        if bot_role and bot_role not in guild.me.roles:
            await guild.me.add_roles(bot_role)
            print(f"✅ Боту выдана роль {bot_role.name}")
    except Exception as e:
        print(f"❌ Ошибка выдачи роли боту: {e}")

    system_channel = guild.system_channel
    if system_channel:
        embed = discord.Embed(
            title="✅ **БОТ УСПЕШНО НАСТРОЕН**",
            description="Бот автоматически настроил свои права!\n\n"
            f"**Что сделано:**\n"
            f"• Создана роль `Bot` с необходимыми правами\n"
            f"• Роль бота поднята выше всех остальных\n"
            f"• Настроены права на управление никами\n\n"
            f"**Для завершения настройки:**\n"
            f"• Используйте команду `/setup_queues` для создания каналов\n"
            f"• Используйте команду `/sync` для синхронизации команд\n\n"
            f"**Нововведения:**\n"
            f"• LT3+ тикеты теперь требуют минимум {MIN_TICKET_DAYS} дня(ей) для закрытия\n"
            f"• Сообщения очереди и лидерборда сохраняются после перезапуска",
            color=discord.Color.green(),
        )
        await system_channel.send(embed=embed)


# ========== КОМАНДА ДЛЯ ПРОВЕРКИ ПРАВ ==========
@bot.tree.command(
    name="check_permissions", description="Проверить права бота на сервере"
)
async def check_permissions(interaction: discord.Interaction):
    bot_member = interaction.guild.me

    permissions_to_check = {
        "manage_nicknames": "Управление никами",
        "manage_roles": "Управление ролями",
        "manage_channels": "Управление каналами",
        "manage_messages": "Управление сообщениями",
        "moderate_members": "Модерация участников",
    }

    embed = discord.Embed(title="🔧 **ПРОВЕРКА ПРАВ БОТА**", color=discord.Color.blue())

    for perm, name in permissions_to_check.items():
        if getattr(bot_member.guild_permissions, perm, False):
            embed.add_field(name=f"✅ {name}", value="Есть", inline=True)
        else:
            embed.add_field(name=f"❌ {name}", value="Нет", inline=True)

    embed.add_field(
        name="📊 Позиция роли",
        value=f"Роль бота: `{bot_member.top_role.name}`\nПозиция: `{bot_member.top_role.position}`",
        inline=False,
    )

    if not bot_member.guild_permissions.manage_nicknames:
        embed.add_field(
            name="⚠️ **ТРЕБУЮТСЯ ПРАВА**",
            value="У бота нет права **Управление никами**!\n\n"
            "**Как исправить:**\n"
            "1. Используйте команду `/setup_bot_permissions`\n"
            "2. Или вручную: Настройки сервера → Роли\n"
            "3. Найдите роль `Bot` и включите нужные права",
            inline=False,
        )
        embed.color = discord.Color.orange()

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ========== КОМАНДА ДЛЯ АВТОНАСТРОЙКИ ПРАВ ==========
@bot.tree.command(
    name="setup_bot_permissions",
    description="Автоматически настроить права бота (только для админов)",
)
async def setup_bot_permissions(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ У вас нет прав администратора!", ephemeral=True
        )
        return

    await interaction.response.send_message("🔄 Настройка прав бота...", ephemeral=True)

    guild = interaction.guild
    bot_member = guild.me

    bot_role = None
    for role in guild.roles:
        if role.name == "Bot" and role != bot_member.top_role:
            bot_role = role
            break

    if not bot_role:
        try:
            bot_role = await guild.create_role(
                name="Bot",
                permissions=discord.Permissions(
                    manage_nicknames=True,
                    manage_roles=True,
                    manage_channels=True,
                    manage_messages=True,
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True,
                    mention_everyone=False,
                    moderate_members=True,
                    move_members=True,
                    mute_members=True,
                    deafen_members=True,
                    kick_members=True,
                    ban_members=True,
                ),
                colour=discord.Color.blue(),
                hoist=True,
            )
            await bot_member.add_roles(bot_role)
            embed = discord.Embed(
                title="✅ **РОЛЬ СОЗДАНА**",
                description=f"Создана роль `{bot_role.name}` с необходимыми правами",
                color=discord.Color.green(),
            )
            await interaction.edit_original_response(embed=embed)
        except Exception as e:
            await interaction.edit_original_response(
                content=f"❌ Ошибка создания роли: {e}"
            )
            return
    else:
        try:
            await bot_role.edit(
                permissions=discord.Permissions(
                    manage_nicknames=True,
                    manage_roles=True,
                    manage_channels=True,
                    manage_messages=True,
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True,
                    moderate_members=True,
                    move_members=True,
                    mute_members=True,
                    deafen_members=True,
                    kick_members=True,
                    ban_members=True,
                )
            )
            embed = discord.Embed(
                title="✅ **ПРАВА ОБНОВЛЕНЫ**",
                description=f"Обновлены права для роли `{bot_role.name}`",
                color=discord.Color.green(),
            )
            await interaction.edit_original_response(embed=embed)
        except Exception as e:
            await interaction.edit_original_response(
                content=f"❌ Ошибка обновления прав: {e}"
            )
            return

    try:
        highest_member_role = None
        for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
            if role.name != "@everyone" and role != bot_role:
                highest_member_role = role
                break

        if highest_member_role and bot_role.position <= highest_member_role.position:
            await bot_role.edit(position=highest_member_role.position + 1)
            embed = discord.Embed(
                title="✅ **РОЛЬ ПОДНЯТА**",
                description=f"Роль бота поднята выше `{highest_member_role.name}`",
                color=discord.Color.green(),
            )
            await interaction.edit_original_response(embed=embed)
    except Exception as e:
        await interaction.edit_original_response(
            content=f"⚠️ Не удалось поднять роль: {e}"
        )

    final_embed = discord.Embed(
        title="✅ **НАСТРОЙКА ЗАВЕРШЕНА**",
        description="Права бота успешно настроены!\n\n"
        f"**Теперь бот может:**\n"
        f"• ✅ Менять никнеймы пользователей\n"
        f"• ✅ Управлять ролями\n"
        f"• ✅ Создавать и управлять каналами\n"
        f"• ✅ Модерировать участников\n\n"
        f"**Для создания структуры сервера:**\n"
        f"• Используйте команду `/setup_queues`",
        color=discord.Color.green(),
    )
    await interaction.edit_original_response(embed=final_embed)


# ========== КОМАНДА ДЛЯ РУЧНОЙ СИНХРОНИЗАЦИИ ==========
@bot.tree.command(
    name="sync", description="Принудительная синхронизация команд (только для админов)"
)
async def sync_commands(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ У вас нет прав на использование этой команды!", ephemeral=True
        )
        return

    await interaction.response.send_message(
        "🔄 Синхронизация команд...", ephemeral=True
    )

    try:
        await bot.tree.sync(guild=interaction.guild)
        synced = await bot.tree.sync()

        commands_list = "\n".join([f"  - /{cmd.name}" for cmd in synced])

        embed = discord.Embed(
            title="✅ **КОМАНДЫ СИНХРОНИЗИРОВАНЫ**",
            description=f"Всего команд: **{len(synced)}**\n\n{commands_list}",
            color=discord.Color.green(),
        )
        await interaction.edit_original_response(embed=embed)

    except Exception as e:
        await interaction.edit_original_response(
            content=f"❌ Ошибка синхронизации: {e}"
        )


# ========== КОМАНДА !txt (УПРОЩЁННАЯ, БЕЗ ВРЕМЕНИ И ИКОНОК) ==========
@bot.command(name="txt")
@commands.has_permissions(administrator=True)
async def txt_command(ctx, channel: discord.TextChannel, *, message: str):
    """Отправить красивое embed сообщение в указанный канал"""
    try:
        # Проверяем, является ли сообщение JSON для embed
        if message.strip().startswith("{") and message.strip().endswith("}"):
            try:
                import json

                embed_data = json.loads(message)
                embed = discord.Embed.from_dict(embed_data)
                await channel.send(embed=embed)
            except:
                embed = discord.Embed(
                    title="📢 **ОБЪЯВЛЕНИЕ**",
                    description=message,
                    color=discord.Color.blue(),
                )
                await channel.send(embed=embed)
        else:
            # Создаём простой embed без времени и иконок
            embed = discord.Embed(description=message, color=discord.Color.blue())

            await channel.send(embed=embed)

        # Подтверждение для админа
        confirm_embed = discord.Embed(
            title="✅ **СООБЩЕНИЕ ОТПРАВЛЕНО**",
            description=f"Сообщение отправлено в {channel.mention}",
            color=discord.Color.green(),
        )
        await ctx.send(embed=confirm_embed, delete_after=5)

    except discord.Forbidden:
        error_embed = discord.Embed(
            title="❌ **ОШИБКА**",
            description=f"Нет прав для отправки сообщения в канал {channel.mention}",
            color=discord.Color.red(),
        )
        await ctx.send(embed=error_embed, delete_after=5)
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ **ОШИБКА**",
            description=f"Произошла ошибка: {e}",
            color=discord.Color.red(),
        )
        await ctx.send(embed=error_embed, delete_after=5)


# ========== ДОПОЛНИТЕЛЬНАЯ КОМАНДА ДЛЯ EMBED ==========
@bot.command(name="embed")
@commands.has_permissions(administrator=True)
async def embed_command(
    ctx, channel: discord.TextChannel, color: str = "blue", *, message: str
):
    """Отправить кастомный embed
    Использование: !embed #канал цвет текст
    Доступные цвета: blue, green, red, orange, gold, purple
    """
    colors = {
        "blue": discord.Color.blue(),
        "green": discord.Color.green(),
        "red": discord.Color.red(),
        "orange": discord.Color.orange(),
        "gold": discord.Color.gold(),
        "purple": discord.Color.purple(),
    }

    embed_color = colors.get(color.lower(), discord.Color.blue())

    # Разделяем на заголовок и описание если есть |
    if " | " in message:
        title, description = message.split(" | ", 1)
        embed = discord.Embed(
            title=title,
            description=description,
            color=embed_color,
            timestamp=datetime.now(),
        )
    else:
        embed = discord.Embed(
            description=message, color=embed_color, timestamp=datetime.now()
        )

    embed.set_footer(text=f"Отправлено: {ctx.author.display_name}")

    await channel.send(embed=embed)

    confirm_embed = discord.Embed(
        title="✅ **СООБЩЕНИЕ ОТПРАВЛЕНО**",
        description=f"Embed отправлен в {channel.mention}",
        color=discord.Color.green(),
    )
    await ctx.send(embed=confirm_embed, delete_after=5)


# ========== КОМАНДА ДЛЯ ПРОВЕРКИ СТАТУСА ТИКЕТА ==========
@bot.tree.command(
    name="ticket_info", description="Показать информацию о текущем тикете"
)
async def ticket_info(interaction: discord.Interaction):
    """Показывает информацию о текущем тикете (возраст, можно ли закрывать)"""

    ticket_id = None
    for tid, ticket in tickets_data.items():
        if (
            ticket.get("channel_id") == interaction.channel.id
            and ticket.get("status") == "open"
        ):
            ticket_id = tid
            break

    if not ticket_id:
        embed = discord.Embed(
            title="❌ **ОШИБКА**",
            description="Этот канал не является активным тикетом!",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    ticket = tickets_data[ticket_id]
    test_type = ticket.get("type", "qualified")
    created_at = datetime.fromisoformat(ticket.get("created_at"))
    age = datetime.now() - created_at

    embed = discord.Embed(
        title="📊 **ИНФОРМАЦИЯ О ТИКЕТЕ**", color=discord.Color.blue()
    )

    embed.add_field(name="🆔 ID тикета", value=ticket_id, inline=True)
    embed.add_field(
        name="📋 Тип теста",
        value="⭐ ВЫСОКИЙ" if test_type == "high" else "📋 КВАЛИФИЦИРОВАННЫЙ",
        inline=True,
    )
    embed.add_field(
        name="📅 Создан", value=f"<t:{int(created_at.timestamp())}:F>", inline=True
    )
    embed.add_field(
        name="⏱️ Возраст",
        value=f"{age.days}д {age.seconds // 3600}ч {(age.seconds % 3600) // 60}мин",
        inline=True,
    )

    if test_type == "high":
        required = timedelta(days=MIN_TICKET_DAYS)
        if age >= required:
            embed.add_field(
                name="✅ Статус",
                value="Тикет можно закрыть командой `/close`",
                inline=False,
            )
            embed.color = discord.Color.green()
        else:
            remaining = required - age
            embed.add_field(
                name="⏳ Статус",
                value=f"Тикет можно будет закрыть через {remaining.days}д {remaining.seconds // 3600}ч {(remaining.seconds % 3600) // 60}мин",
                inline=False,
            )
            embed.color = discord.Color.orange()
    else:
        embed.add_field(
            name="✅ Статус",
            value="Тикет можно закрыть командой `/close`",
            inline=False,
        )
        embed.color = discord.Color.green()

    tester_id = ticket.get("tester_id")
    if tester_id:
        tester = interaction.guild.get_member(int(tester_id))
        embed.add_field(
            name="👤 Тестер",
            value=tester.mention if tester else "Неизвестно",
            inline=True,
        )
    else:
        embed.add_field(name="👤 Тестер", value="Не назначен", inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ========== СОБЫТИЕ ON_READY ==========
@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущен!")
    print(f"📁 Загружены сохранённые ID сообщений: {len(message_ids)} серверов")

    for guild in bot.guilds:
        try:
            await bot.tree.sync(guild=guild)
            print(f"✅ Команды синхронизированы для {guild.name}")
        except Exception as e:
            print(f"❌ Ошибка синхронизации для {guild.name}: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"🔄 Всего команд: {len(synced)}")
        for cmd in synced:
            print(f"  - /{cmd.name}")
    except Exception as e:
        print(f"❌ Ошибка глобальной синхронизации: {e}")

    for guild in bot.guilds:
        # Восстанавливаем сообщение верификации
        verification_channel = await get_channel(guild, CHANNEL_VERIFICATION)
        if verification_channel:
            embed = discord.Embed(
                title="✅ **ВЕРИФИКАЦИЯ**",
                description="Нажмите на кнопку ниже, чтобы пройти верификацию.\n\n"
                "**После верификации вы получите:**\n"
                "• Роль **Участник**\n"
                "• Ваш никнейм на сервере изменится на указанный",
                color=discord.Color.green(),
            )
            await edit_or_create_message(
                verification_channel,
                guild.id,
                "verification_message_id",
                embed,
                view=VerificationButton(),
                auto_create=False,
            )

        # Восстанавливаем сообщение поддержки
        support_channel = await get_channel(guild, CHANNEL_SUPPORT)
        if support_channel:
            embed = discord.Embed(
                title="🎫 **ПОДДЕРЖКА**",
                description="**Нажми на кнопку ниже, чтобы создать обращение в поддержку.**\n\n"
                "**📋 ПО КАКИМ ВОПРОСАМ:**\n"
                "• Жалобы на участников\n"
                "• Жалобы на Verified Tester\n"
                "• Вопросы к администрации\n"
                "• Технические проблемы\n"
                "• Предложения по серверу\n\n"
                "⏱️ **Время ответа:** до 24 часов",
                color=discord.Color.blue(),
            )
            await edit_or_create_message(
                support_channel,
                guild.id,
                "support_message_id",
                embed,
                view=SupportTicketButton(),
                auto_create=False,
            )

        # Восстанавливаем сообщение заявок в стаф
        staff_app_channel = await get_channel(guild, CHANNEL_STAFF_APPLICATIONS)
        if staff_app_channel:
            embed = discord.Embed(
                title="📝 **ЗАЯВКИ В СТАФ**",
                description="**Нажми на кнопку ниже, чтобы подать заявку на вступление в стаф.**\n\n"
                "**⚠️ ТРЕБОВАНИЯ:**\n"
                "• Наличие роли **LT3** или выше (LT3, HT3, LT2, HT2)\n"
                "• Активность на сервере\n"
                "• Знание правил сервера\n\n"
                "**📋 РОЛЬ, КОТОРУЮ МОЖНО ПОЛУЧИТЬ:**\n"
                "• Verified Tester\n\n"
                "⏱️ **Время рассмотрения:** до 7 дней\n"
                "👑 **Рассматривает заявки только администратор!**",
                color=discord.Color.purple(),
            )
            await edit_or_create_message(
                staff_app_channel,
                guild.id,
                "staff_applications_message_id",
                embed,
                view=StaffApplicationButton(),
                auto_create=False,
            )

        # Восстанавливаем сообщение очереди
        queue_channel = await get_channel(guild, CHANNEL_QUEUE)
        if queue_channel:
            servers_text = "\n".join(
                [f"   {s['flag']} `{s['address']}`" for s in SERVERS]
            )
            embed = discord.Embed(
                title="📋 **ОЧЕРЕДЬ НА ТЕСТИРОВАНИЕ**",
                description=f"Нажмите на кнопку ниже, чтобы встать в очередь на тестирование.\n\n"
                f"⏱️ **КД квалифицированного теста:** {QUALIFIED_COOLDOWN_DAYS} дней\n"
                f"⏱️ **КД высокого теста:** {HIGH_COOLDOWN_DAYS} дней\n"
                f"⏱️ **Минимальная длительность LT3+ тикета:** {MIN_TICKET_DAYS} дня(ей)\n\n"
                f"**🌐 Доступные сервера:**\n{servers_text}\n\n"
                f"**🏆 Тиры для получения:**\n"
                f"• Квалифицированный тест: {', '.join(QUALIFIED_TIERS)}\n"
                f"• Высокий тест (после LT3): {', '.join(HIGH_TIERS)}\n\n"
                f"**⚠️ ВНИМАНИЕ:** Если у вас есть тир LT3 или выше (HT3, LT2, HT2), вы НЕ можете встать в очередь!",
                color=discord.Color.blue(),
            )
            await edit_or_create_message(
                queue_channel,
                guild.id,
                "queue_message_id",
                embed,
                view=QueueButton(),
                auto_create=False,
            )

    await update_queue_display()
    await update_tester_month_display()

    print(
        f"✅ Бот готов к работе! Минимальная длительность LT3+ тикетов: {MIN_TICKET_DAYS} дня(ей)"
    )


# ========== СОБЫТИЕ ON_MEMBER_UPDATE ==========
@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    before_roles = set(before.roles)
    after_roles = set(after.roles)

    tracked_roles = [
        ROLE_ADMINISTRATOR,
        ROLE_MODERATOR,
        ROLE_SENIOR_TESTER,
        ROLE_TESTER,
    ]

    for role_name in tracked_roles:
        role = discord.utils.get(after.guild.roles, name=role_name)
        if not role:
            continue

        if role not in before_roles and role in after_roles:
            await send_staff_announcement(after, role_name, is_add=True)

        if role in before_roles and role not in after_roles:
            await send_staff_announcement(after, role_name, is_add=False)


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🚀 Запуск бота...")
    bot.run(TOKEN)
