    
import os
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- AYARLAR ---
UYARI_LIMITI = 5
TIMEOUT_SURESI = 10  # dakika
SPAM_LIMIT = 4  # 5 saniyede 4 mesaj = spam
SPAM_SURE = 5  # saniye

# Küfürler txt dosyasından okunuyor
try:
    with open("kufurler.txt", "r", encoding="utf-8") as f:
        KUFURLER = [satir.strip().lower() for satir in f if satir.strip()]
except:
    KUFURLER = []
    print("kufurler.txt bulunamadi, bos liste ile basliyor")

uyarilar = {}
spam_takip = defaultdict(list)

def bugun():
    return datetime.now().strftime("%Y-%m-%d")

async def uyari_ver(member, sebep, message):
    user_id = member.id
    tarih = bugun()

    if user_id not in uyarilar or uyarilar[user_id]["tarih"] != tarih:
        uyarilar[user_id] = {"tarih": tarih, "sayi": 0}
    
    uyarilar[user_id]["sayi"] += 1
    sayi = uyarilar[user_id]["sayi"]

    try:
        await message.channel.send(f"⚠️ {member.mention} **{sebep}** sebebiyle uyarıldı! ({sayi}/{UYARI_LIMITI})", delete_after=5)
    except:
        pass

    if sayi >= UYARI_LIMITI:
        try:
            await member.timeout(timedelta(minutes=TIMEOUT_SURESI), reason="Günlük uyarı limiti doldu")
            await message.channel.send(f"🔇 {member.mention} bugün {UYARI_LIMITI} uyarıya ulaştığı için **{TIMEOUT_SURESI} dakika** zaman aşımına uğradı!")
            uyarilar[user_id]["sayi"] = 0
        except Exception as e:
            print(f"Timeout hatası: {e}")

def kufur_var_mi(text):
    text = text.lower()
    for kufur in KUFURLER:
        if kufur and kufur in text:
            return True
    return False

def caps_mi(text):
    harfler = [c for c in text if c.isalpha()]
    if len(harfler) < 10:
        return False
    buyuk = sum(1 for c in harfler if c.isupper())
    return (buyuk / len(harfler)) > 0.7

@bot.event
async def on_ready():
    print(f"{bot.user} aktif kanka!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if not message.guild:
        return
    if message.author.guild_permissions.administrator:
        await bot.process_commands(message)
        return

    icerik = message.content
    kucuk = icerik.lower()

    # 1. KÜFÜR
    if kufur_var_mi(kucuk):
        await message.delete()
        await uyari_ver(message.author, "Küfür", message)
        return

    # 2. CAPS LOCK
    if caps_mi(icerik):
        await message.delete()
        await uyari_ver(message.author, "Caps Lock", message)
        return

    # 3. SPAM
    simdi = datetime.now()
    spam_takip[message.author.id].append(simdi)
    spam_takip[message.author.id] = [t for t in spam_takip[message.author.id] if (simdi - t).total_seconds() < SPAM_SURE]
    
    if len(spam_takip[message.author.id]) >= SPAM_LIMIT:
        await message.delete()
        spam_takip[message.author.id].clear()
        await uyari_ver(message.author, "Spam", message)
        return

    await bot.process_commands(message)

@bot.command()
async def uyarilarim(ctx):
    user_id = ctx.author.id
    sayi = 0
    if user_id in uyarilar and uyarilar[user_id]["tarih"] == bugun():
        sayi = uyarilar[user_id]["sayi"]
    await ctx.send(f"{ctx.author.mention} Bugünkü uyarı sayın: **{sayi}/{UYARI_LIMITI}**")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def uyari_sifirla(ctx, member: discord.Member):
    if member.id in uyarilar:
        uyarilar[member.id]["sayi"] = 0
    await ctx.send(f"{member.mention} uyarıları sıfırlandı.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def temizle(ctx, adet: int = 10):
    await ctx.channel.purge(limit=adet+1)
    await ctx.send(f"{adet} mesaj silindi.", delete_after=3)

bot.run(TOKEN)