import nextcord
from nextcord.ext import commands, tasks
import random
import datetime
import json
import logging
import logging.handlers
import platform
import psutil
import inspect
import textwrap
import traceback
from contextlib import redirect_stdout
import io
import math
import cpuinfo # pip3 install py-cpuinfo
# ! Importok, ne nagyon érjetek hozzá

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

# * A bot létrehozása, a prefix a bot megemlítése vagy "szia!!"
client = commands.Bot(command_prefix=commands.when_mentioned_or('szia!!'), intents=nextcord.Intents.all())
client.remove_command("help") # * Alap help parancs törlése

logger = logging.getLogger('nextcord')
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler("discord.log", mode='a', maxBytes=10000000, backupCount=1, encoding='utf-8', delay=0)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
# * Logging, ha nem akarod, szedd ki

@client.event
async def on_command_error(ctx, error):
    command = client.get_command(str(ctx.message.content).replace("szia!!", ""))
    if isinstance(error, commands.MissingRequiredArgument): # ! Error: Nem írtak be egy kötelező argumentumot
        await ctx.send(f"Használat: {command.usage}")
    elif isinstance(error, commands.BadArgument): # ! Error: Rossz egy argumentum
        await ctx.send(f"Használat: {command.usage}")
    elif isinstance(error, AttributeError): # ! Error: Rossz kód
        await ctx.reply(f"Belső hiba! ```{error}```", mention_author=False)
    elif isinstance(error, commands.MissingPermissions): # ! Error: Hiányzó jog
        await ctx.message.delete() # ! Üzenet törlése
    elif isinstance(error, commands.MissingRole): # ! Error: Hiányzó rang
        await ctx.message.delete() # ! Üzenet törlése
    else: # * Különben (tehát ha ezek közül egyik sem)
        raise error # ! Írja ki konzolra

@client.event
async def on_ready(): # * Amikor a bot elindul
    print(f"A bot csatlakozott a Discord API-hoz. Kezdési ping: {round(client.latency * 1000)}ms ({client.latency} másodperc), szerverek száma: {len(client.guilds)}")
    await client.change_presence(activity=nextcord.Game(name="szia!config - {} szerver".format(len(client.guilds)))) # ? Aktivitás megváltoztatása - Írd át a te prefixedre

@client.event
async def on_guild_join(guild): # * Amikor a bot becsatlakozik egy szerverre
    with open("szavak.json", encoding="UTF-8") as r:
        beallitasok = json.load(r) # ? Beállítások dict létrehozása a szavak.json értékével
    beallitasok[str(guild.id)] = {}
    beallitasok[str(guild.id)]["id"]=guild.id
    beallitasok[str(guild.id)]["allapot"]="on"
    beallitasok[str(guild.id)]["szavak"]=["hello", "helló", "szia", "szius", "csá", "csa", "cso", "cső", "szioka", "szióka"]
    beallitasok[str(guild.id)]["uzenet"]=["Szia Uram!", "Hellóka!", "Hellcső!"]
                                        # ! Alap beállítások létrehozása
    with open("szavak.json", "w") as w:
        json.dump(beallitasok, w) # * JSON fájl frissítése
    await client.change_presence(activity=nextcord.Game(name="szia!config - {} szerver".format(len(client.guilds)))) # ? Aktivitás frissítése

@client.event
async def on_message(ctx): # * Amikor üzenetet írnak
    await client.process_commands(ctx) # * Parancs végrehajtása (ha parancsot írtak be)
    with open("szavak.json", encoding="UTF-8") as r:
        beallitasok = json.load(r)[str(ctx.guild.id)] # ! beallitasok dict létrehozása, most lekérésre csak
    if ctx.author.bot == False and ctx.content.lower() in beallitasok["szavak"] and beallitasok["allapot"] == "on":
        await ctx.reply(random.choice(beallitasok["uzenet"]), mention_author=False) # ! Random válasz visszaadása
    else:
        return

@client.command()
async def ping(ctx):
    await ctx.reply(f"Pong! :ping_pong: `{round(client.latency * 1000)}`ms", mention_author=False)

