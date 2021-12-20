#!/usr/bin/python3

import os
import logging

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

import dbreader
import scraper

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

logging.basicConfig(filename='app.log',
    level=logging.WARNING, 
    format='%(asctime)s - %(levelname)s - %(message)s')

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='watch', help='Add a keyword to your watch list.')
async def add_item_watch(ctx, *args):
    if ctx.channel.name == 'bapcs-deals':
        # Return non-duplicated list of lowercase keywords
        keywords = []
        for arg in args:
            if arg.lower() not in keywords:
                keywords.append(arg.lower())
        keyword_list = dbreader.add_remove_keywords(ctx.author.name, ctx.author.id, keywords)
        if len(keyword_list) == 0:
            response = 'You are not watching any keywords.'
        else:
            response = "Updated keyword list:\n"
            for keyword in keyword_list:
                response = response + f"- `{keyword}`\n"
        await ctx.channel.send(response)

@bot.command(name='status', help='List all of your watch settings')
async def print_status(ctx, *args):
    if ctx.channel.name == 'bapcs-deals':
        usertoquery = ''
        if len(args) > 1:
            response = "ERROR: More than one argument detected.\n\n" + \
                "Run this command without any commands to check what you are watching.\n\n" + \
                "Run this command with someones username to find out what they are watching."
        else:
            # If user has any arguments use that as the query instead of their username
            if len(args) == 1:
                usertoquery = args[0] 
            else:
                usertoquery = ctx.author.name
            status = dbreader.return_watcher_info(usertoquery)
            if status == None:
                response = f"Unable to find a watchlist for {usertoquery}."
            else:
                response = f"Here is the config I have for {status['username']}:\n\n"
                if status['target_upvote'] == None or status['target_time'] == None:
                    pop_settings = "They do not have any popularity settings configured.\n\n"
                else:
                    pop_settings = f"They will get notifications for posts that receive " + \
                        f"`{status['target_upvote']}` upvotes in under " + \
                        f"`{status['target_time']}` seconds.\n\n"
                response = response + pop_settings
                if len(status['keyword_list']) == 0:
                    response = response + "They are not watching any keywords."
                else:
                    response = response + "Keywords they are watching:\n"
                    for keyword in status['keyword_list']:
                        response = response + f"- `{keyword}`\n"
        await ctx.channel.send(response)

@bot.command(name='popset', help='Set your post popularity settings.')
async def pop_set(ctx, *args):
    if ctx.channel.name == 'bapcs-deals':
        if len(args) == 1:
            if args[0].lower() == 'stop':
                dbreader.update_watcher_pop_settings(ctx.author.name, ctx.author.id)
            response = "Got it, you wont be notified about new posts anymore."
        else:
            try:
                new_target_upvote = int(args[0])
                new_target_time = int(args[1])
                if new_target_time < 0 or new_target_upvote < 0:
                    raise ValueError
                dbreader.update_watcher_pop_settings(ctx.author.name,
                    ctx.author.id,
                    new_target_upvote=new_target_upvote,
                    new_target_time=new_target_time
                    )
                response = f"Done! You will get notifications for posts that receive " + \
                    f"`{new_target_upvote}` upvotes in under `{new_target_time}` seconds."
            except ValueError:
                response = "ERROR: `<targetupvote>` and `<targettime>` must be positive integers."
            except Exception as e:
                logging.warning(e)
                response = "ERROR: Unknown exception, complain to grumpygramps."
      
        await ctx.channel.send(response)


@tasks.loop(seconds=30)
async def execute_scraper():
    watchers = await scraper.execute()
    if isinstance(watchers, Exception):
        logging.warning(watchers)
        return
    bapcs_channel = discord.utils.get(bot.get_all_channels(), name='bapcs-deals')
    for watcher in watchers:
        if len(watcher['new_posts']) == 0:
            continue
        response = f"**<@{watcher['discord_id']}>, New Posts:**\n\n"
        for post in watcher['new_posts']:
            response = response + f"Title: {post['submission'].title}\n" + \
                f"Link: {post['submission'].shortlink}\n"
            if post['match_reason'] == 'keyword':
                response = response + "Match Reason: Keyword - " + \
                    f"`{post['match_info']}`\n\n"
            else:
                response = response + "Match Reason: Popularity Settings\n" + \
                    f"Seconds since posted: `{post['match_info'].seconds}`\n" + \
                    f"Upvotes: `{post['submission'].score}`\n\n"
            if len(response) > 1000:
                await bapcs_channel.send(response)
                response = ""
        await bapcs_channel.send(response)


@execute_scraper.before_loop
async def before_scraper():
    await bot.wait_until_ready()

execute_scraper.start()
bot.run(TOKEN)
