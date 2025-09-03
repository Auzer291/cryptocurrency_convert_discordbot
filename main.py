import json
import requests
import time
import os
from forex_python.converter import CurrencyRates
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
import datetime
from datetime import datetime

load_dotenv()
EX_API = os.getenv('EX_API')
BASE_EX_URL = "https://v6.exchangerate-api.com/v6/{}/latest/".format(EX_API)
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

def get_usdt_price(cryptocurrency):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={cryptocurrency}USDT"
    response = requests.get(url)
    data = response.json()
    #return float(data['price'])
    try:
        response.raise_for_status()
        return float(data['price'])  # Raise an error for bad responses
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        return None
    
#print(get_usdt_price("BTC"))
#curr = get_usdt_price("BTC")

def get_exchange_rate(base_currency="USD", target_currency="VND"):
    response = requests.get(BASE_EX_URL + base_currency)
    if response.status_code == 200:
        data = response.json()
        return data["conversion_rates"].get(target_currency, None)
    else:
        return None
#print(get_exchange_rate())

def usd_to_vnd(usd_amount):
    rate = get_exchange_rate()
    if rate:
        return usd_amount * rate
    else:
        return None
    
#print("USD TO VND: {}".format(usd_to_vnd(curr)))

intents = discord.Intents.all()
#intents.message_content = True
bot = commands.Bot(command_prefix=["!","b!"], intents=intents)
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Lỗi thiếu thông số: `{error.param}`.")
    else:
        # Handle other types of errors or log them
        print(f"Unhandled error: {error}")
        await ctx.send("An error occurred. Please try again later.")

@bot.tree.command(name="ping", description="Kiểm tra độ trễ của bot khi gửi lệnh")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Độ trễ: {:.1f} ms :signal_strength:".format(bot.latency * 1000), ephemeral=True)


@bot.tree.command(name="usd_to_vnd", description="Chuyển đổi USD sang VND")
async def usd_to_vnd_command(interaction: discord.Interaction, amount: float):
    vnd_amount = usd_to_vnd(amount)
    if vnd_amount is not None:
        await interaction.response.send_message(f"{amount} USD sẽ bằng khoảng {vnd_amount:,.2f} VND.", ephemeral=True)
    else:
        await interaction.response.send_message("Đã xảy ra lỗi. Xin vui lòng thử lại!", ephemeral=True)


@bot.tree.command(name="vnd_to_usd", description="Chuyển đổi VND sang USD")
async def vnd_to_usd_command(interaction: discord.Interaction, amount: float):
    rate = get_exchange_rate()
    if rate:
        usd_amount = amount / rate
        await interaction.response.send_message(f"{amount:,.2f} VND sẽ bằng khoảng {usd_amount:.2f} USD.", ephemeral=True)
    else:
        await interaction.response.send_message("Đã xảy ra lỗi. Xin vui lòng thử lại!", ephemeral=True)

@bot.tree.command(name="crypto_to_vnd", description="Chuyển đổi từ một loại crypto sang VND")
#@bot.app_commands.describe(cryptocurrency="Supported Cryptocurrency: LTC(litecoin), BTC(bitcoin), SOL(Solana), ETH(ethereum)", amount="Amount of cryptocurrency to convert")
async def crypto_to_vnd_command(interaction: discord.Interaction, cryptocurrency: str, amount: float):
    cryptocurrency = cryptocurrency.upper()
    crypto_price_usdt = get_usdt_price(cryptocurrency.upper())
    if crypto_price_usdt is not None:
        vnd_amount = usd_to_vnd(crypto_price_usdt * amount)
        if vnd_amount is not None:
            await interaction.response.send_message(f"{amount} {cryptocurrency.upper()} sẽ bằng khoảng {vnd_amount:,.2f} VND.", ephemeral=True)
        else:
            await interaction.response.send_message("Đã xảy ra lỗi. Xin vui lòng thử lại!", ephemeral=True)
    else:
        await interaction.response.send_message(f"Could not fetch the price for {cryptocurrency.upper()}. Please ensure the cryptocurrency symbol is correct.", ephemeral=True)

@bot.tree.command(name="vnd_to_crypto", description="Chuyển đổi từ tiền VND sang một loại crypto")
#@bot.app_commands.describe(cryptocurrency="Supported Cryptocurrency: LTC(litecoin), BTC(bitcoin), SOL(Solana), ETH(ethereum)", amount="Amount of VND to convert")
async def vnd_to_crypto_command(interaction: discord.Interaction, cryptocurrency: str, amount:float):
    cryptocurrency = cryptocurrency.upper()
    crypto_price_usdt = get_usdt_price(cryptocurrency)
    if crypto_price_usdt is not None:
        rate = get_exchange_rate()
        if rate:
            usd_amount = amount / rate
            crypto_amount = usd_amount / crypto_price_usdt
            await interaction.response.send_message(f"{amount:,.2f} VND sẽ bằng khoảng {crypto_amount:.6f} {cryptocurrency}.", ephemeral=True)
        else:
            await interaction.response.send_message("Đã xảy ra lỗi. Xin vui lòng thử lại!", ephemeral=True)
    else:
        await interaction.response.send_message(f"Could not fetch the price for {cryptocurrency}. Please ensure the cryptocurrency symbol is correct.", ephemeral=True)