@client.command()
async def config(ctx):
    if not ctx.author.guild_permissions.administrator:
        embed=nextcord.Embed(title="Hiányzó Jogok", description="Nincs elég jogod a parancs használatához!\n*Ehhez kell: `Adminisztrátor`*", timestamp=datetime.datetime.utcnow(), color=nextcord.Color.red())
        embed.set_author(name=f"{ctx.author.name} | Hiba", icon_url=ctx.author.display_avatar)
        embed.set_footer(text=f"Szia Uram! | Hiba", icon_url=client.user.display_avatar)
        return await ctx.reply(embed=embed, mention_author=False)
    with open("szavak.json", encoding="UTF-8") as r:
        beallitasok = json.load(r)[str(ctx.guild.id)]
    embed = nextcord.Embed(title="Opciók", description="Lista a paraméterekről:", color=nextcord.Colour.red(), timestamp=datetime.datetime.utcnow())
    embed.add_field(name="Rendszer (szia!config_rendszer be/ki)", value=f"```{'be' if beallitasok['allapot'] == 'on' else 'ki'}```")
    koszonesek = ""
    visszakoszonesek = ""
    for i in beallitasok["szavak"]:
        koszonesek = koszonesek + "`" + i + "`" + ", "
    for l in beallitasok["uzenet"]:
        visszakoszonesek = visszakoszonesek + "`" + l + "`" + ", "
    embed.add_field(name="Köszönések (szia!config_koszonesek add/remove [szöveg])" if len(beallitasok["szavak"]) > 1 else "Köszönés", value=koszonesek[:-2])
    embed.add_field(name="Visszaköszönések (szia!config_visszakoszonesek add/remove [szöveg])" if len(beallitasok["uzenet"]) > 1 else "Visszaköszönés", value=visszakoszonesek[:-2])
    embed.set_author(name=f"{ctx.author.name} | Config", icon_url=ctx.author.display_avatar)
    embed.set_footer(text=f"Szia Uram! | Config", icon_url=client.user.display_avatar)
    await ctx.reply(embed=embed, mention_author=False)

@client.command()
async def config_rendszer(ctx, option):
    if not ctx.author.guild_permissions.administrator:
        embed=nextcord.Embed(title="Hiányzó Jogok", description="Nincs elég jogod a parancs használatához!\n*Ehhez kell: `Adminisztrátor`*", timestamp=datetime.datetime.utcnow(), color=nextcord.Color.red())
        embed.set_author(name=f"{ctx.author.name} | Hiba", icon_url=ctx.author.display_avatar)
        embed.set_footer(text=f"Szia Uram! | Hiba", icon_url=client.user.display_avatar)
        return await ctx.reply(embed=embed, mention_author=False)
    with open("szavak.json", encoding="UTF-8") as r:
        beallitasok = json.load(r)
    if option == "be":
        if beallitasok[str(ctx.guild.id)]["allapot"] == "on":
            return await ctx.reply("Az üdvözlő rendszer már be van kapcsolva!", mention_author=False)
        beallitasok[str(ctx.guild.id)]["allapot"] = "on"
        await ctx.reply("Az üdvözlő rendszer bekapcsolva!", mention_author=False)
    elif option == "ki":
        if beallitasok[str(ctx.guild.id)]["allapot"] == "off":
            return await ctx.reply("Az üdvözlő rendszer már ki van kapcsolva!", mention_author=False)
        beallitasok[str(ctx.guild.id)]["allapot"] = "off"
        await ctx.reply("Az üdvözlő rendszer kikapcsolva!", mention_author=False)
    else:
        await ctx.reply("Nincs ilyen opció!", mention_author=False)
    with open("szavak.json", 'w', encoding="UTF-8") as w:
        json.dump(beallitasok, w)

@client.command()
async def config_koszonesek(ctx, addremove, *, szoveg):
    if not ctx.author.guild_permissions.administrator:
        embed=nextcord.Embed(title="Hiányzó Jogok", description="Nincs elég jogod a parancs használatához!\n*Ehhez kell: `Adminisztrátor`*", timestamp=datetime.datetime.utcnow(), color=nextcord.Color.red())
        embed.set_author(name=f"{ctx.author.name} | Hiba", icon_url=ctx.author.display_avatar)
        embed.set_footer(text=f"Szia Uram! | Hiba", icon_url=client.user.display_avatar)
        return await ctx.reply(embed=embed, mention_author=False)
    with open("szavak.json", encoding="UTF-8") as r:
        beallitasok = json.load(r)
    if ('"' or "'" or "`") in szoveg:
        return await ctx.reply("Nem engedélyezett karakter van a szövegedben. Tilos használni: " + '"' + ", ', `.")
    if addremove == "add":
        if szoveg not in beallitasok[str(ctx.guild.id)]["szavak"]:
            beallitasok[str(ctx.guild.id)]["szavak"].append(szoveg)
            await ctx.reply(f"`{szoveg}` hozzáadva a köszönésekhez!", mention_author=False)
        else:
            await ctx.reply(f"Ez már bent van a köszönésekben!", mention_author=False)
            return
    elif addremove == "remove":
        if szoveg in beallitasok[str(ctx.guild.id)]["szavak"]:
            beallitasok[str(ctx.guild.id)]["szavak"].remove(szoveg)
            await ctx.reply(f"`{szoveg}` eltávolítva a köszönésekből!", mention_author=False)
        else:
            await ctx.reply(f"Ez nincs bent a köszönésekben!", mention_author=False)
            return
    with open("szavak.json", 'w', encoding="UTF-8") as w:
        json.dump(beallitasok, w)

