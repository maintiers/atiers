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
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Конфигурация двух серверов
SERVERS = {
    "netherop": {
        "server_id": 1489937461974011934,
        "log_channel_id": 1490066076829094189,
        "name": "NetherOP",
        "role_to_tier": {
            1489937461986463868: {"tier": "Tier 1", "sub_tier": "LT1"},
            1489937461986463869: {"tier": "Tier 1", "sub_tier": "HT1"},
            1489937617461186630: {"tier": "Tier 2", "sub_tier": "LT2"},
            1489937616328462337: {"tier": "Tier 2", "sub_tier": "HT2"},
            1489937619818250342: {"tier": "Tier 3", "sub_tier": "LT3"},
            1489937618660753542: {"tier": "Tier 3", "sub_tier": "HT3"},
            1489937623085748254: {"tier": "Tier 4", "sub_tier": "LT4"},
            1489937621143519429: {"tier": "Tier 4", "sub_tier": "HT4"},
            1489937625644142622: {"tier": "Tier 5", "sub_tier": "LT5"},
            1489937624364879922: {"tier": "Tier 5", "sub_tier": "HT5"},
        },
    },
    "beast": {
        "server_id": 1490802616349753384,
        "log_channel_id": 1490802618031931488,
        "name": "Beast",
        "role_to_tier": {
            1490802616370855958: {"tier": "Tier 1", "sub_tier": "LT1"},
            1490802616370855959: {"tier": "Tier 1", "sub_tier": "HT1"},
            1490802616370855956: {"tier": "Tier 2", "sub_tier": "LT2"},
            1490802616370855957: {"tier": "Tier 2", "sub_tier": "HT2"},
            1490802616349753392: {"tier": "Tier 3", "sub_tier": "LT3"},
            1490802616349753393: {"tier": "Tier 3", "sub_tier": "HT3"},
            1490802616349753390: {"tier": "Tier 4", "sub_tier": "LT4"},
            1490802616349753391: {"tier": "Tier 4", "sub_tier": "HT4"},
            1490802616349753388: {"tier": "Tier 5", "sub_tier": "LT5"},
            1490802616349753389: {"tier": "Tier 5", "sub_tier": "HT5"},
        },
    },
}

WEBSITE_URL = "http://localhost:5000"  # URL вашего сайта

# Настройки повторных попыток
MAX_RETRIES = 5
RETRY_DELAY = 3

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def send_to_website(
    action, discord_id, username=None, tier=None, sub_tier=None, server="netherop"
):
    """Отправка данных на сайт с повторными попытками"""
    for attempt in range(MAX_RETRIES):
        try:
            data = {
                "action": action,
                "server": server,
                "discord_id": str(discord_id),
                "username": username,
                "tier": tier,
                "sub_tier": sub_tier,
            }
            response = requests.post(f"{WEBSITE_URL}/api/sync", json=data, timeout=10)
            if response.status_code == 200:
                print(
                    f"[✓] [{server.upper()}] {action} - {username} ({tier} - {sub_tier})"
                )
                return True
            else:
                print(
                    f"[✗] [{server.upper()}] Ошибка {response.status_code}, попытка {attempt + 1}/{MAX_RETRIES}"
                )
        except requests.exceptions.ConnectionError:
            print(
                f"[✗] [{server.upper()}] Не могу подключиться к сайту! Убедитесь, что сайт запущен на {WEBSITE_URL}"
            )
        except Exception as e:
            print(
                f"[✗] [{server.upper()}] Ошибка: {e}, попытка {attempt + 1}/{MAX_RETRIES}"
            )

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)

    return False


def get_server_config(guild_id):
    """Получить конфигурацию сервера по ID"""
    for server_key, config in SERVERS.items():
        if config["server_id"] == guild_id:
            return server_key, config
    return None, None


