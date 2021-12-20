# bapcs_scraper
Discord bot to manage notifications from r/buildapcsales.

This bot will run in your discord under the channel `bapcs-deals`.  It allows you to set notifications via keywords or popular posts.

If your waiting on a good deal on a computer product add the product name to your watch list via the `!watch` command, the minute a new deal is posted for that product the discord bot will @mention you in the channel with the post details.

The same goes for popular posts, configure your popularity threshold and the bot will @mention you when a post has met your popularity criteria.  (Criteria being a certain amount of upvotes in a certain amount of time)

Manage the bot via the commands in the same discord channel.

**Make sure you have the channel notifications set to @mentions only, otherwise you will get notifications for everyone else.**

Built to run on linux as a service. You will need to setup a [PRAW INI file](https://praw.readthedocs.io/en/stable/getting_started/configuration/prawini.html), along with an .env file with your discord token.