@client.command()
async def config_visszakoszonesek(ctx, addremove, *, szoveg):
    if not ctx.author.guild_permissions.administrator:
        embed=nextcord.Embed(title="Hiányzó Jogok", description="Nincs elég jogod a parancs használatához!\n*Ehhez kell: `Adminisztrátor`*", timestamp=datetime.datetime.utcnow(), color=nextcord.Color.red())
        embed.set_author(name=f"{ctx.author.name} | Hiba", icon_url=ctx.author.display_avatar)
        embed.set_footer(text=f"Szia Uram! | Hiba", icon_url=client.user.display_avatar)
        return await ctx.reply(embed=embed, mention_author=False)
    with open("szavak.json", encoding="UTF-8") as r:
        beallitasok = json.load(r)
    if ('"' or "'" or "`") in szoveg:
        return await ctx.reply("Nem engedélyezett karakter van a szövegedben. Tilos használni: " + '"' + ", ', `.")
    if addremove == "add":
        if szoveg not in beallitasok[str(ctx.guild.id)]["uzenet"]:
            beallitasok[str(ctx.guild.id)]["uzenet"].append(szoveg)
            await ctx.reply(f"`{szoveg}` hozzáadva a köszönésekhez!", mention_author=False)
        else:
            await ctx.reply(f"Ez már bent van a köszönésekben!", mention_author=False)
            return
    elif addremove == "remove":
        if szoveg in beallitasok[str(ctx.guild.id)]["uzenet"]:
            beallitasok[str(ctx.guild.id)]["uzenet"].remove(szoveg)
            await ctx.reply(f"`{szoveg}` eltávolítva a köszönésekből!", mention_author=False)
        else:
            await ctx.reply(f"Ez nincs bent a köszönésekben!", mention_author=False)
            return
    with open("szavak.json", 'w', encoding="UTF-8") as w:
        json.dump(beallitasok, w)

@client.command()
async def info(ctx):
    embed = nextcord.Embed(title="Bot Információk", timestamp=datetime.datetime.utcnow(), color=nextcord.Color.red())
    embed.add_field(name="A bot készítője", value="`Pearoo#4179`", inline=False)
    embed.add_field(name="Segítők", value="Fejlesztés: `FightMan01#1680`, `Dempy#0053`, cablesalty\nVPS: `✠ϟ Elydra ϟ✠#0001`\nÖtlet: `Tsukuyomi (月読命)#1377`\nNem segített semmit, csak benne akart lenni a listában: `ShadowCracker#0097`", inline=False)
    embed.add_field(name="Parancsok száma", value=len(client.commands))
    embed.add_field(name="Szerverek száma", value=len(client.guilds))
    embed.add_field(name="Csatornák száma", value=len(set(client.get_all_channels())))
    embed.add_field(name="Felhasználók száma", value=len(set(client.get_all_members())))
    embed.add_field(name="Python verzió", value=platform.python_version())
    embed.add_field(name="nextcord verzió", value=nextcord.__version__)
    embed.add_field(name="Programozási könyvtárak", value="`nextcord`, `json`, `random`, `datetime`, `platform`, `psutil`, `contextlib`, `traceback`, `inspect`, `textwrap`, `io`")
    if platform.system() == "Darwin": # Ha a rendszer macOS, nem kell a platform.version()
        embed.add_field(name="Operációs rendszer", value=f"{platform.system()} {platform.release()}")
    else:
        embed.add_field(name="Operációs rendszer", value=f"{platform.system()} {platform.release()} {platform.version()}")
    embed.add_field(name="CPU (processzor)", value=f"{cpuinfo.get_cpu_info()['brand_raw']} ({cpuinfo.get_cpu.info()['count']} mag)")
    embed.add_field(name="CPU kihasználtság", value=f"{psutil.cpu_percent()}%")
    embed.add_field(name="Memória mérete", value=f"{convert_size(psutil.virtual_memory().total)} ({psutil.virtual_memory().used} felhasználva)")
    embed.add_field(name="Memória kihasználtság", value=f"{psutil.virtual_memory().percent}%")
    await ctx.reply(embed=embed, mention_author=False)

client.run("token") # !! ILLESZD BE A SAJÁT TOKENED!