@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущен!")
    print(f"📡 Отслеживается {len(SERVERS)} серверов:")
    print("=" * 50)

    for server_key, config in SERVERS.items():
        guild = bot.get_guild(config["server_id"])
        if guild:
            print(f"   ✅ {config['name']}")
            print(f"      • Название: {guild.name}")
            print(f"      • Участников: {len(guild.members)}")
            print(f"      • Тиров: {len(config['role_to_tier'])}")

            # Отправляем приветствие в лог-канал
            channel = bot.get_channel(config["log_channel_id"])
            if channel:
                await channel.send(
                    f"✅ **Бот синхронизации запущен для {config['name']}!**\n"
                    f"📡 Отслеживается {len(config['role_to_tier'])} тиров\n"
                    f"🌐 Сайт: {WEBSITE_URL}"
                )
        else:
            print(f"   ❌ {config['name']} - сервер не найден! Проверьте ID сервера")

    print("=" * 50)
    print(f"🌐 Сайт для синхронизации: {WEBSITE_URL}")
    print("💾 Данные сохраняются в базе данных сайта и не теряются при перезапуске")


@bot.event
async def on_member_update(before, after):
    """Отслеживание изменений ролей у участника"""
    # Определяем сервер
    server_key, config = get_server_config(after.guild.id)
    if not config:
        return

    before_roles = set(before.roles)
    after_roles = set(after.roles)

    added_roles = after_roles - before_roles
    removed_roles = before_roles - after_roles

    channel = bot.get_channel(config["log_channel_id"])

    # Обработка выданных ролей
    for role in added_roles:
        if role.id in config["role_to_tier"]:
            tier_info = config["role_to_tier"][role.id]
            success = send_to_website(
                "add",
                after.id,
                after.display_name,
                tier_info["tier"],
                tier_info["sub_tier"],
                server_key,
            )
            if success and channel:
                await channel.send(
                    f"🎉 **{after.display_name}** получил роль **{role.name}** "
                    f"→ {tier_info['tier']} ({tier_info['sub_tier']}) → сайт обновлён!"
                )

    # Обработка снятых ролей
    for role in removed_roles:
        if role.id in config["role_to_tier"]:
            success = send_to_website("remove", after.id, server=server_key)
            if success and channel:
                await channel.send(
                    f"📤 **{after.display_name}** лишился роли **{role.name}** "
                    f"→ удалён из тир-листа {config['name']}!"
                )


@bot.command()
async def sync(ctx, target_server=None):
    """Принудительная синхронизация всех участников
    Использование: !sync [netherop/beast/all]"""

    # Определяем текущий сервер
    current_server_key, current_config = get_server_config(ctx.guild.id)

    # Выбираем серверы для синхронизации
    servers_to_sync = []
    if target_server == "all":
        servers_to_sync = list(SERVERS.items())
        await ctx.send(f"🔄 Начинаю синхронизацию ВСЕХ серверов...")
    elif target_server in SERVERS:
        servers_to_sync = [(target_server, SERVERS[target_server])]
        await ctx.send(
            f"🔄 Начинаю синхронизацию сервера {SERVERS[target_server]['name']}..."
        )
    else:
        # Если не указан, синхронизируем текущий сервер
        servers_to_sync = [(current_server_key, current_config)]
        await ctx.send(
            f"🔄 Начинаю синхронизацию текущего сервера {current_config['name']}..."
        )

    total_count = 0
    for server_key, config in servers_to_sync:
        guild = bot.get_guild(config["server_id"])
        if not guild:
            await ctx.send(f"❌ Сервер {config['name']} не найден!")
            continue

        await ctx.send(f"📡 Синхронизирую {config['name']}...")
        count = 0

        for member in guild.members:
            for role in member.roles:
                if role.id in config["role_to_tier"]:
                    tier_info = config["role_to_tier"][role.id]
                    send_to_website(
                        "add",
                        member.id,
                        member.display_name,
                        tier_info["tier"],
                        tier_info["sub_tier"],
                        server_key,
                    )
                    count += 1
                    break

        total_count += count
        await ctx.send(f"✅ {config['name']}: синхронизировано {count} игроков.")

        # Отправляем лог в канал
        channel = bot.get_channel(config["log_channel_id"])
        if channel:
            await channel.send(
                f"📊 **Синхронизация завершена!** Обработано {count} игроков."
            )

    await ctx.send(
        f"🎉 Синхронизация завершена! Всего обработано {total_count} игроков."
    )