@bot.tree.command(name="crypto_to_usd", description="Chuyển đổi từ một loại crypto sang USD")
async def crypto_to_usd_command(interaction: discord.Interaction, cryptocurrency: str, amount: float):
    cryptocurrency = cryptocurrency.upper()
    crypto_price_usdt = get_usdt_price(cryptocurrency)
    if crypto_price_usdt is not None:
        usd_amount = crypto_price_usdt * amount
        await interaction.response.send_message(f"{amount} {cryptocurrency} sẽ bằng khoảng {usd_amount:.2f} USD.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Could not fetch the price for {cryptocurrency}. Please ensure the cryptocurrency symbol is correct.", ephemeral=True)

@bot.tree.command(name="usd_to_crypto", description="Chuyển đổi từ tiền USD sang một loại crypto")
async def usd_to_crypto_command(interaction: discord.Interaction, cryptocurrency: str, amount: float):
    cryptocurrency = cryptocurrency.upper()
    crypto_price_usdt = get_usdt_price(cryptocurrency)
    if crypto_price_usdt is not None:
        crypto_amount = amount / crypto_price_usdt
        await interaction.response.send_message(f"{amount} USD sẽ bằng khoảng {crypto_amount:.6f} {cryptocurrency}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Could not fetch the price for {cryptocurrency}. Please ensure the cryptocurrency symbol is correct.", ephemeral=True)

@bot.tree.command(name="help", description="Cho xem danh sách các lệnh của bot và cách sử dụng chúng")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="Danh Sách Lệnh của Bot (prefix:\"!\", \"/\", \"b!\")",
                      description="Dưới đây là danh sách các lệnh và hướng dẫn sử dụng các lệnh của bot",
                      colour=0xff94f6,
                      timestamp=datetime.now())
    embed.set_author(name="Đổi Tiền Crypto Bot - Được làm bởi @uzar369_00895",
    icon_url="https://cdn.discordapp.com/attachments/1404846108097646747/1411742047450169514/yis.png?ex=68b90e7d&is=68b7bcfd&hm=b081de958bd77ace51401064756e0ddc17262b7c39079729dba0a18894d53960&")

    embed.add_field(name="***ping*** : Kiểm tra độ trễ của bot khi gửi lệnh",
                    value="- Sử dụng lệnh /ping để dùng lệnh này",
                    inline=False)
    embed.add_field(name="***usd_to_vnd*** : Chuyển đổi USD sang VND",
                    value="- Sử dụng   /usd_to_vnd [số tiền USD] để sử dụng lệnh này",
                    inline=False)
    embed.add_field(name="***vnd_to_usd*** : Chuyển đổi VND sang USD",
                    value="- Sử dụng   /vnd_to_usd [số tiền VND] để sử dụng lệnh này",
                    inline=False)
    embed.add_field(name="***crypto_to_vnd*** : Chuyển đổi từ một loại crypto sang VND",
                    value="- Sử dụng   /crypto_to_vnd [Loại crypto(LTC, BTC, SOL, ETH)] [số lượng đồng crypto] để sử dụng lệnh này",
                    inline=False)
    embed.add_field(name="***crypto_to_usd*** : Chuyển đổi từ một loại crypto sang USD",
                    value="- Sử dụng   /crypto_to_usd [Loại crypto(LTC, BTC, SOL, ETH)] [số lượng đồng crypto] để sử dụng lệnh này",
                    inline=False)
    embed.add_field(name="***vnd_to_crypto*** : Chuyển đổi từ tiền VND sang một loại crypto",
                    value="- Sử dụng   /vnd_to_crypto [Loại crypto(LTC, BTC, SOL, ETH)] [số tiền VND] để sử dụng lệnh này",
                    inline=False)
    embed.add_field(name="***usd_to_crypto*** : Chuyển đổi từ tiền USD sang một loại crypto",
                    value="- Sử dụng   /usd_to_crypto [Loại crypto(LTC, BTC, SOL, ETH)] [số tiền USD] để sử dụng lệnh này",
                    inline=False)

    embed.set_footer(text="tạo bởi @uzar369_00895")
    await interaction.response.send_message(embed=embed, ephemeral=True)
bot.remove_command('help')
bot.run(DISCORD_BOT_TOKEN)