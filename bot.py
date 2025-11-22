import discord
from discord.ext import commands
from bot_logic import gen_pass
import random
import os
import requests
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

# ------------------------------
#     COMMAND PERUBAHAN IKLIM
# ------------------------------
@bot.command()
async def cuaca(ctx, *, kota: str):
    try:
        # ============================
        # 1. GEOCODING → Ambil Koordinat
        # ============================
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {
            "name": kota,
            "count": 1,
            "language": "id",
            "format": "json"
        }

        geo_res = requests.get(geo_url, params=geo_params).json()

        if "results" not in geo_res:
            await ctx.send(f"❌ Kota **{kota}** tidak ditemukan.")
            return

        nama_kota = geo_res["results"][0]["name"]
        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]

        # ============================
        # 2. CUACA
        # ============================
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "rain", "weather_code"],
            "timezone": "Asia/Jakarta"
        }

        response = openmeteo.weather_api(
            "https://api.open-meteo.com/v1/forecast",
            params=params
        )[0]

        current = response.Current()
        suhu = round(current.Variables(0).Value())
        hujan = current.Variables(1).Value()
        kode = int(current.Variables(2).Value())

        # ============================
        # 3. JENIS HUJAN OTOMATIS
        # ============================
        if hujan == 0:
            status_hujan = "Tidak ada hujan"
        elif hujan < 1:
            status_hujan = "Gerimis"
        elif hujan < 5:
            status_hujan = "Hujan ringan"
        elif hujan < 20:
            status_hujan = "Hujan sedang"
        else:
            status_hujan = "Hujan lebat"

        # ============================
        # 4. EMOJI KODE CUACA
        # ============================
        weather_emoji = {
            0: "☀️ Cerah",
            1: "🌤 Sedikit Berawan",
            2: "⛅ Berawan",
            3: "☁️ Mendung",
            45: "🌫 Berkabut",
            61: "🌧 Hujan Ringan",
            63: "🌧 Hujan Sedang",
            65: "🌧 Hujan Lebat",
            95: "⛈ Badai Petir",
        }

        kondisi = weather_emoji.get(kode, "🌫 Tidak diketahui")

        # ============================
        # 5. EMBED
        # ============================
        embed = discord.Embed(
            title=f"Cuaca {nama_kota}",
            description="Informasi cuaca saat ini:",
            color=0x2ecc71
        )

        embed.add_field(name="🌡 Suhu", value=f"{suhu}°C", inline=True)
        embed.add_field(name="🌧 Hujan", value=f"{hujan} mm ({status_hujan})", inline=True)
        embed.add_field(name="☁ Kondisi", value=kondisi, inline=False)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send("❌ Gagal mengambil data cuaca.")
        print(e)




# ------------------------------
#       EVENT on_ready
# ------------------------------
@bot.event
async def on_ready():
    print(f'Bot aktif sebagai {bot.user}')
    print(f'ID: {bot.user.id}')
    print('------')


# ------------------------------
#       COMMAND LAIN
# ------------------------------
@bot.command()
async def hello(ctx):
    await ctx.send(f'Hai! Saya adalah bot {bot.user}!')

@bot.command()
async def Selamatpagi(ctx):
    await ctx.send("selamat pagi juga ,love love.")

@bot.command()
async def pasw(ctx):
    await ctx.send(gen_pass(10))

@bot.command()
async def selamatmalam(ctx):
    await ctx.send("selamat malam juga,love love.")

@bot.command()
async def guess(ctx):
    await ctx.send('Guess a number between 1 and 10.')

    def is_correct(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

    answer = random.randint(1, 10)

    try:
        guess = await bot.wait_for('message', check=is_correct, timeout=5.0)
    except TimeoutError:
        return await ctx.send(f'Sorry, you took too long. The answer was {answer}.')

    if int(guess.content) == answer:
        await ctx.send('You are right!')
    else:
        await ctx.send(f'Oops. It is actually {answer}.')

@bot.command()
async def meme(ctx):
    img_name = random.choice(os.listdir('images'))
    with open(f'images/{img_name}', 'rb') as f:
        picture = discord.File(f)
    await ctx.send(file=picture)

def get_duck_image_url():    
    url = 'https://random-d.uk/api/random'
    res = requests.get(url)
    data = res.json()
    return data['url']

@bot.command('duck')
async def duck(ctx):
    image_url = get_duck_image_url()
    await ctx.send(image_url)

@bot.command('solusi')
async def solusi(ctx):
    with open('solusi.txt', 'r', encoding='utf-8') as f:
        await ctx.send(f.read())