@bot.command()
async def sync_member(ctx, member: discord.Member, target_server=None):
    """Синхронизация конкретного участника
    Использование: !sync_member @участник [netherop/beast]"""

    # Определяем сервер для синхронизации
    if target_server and target_server in SERVERS:
        server_key = target_server
        config = SERVERS[target_server]
        guild = bot.get_guild(config["server_id"])

        if not guild:
            await ctx.send(f"❌ Сервер {config['name']} не найден!")
            return

        # Ищем участника на другом сервере
        target_member = guild.get_member(member.id)
        if not target_member:
            await ctx.send(
                f"❌ Участник {member.display_name} не найден на сервере {config['name']}!"
            )
            return

        await ctx.send(
            f"🔄 Синхронизирую {target_member.display_name} с сервером {config['name']}..."
        )

        count = 0
        for role in target_member.roles:
            if role.id in config["role_to_tier"]:
                tier_info = config["role_to_tier"][role.id]
                send_to_website(
                    "add",
                    target_member.id,
                    target_member.display_name,
                    tier_info["tier"],
                    tier_info["sub_tier"],
                    server_key,
                )
                count += 1
                break

        if count > 0:
            await ctx.send(
                f"✅ {target_member.display_name} синхронизирован с {config['name']}!"
            )
        else:
            await ctx.send(
                f"⚠️ У {target_member.display_name} нет тир-ролей на сервере {config['name']}!"
            )

    else:
        # Синхронизируем на текущем сервере
        current_server_key, config = get_server_config(ctx.guild.id)

        count = 0
        for role in member.roles:
            if role.id in config["role_to_tier"]:
                tier_info = config["role_to_tier"][role.id]
                send_to_website(
                    "add",
                    member.id,
                    member.display_name,
                    tier_info["tier"],
                    tier_info["sub_tier"],
                    current_server_key,
                )
                count += 1
                break

        if count > 0:
            await ctx.send(
                f"✅ {member.display_name} синхронизирован с {config['name']}!"
            )
        else:
            await ctx.send(f"⚠️ У {member.display_name} нет тир-ролей!")


@bot.command()
async def sync_all_members(ctx):
    """Полная синхронизация всех участников на всех серверах"""
    await ctx.send("🔄 Начинаю ПОЛНУЮ синхронизацию всех серверов...")
    await ctx.send("⏳ Это может занять некоторое время...")

    total_count = 0
    for server_key, config in SERVERS.items():
        guild = bot.get_guild(config["server_id"])
        if not guild:
            await ctx.send(f"❌ Сервер {config['name']} не найден!")
            continue

        await ctx.send(
            f"📡 Синхронизирую {config['name']} ({len(guild.members)} участников)..."
        )
        count = 0

        for member in guild.members:
            for role in member.roles:
                if role.id in config["role_to_tier"]:
                    tier_info = config["role_to_tier"][role.id]
                    send_to_website(
                        "add",
                        member.id,
                        member.display_name,
                        tier_info["tier"],
                        tier_info["sub_tier"],
                        server_key,
                    )
                    count += 1
                    break

        total_count += count
        await ctx.send(f"✅ {config['name']}: синхронизировано {count} игроков.")

        # Отправляем лог в канал
        channel = bot.get_channel(config["log_channel_id"])
        if channel:
            await channel.send(
                f"📊 **Полная синхронизация {config['name']} завершена!** Обработано {count} игроков."
            )

    await ctx.send(
        f"🎉 Полная синхронизация завершена! Всего обработано {total_count} игроков."
    )
    await ctx.send("💾 Все данные сохранены в базе данных сайта!")


