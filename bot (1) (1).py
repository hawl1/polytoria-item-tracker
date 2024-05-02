import asyncio
import httpx
import discord
from discord.enums import Status

# sorry for the bad way of coding, blame bot-hosting.net

previous_data = {}
# channel_ids, put channel ids here, like int("93439372983")
channel_ids = []

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

# List of custom messages
custom_messages = [
    "hawli stop restarting servers",
    "10+9=21",
    "𝓯𝓻𝓮𝓪𝓴𝔂 atm",
   "Spacebuilder+Ohio=Ohiobuilder",
    "Ye",
    "Skibidimo",
    "Bot will never be open source",
    "Hawki",
    "bloxius key",
    "hawlis ban logs are darker than my future"
]

async def change_custom_presence():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for message in custom_messages:
            await bot.change_presence(activity=discord.CustomActivity(message))
            await asyncio.sleep(690) # funny number

async def get_data(page=1):
    """
    Get data from the Polytoria API.

    Args:
        page (int): The page number to fetch.

    Returns:
        dict: JSON response from the API.
    """
    base_url = "https://polytoria.com/api/store/items"
    params = {
        "types[]": ["hat", "tool", "face"],
        "page": page,
        "search": "",
        "sort": "createdAt",
        "order": "desc",
        "showOffsale": "false",
        "collectiblesOnly": "true",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(base_url, params=params, timeout=20)  # Polytoria API has some skill issues lmao
            response.raise_for_status()
            return response.json()
            print("Fetched data succesfully")
        except httpx.ReadTimeout as e:
            print(f"Timeout occurred while fetching data: {e}")
            return None
        except Exception as e:
            print(f"Error occurred while fetching data: {e}")
            return None


async def send_item_embed(item, is_sold_out):
    """
    Send an embed message with item information to multiple channels.

    Args:
        item (dict): Item information.
        is_new (bool): Whether the item is new or a price change.
    """
    try:
        item_url = f"https://polytoria.com/store/{item['id']}"
        embed_title = item['name']
        previous_price = previous_data.get(item["id"], {}).get("price")

        embed = discord.Embed(title=embed_title, url=item_url)
        embed.set_thumbnail(url=item["thumbnailUrl"])

        if is_sold_out:
            embed_color = discord.Color.purple()
            embed.add_field(name="Price", value=f"<:ptbrick:1155217703590703204> {item['price']}", inline=True)
            price_status = "Item Sold Out!"
            embed.color = embed_color
            for channel_id in channel_ids:
                channel = bot.get_channel(channel_id)
                await channel.send(content=f"**{price_status}**", embed=embed)
        else:
            embed_color = discord.Color.orange()

            if previous_price is not None:
                embed.add_field(name="Old Price",
                                value=f" <:ptbrick:1155217703590703204> {previous_price}",
                                inline=True)
                embed.add_field(name="New Price",
                                value=f" <:ptbrick:1155217703590703204> {item['price']}",
                                inline=True)

                if item['price'] < previous_price:
                    price_status = "Price dropped!"
                    embed_color = discord.Color.red()
                elif item['price'] > previous_price:
                    price_status = "Price increased!"
                    embed_color = discord.Color.green()
                else:
                    price_status = "Price remains the same"
                    embed_color = discord.Color.gold()
            else:
                embed.add_field(name=price_status, value=f"<:ptbrick:1155217703590703204> {item['price']}", inline=True)

        embed.color = embed_color

        for channel_id in channel_ids:
            channel = bot.get_channel(channel_id)
            await channel.send(content=f"**{price_status}**", embed=embed)
    except Exception as e:
        print(f"Error occurred while sending embed: {e}")

@bot.event
async def on_ready():
    """
    Event handler for bot being ready.
    """
    global previous_data
    global page
    page = 1

    print(f"{bot.user.name} has connected to Discord!")
    bot.loop.create_task(change_custom_presence())

    while True:
        while True:
            data = await get_data(page)
            if data is None:
                await asyncio.sleep(10)  # Retry after waiting for a while
                continue

            try:
                for item in data.get("data", []):
                    item_id = item.get("id")
                    current_price = item.get("price")
                    is_limited = item.get("isLimited")
                    is_sold_out = item.get("isSoldOut")

                    if item_id is None or current_price is None or is_limited is None or is_sold_out is None:
                        continue  # Skip incomplete data

                    if item_id in previous_data:
                        previous_price = previous_data[item_id].get("price")
                        was_limited = previous_data[item_id].get("isLimited")
                        was_sold_out = previous_data[item_id].get("isSoldOut")

                        if current_price != previous_price:
                            await send_item_embed(item, False)  # Price changed
                        if not was_limited and is_limited:
                            await send_item_embed(item, True)  # New limited item
                        if not was_sold_out and is_sold_out:
                            await send_item_embed(item, True)  # Item sold out

                    previous_data[item_id] = {
                        "price": current_price,
                        "isLimited": is_limited,
                        "isSoldOut": is_sold_out
                    }
                    if not item_id in previous_data and is_sold_out:
                        await send_item_embed(item, True)  # Newly sold out item
            except Exception as e:
                print(f"Error occurred while processing data: {e}")

            if data.get("meta", {}).get("currentPage", 0) < data.get("meta", {}).get("lastPage", 0):
                page += 1
            else:
                page = 1
                break

        await asyncio.sleep(15)

# Keep the bot running

bot.run("BOT_TOKEN_HERE")
