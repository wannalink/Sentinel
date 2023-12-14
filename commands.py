from sqlalchemy.orm import sessionmaker
from custom_session import M_scoped_session
from Schema import Alliances, Corporations
from discord import Interaction, Intents
from sqlalchemy import create_engine
from discord.ext import commands
from commandhelpers import *
from dbutility import *
from Mybot import MyBot
import market


description = "An early warning system for Eve online."
intents = Intents.default()
intents.message_content = False

engine = create_engine('sqlite:///database.db', echo=False)
Session_factory = sessionmaker(bind=engine)
Session = M_scoped_session(Session_factory)


bot: commands.Bot = MyBot(command_prefix='/',
                          description=description, intents=intents)
tree = bot.tree


@tree.command(name="allycorp", description="Add a corp to the Santa's good list. Will also add to watch if you haven't done that.")
async def allycorp(interaction: Interaction, corp: str):
    with Session as session:
        valid = await validate_corp_ally_obj(interaction, corp, Corporations, session)
        if not valid:
            return
        await add_ally_objects(interaction, corp, Corporations, session)


@tree.command(name="allyalliance", description="Add an alliance to the Santa's good list. Will also add to watch if you haven't done that.")
async def allyalliance(interaction: Interaction, alliance: str):
    with Session as session:
        valid = await validate_corp_ally_obj(interaction, alliance, Alliances, session)
        if not valid:
            return
        await add_ally_objects(interaction, alliance, Alliances, session)


@tree.command(name="watchalliance", description="Add a filter for an alliance.")
async def watchalliance(interaction: Interaction, alliance: str):
    with Session as session:
        valid = await validate_corp_ally_obj(interaction, alliance, Alliances, session)
        if not valid:
            return
        await add_corp_alliance_objects(interaction, alliance, Alliances, session)


@tree.command(name="watchcorp", description="Add a filter for a corporation.")
async def watchcorp(interaction: Interaction, corp: str):
    with Session as session:
        valid = await validate_corp_ally_obj(interaction, corp, Corporations, session)
        if not valid:
            return
        await add_corp_alliance_objects(interaction, corp, Corporations, session)


@tree.command(name="watch", description="Filter for a system, region, or constellation.")
async def watch(interaction: Interaction, obj: str):
    with Session as session:
        objects = [(Systems, "System"),
                   (Constellations, "Constellation"),
                   (Regions, "Region")]
        for c, n in objects:
            added, already_watched, name, _ = add_object_to_watch(
                interaction, session, obj, c)
            if already_watched:
                await interaction.response.send_message(f"{n}: {name} is already being watched!")
                return
            elif added:
                await interaction.response.send_message(f"{n}: {name} added to watch list!")
                return
    await interaction.response.send_message(f"Unknown celestial object, check your spelling.")


@tree.command(name="ignorealliance", description="Remove an alliance from the filters")
async def ignorealliance(interaction: Interaction, alliance: str):
    with Session as session:
        valid = await validate_corp_ally_obj(interaction, alliance, Alliances, session)
        if not valid:
            return
        removed, not_watched, ally_name = remove_object_from_watch(
            interaction, session, alliance, Alliances)
        if removed:
            await interaction.response.send_message(f"Alliance: {ally_name} removed from watch list!")
            return
        elif not_watched:
            await interaction.response.send_message(f"Alliance: {ally_name} is not being watched!")
            return
    await interaction.response.send_message(f"Unknown Alliance, try removing by ID or check your spelling.")


@tree.command(name="ignorecorp", description="Remove a Corporation from the filters")
async def ignorecorp(interaction: Interaction, corp: str):
    with Session as session:
        valid = await validate_corp_ally_obj(interaction, corp, Corporations, session)
        if not valid:
            return
        removed, not_watched, corp_name = remove_object_from_watch(
            interaction, session, corp, Corporations)
        if removed:
            await interaction.response.send_message(f"Corporation: {corp_name} removed from watch list!")
            return
        elif not_watched:
            await interaction.response.send_message(f"Corporation: {corp_name} is not being watched!")
            return
    await interaction.response.send_message(f"Unknown Corporation, try removing by ID or check your spelling.")