@bot.command()
async def servers(ctx):
    """Показать список отслеживаемых серверов"""
    embed = discord.Embed(title="📡 Отслеживаемые серверы", color=0x00FF00)

    for server_key, config in SERVERS.items():
        guild = bot.get_guild(config["server_id"])
        if guild:
            status = "✅ Онлайн"
            member_count = len(guild.members)
        else:
            status = "❌ Оффлайн"
            member_count = 0

        embed.add_field(
            name=f"{config['name']} ({server_key})",
            value=f"Статус: {status}\nУчастников: {member_count}\nТиров: {len(config['role_to_tier'])}",
            inline=False,
        )

    embed.set_footer(text="Данные сохраняются в базе данных сайта")
    await ctx.send(embed=embed)


@bot.command()
async def status(ctx):
    """Статус бота"""
    embed = discord.Embed(title="✅ Статус бота", color=0x00FF00)
    embed.add_field(name="Серверов", value=len(SERVERS), inline=True)
    embed.add_field(
        name="Всего тиров",
        value=sum(len(c["role_to_tier"]) for c in SERVERS.values()),
        inline=True,
    )
    embed.add_field(name="Сайт", value=WEBSITE_URL, inline=False)
    embed.add_field(
        name="Сохранение данных", value="✅ В базе данных SQLite", inline=False
    )
    embed.set_footer(text="Данные не теряются при перезапуске бота или сайта")

    await ctx.send(embed=embed)


@bot.command()
async def test_sync(ctx, server="netherop"):
    """Тестовая синхронизация
    Использование: !test_sync [netherop/beast]"""

    if server not in SERVERS:
        await ctx.send(
            f"❌ Сервер {server} не найден! Доступные: {', '.join(SERVERS.keys())}"
        )
        return

    test_user = ctx.author
    config = SERVERS[server]
    await ctx.send(
        f"🧪 Тестовая синхронизация для {test_user.display_name} на сервере {config['name']}..."
    )

    # Отправляем тестовые данные
    success = send_to_website(
        "add", test_user.id, test_user.display_name, "Tier 3", "HT3", server
    )

    if success:
        await ctx.send(
            f"✅ Тестовые данные отправлены на сайт для сервера {config['name']}!"
        )
    else:
        await ctx.send(
            f"❌ Не удалось отправить данные! Убедитесь, что сайт запущен на {WEBSITE_URL}"
        )


@bot.command()
async def clear_server(ctx, server=None):
    """Очистить всех игроков с сервера (только для администраторов)
    Использование: !clear_server [netherop/beast]"""

    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Эта команда доступна только администраторам!")
        return

    if not server or server not in SERVERS:
        await ctx.send(f"❌ Укажите сервер: {', '.join(SERVERS.keys())}")
        return

    await ctx.send(
        f"⚠️ Вы уверены? Это удалит ВСЕХ игроков с сервера {SERVERS[server]['name']}!"
    )
    await ctx.send("Введите `yes` для подтверждения в течение 30 секунд...")

    def check(m):
        return m.author == ctx.author and m.content.lower() == "yes"

    try:
        await bot.wait_for("message", timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("❌ Операция отменена.")
        return

    # Получаем всех игроков с сервера и удаляем
    guild = bot.get_guild(SERVERS[server]["server_id"])
    if guild:
        for member in guild.members:
            send_to_website("remove", member.id, server=server)

    await ctx.send(f"✅ Все игроки с сервера {SERVERS[server]['name']} удалены!")


# Flask приложение для поддержания активности
app = Flask(__name__)


@app.route("/")
def home():
    return "Бот синхронизации двух серверов работает!\nДанные сохраняются в базе данных сайта."


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


# Запускаем веб-сервер для поддержания активности
keep_alive()

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 ЗАПУСК БОТА СИНХРОНИЗАЦИИ")
    print("=" * 50)
    print("📡 Отслеживаемые серверы:")
    for key, config in SERVERS.items():
        print(f"   • {config['name']} (ID: {config['server_id']})")
    print(f"🌐 Сайт: {WEBSITE_URL}")
    print("💾 Данные сохраняются в БД сайта и не теряются при перезапуске!")
    print("=" * 50)
    bot.run(TOKEN)
