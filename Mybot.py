import asyncio
from os import environ
from CWebSocket import message_queue, does_msg_match_guild_watchlist
import discord
from discord.ext import commands, tasks
from dbutility import *
import datetime
import market

class MyBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blocker = False
        self.blocker_market = False

    @tasks.loop(seconds=1)
    async def background_task(self):
        if self.blocker or len(message_queue) == 0:
            return

        self.blocker = True

        from commands import Session
        with Session as session:
            # Cache the ready status of the guild to prevent redunant queries
            @lru_cache(maxsize=100)
            def check_guild_status(guild_id: int):
                return is_server_channel_set(guild_id, session) and not is_server_muted(session, guild_id)

            # Cache the channel id to prevent redundant queries
            @lru_cache(maxsize=100)
            def get_channel_id(guild_id: int):
                return get_channel_id_from_guild_id(session, guild_id)

            @lru_cache(maxsize=100)
            def get_filter_from_guild_id(guild_id: int):
                filter = does_server_have_filter(guild_id, session)
                if filter == None:
                    filter = WatchLists(server_id=guild_id)
                    session.add(filter)
                    session.commit()
                return filter

            try:
                while (len(message_queue) != 0):
                    message = message_queue.pop(0)
                    for guild in self.guilds:
                        if check_guild_status(guild.id):
                            matched, embed = does_msg_match_guild_watchlist(
                                message, get_filter_from_guild_id(guild.id), session)
                            if not matched or embed == None:
                                continue
                            channelid = get_channel_id(guild.id)
                            if channelid == None:
                                continue
                            channel = self.get_channel(channelid)
                            await channel.send(embed=embed)
            except discord.errors.HTTPException:
                from main import logger
                from os import system
                logger.warning("Rate limited during sending message")
                system("kill 1")
            except Exception as e:
                from main import logger
                logger.exception(e)
            finally:
                self.blocker = False
                from gc import collect
                collect()

    @tasks.loop(seconds=310)
    async def background_task_market(self):

        def generate_market_embed(input_data, embed_type=None):
            if embed_type == 'diff':
                order_type_name = input_data['name']
                order_type_id = input_data['name_id']
                old_vol = input_data['old_vol']
                new_vol = input_data['new_vol']
                price = input_data['price']
                station_name = input_data['station_name']
                station_type = input_data['station_type']
                region_id = input_data['region_id']
                order_age = input_data['order_age']
                evetime = input_data['evetime']
                if input_data['cheapest'] == False:
                    isk = 'ISK*'
                else:
                    isk = 'ISK'
                embed = discord.Embed(title=f"{order_type_name} {old_vol} -> {new_vol} ({price} {isk})", url=f"https://evetycoon.com/market/{order_type_id}",
                            description=f"Cache age: {order_age} (EVE time: {evetime})", color=0xef600a)
                embed.set_author(name=station_name, url=f'''https://evemaps.dotlan.net/station/{station_name}'''.replace(
                    " ", "_"), icon_url=f"https://e.dotlan.net/images/Station/{station_type}_32.png")
                embed.set_thumbnail(
                    url=f"https://images.evetech.net/types/{order_type_id}/render?size=128")
                return embed
            elif embed_type == 'market_list':
                # TODO
                pass
            else:
                print('embed_type not specified')
                return

        if self.blocker_market:
            return

        self.blocker_market = True
        channel_market = self.get_channel(int(environ['DISCORD_CHANNEL'])) 
        
        try:
            # market_info_ret = market.market_info()
            market_info_ret = await market.as_market_info()
            if market_info_ret:
                for order in market_info_ret:
                    await channel_market.send(discord.utils.get(channel_market.guild.roles, name=environ['MENTION_ROLE']).mention, embed=generate_market_embed(order, embed_type='diff'))

        except Exception as e:
            from main import logger
            logger.exception(e)

        finally:
            self.blocker_market = False
            from gc import collect
            collect()       


    async def setup_hook(self):
        self.background_task.start()
        self.background_task_market.start()

    @background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()

    @background_task_market.before_loop
    async def before_my_task_market(self):
        await self.wait_until_ready()