@tree.command(name="ignore", description="Remove the filter for a system, region, or constellation.")
async def ignore(interaction: Interaction, obj: str):
    with Session as session:
        objects = [(Systems, "System"),
                   (Constellations, "Constellation"),
                   (Regions, "Region")]
        for c, n in objects:
            removed, not_watched, name = remove_object_from_watch(
                interaction, session, obj, c)
            if removed:
                await interaction.response.send_message(f"{n}: {name} removed from watch list!")
                return
            if not_watched:
                await interaction.response.send_message(f"{n}: {name} is not being watched!")
                return
    await interaction.response.send_message(f"Unknown cellestial object, check your spelling.")


@tree.command(name="watchall", description="Remove all filters. Recieve all killmails.")
async def watchall(interaction: Interaction):
    with Session as session:
        set_filter_to_all(interaction.guild.id, session)
    await interaction.response.send_message(f"All filters removed! Watching all kills.")


@tree.command(name="watchlist", description="Lists all the entities in the watchlist")
async def watchlist(interaction: Interaction):
    with Session as session:
        await interaction.response.send_message(list_filter(interaction.guild.id, session))


@tree.command(name="setchannel", description="Set the channel for the killstream.")
async def setchannel(interaction: Interaction):
    with Session as session:
        channel = bot.get_channel(interaction.channel_id)
        if not is_server_channel_set(interaction.guild.id, session):
            await interaction.response.send_message(f"Channel set to: {channel.name}. Notifications will now appear in {channel.name}")
        else:
            await interaction.response.send_message(f"Channel moved to: {channel.name}. Notifications will now appear in {channel.name}")
        update_server_channel(interaction, session)


@tree.command(name="neutralcolor", description="Set the color for neutral killmails. Accepts hexademical only!")
async def neutralcolor(interaction: Interaction, color: str):
    with Session as session:
        color = color.replace("#", '')
        try:
            int(color, base=16)
            set_neutral_color_for_guild(interaction, color, session)
            await interaction.response.send_message(f"Neutral color set to: {color}")
        except TypeError:
            await interaction.response.send_message(f"Invalid hexadecimal: {color}")


@tree.command(name="involvedmin", description="Hide killmails below this number of involved attackers. Accepts numbers only!")
async def involvedmin(interaction: Interaction, invmin: str):
    with Session as session:
        if invmin.isdigit():
            set_involvedmin_for_guild(interaction, invmin, session)
            channel = bot.get_channel(interaction.channel_id)
            if int(invmin) > 0:
                await channel.edit(name=f"killfeed-min-{invmin}")
            else:
                await channel.edit(name="killfeed")
            await interaction.response.send_message(f"Threshold set to: {invmin}")
        else:
            await interaction.response.send_message(f"Invalid number: {invmin}")


@bot.event
async def on_guild_join(guild):
    await tree.sync(guild=guild.id)
    with Session as session:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                create_new_guild(channel.id, guild, session)


@tree.command(name="stop", description="Stop the killstream.")
async def stop(interaction: Interaction):
    with Session as session:
        update_server_muted(session, interaction, True)
    await interaction.response.send_message(f"Stopped!")


@tree.command(name="start", description="Start the killstream.")
async def start(interaction: Interaction):
    with Session as session:
        update_server_muted(session, interaction, False)
    await interaction.response.send_message(f"Started!")


@tree.command(name="status", description="Gives the current status.")
async def status(interaction: Interaction):
    with Session as session:
        if is_server_muted(session, interaction.guild_id):
            await interaction.response.send_message(f"Killstream is currently muted. Enable with /start")
        else:
            await interaction.response.send_message(f"Killstream is currently open. Mute with /stop")


@tree.command(name="market", description="Gives the current list of capital ship orders in solar system.")
async def market_info(interaction: Interaction):
    orders, sum = market.orders_status()
    market_response = [f"{sum} orders in total"]
    for type in orders:
        type_name, volume, price, time = type.values()
        market_response.append(f"{volume}: {type_name} [{price} ISK] (Cached: {time} ago)")    
    market_response_str = '\n'.join(map(str, market_response))
    await interaction.response.send_message("```" + market_response_str + "```")


@bot.event
async def on_ready():
    from app import logger
    from config import service_status
    from datetime import datetime
    print(f"Logged in as {bot.user} (IUD: {bot.user.id})")
    logger.info("Discord logged in")
    service_status['discord']['started'] = datetime.now()
    await tree.sync()
