Per https://praw.readthedocs.io/en/latest/getting_started/quick_start.html it looks like we can request 100 items per call

Pulled from https://praw.readthedocs.io/en/latest/code_overview/models/submission.html
  Things to track on the first call:
    created_utc - Time the submission was created, represented in Unix Time.
    id - ID of the submission.
    title - The title of the submission.
    num_comments - The number of comments on the submission.
    score - The number of upvotes for the submission.
    upvote_ratio - The percentage of upvotes from all votes on the submission.
    url - The URL the submission links to, or the permalink if a selfpost.

  Things to track on each call thereafter:
    time since created, if its been 24 hours stop tracking
    num_comments
    score
    upvote_ratio

Have the bot run the script in the background with https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
- This will make everything into one script
- Still need to update the table, but dont have to worry about sending the results to another script, will already have them
- Can modify the scraper to run every 15 sec, 30 sec, etc
- Add it as a system service


TODO:

[x] Add new_posts key to watcher list after there is a match, along with the relevant post info
[x] Iterate through posts and send message to users about any new posts
 [x] Include the reason they were notified
 [x] Make sure to tag them so they get a notification (this can be done with ctx.author.id or ctx.author.mention)
  [x] Will need to rewrite the other commands so the author id is added to the database also
[x] Clear out all posts that are over a day old
[] Write out all discord commands and verify they are working
  [x] Status command
    [x] Modify message so if person has new posts settings disabled it says that intead of "None"
    [x] Status is printing out correctly, need to add logic so you can query what other people are watching
  [x] keyword command
   [x] Combining add/delete usage into one command
    [x] Working on cleaning up database keywords when providing a new keyword list
  [x] Add/delete/modify popularity post command
   [x] Add logic to check that arguments are integers
   [x] Add logic to prevent negative integer arguments
   [x] Add logic to disble popular post notifications (DB accepts None into an integer field, that could be how we disable notifications per user)
[x] Migrate praw over to async praw: 
- https://asyncpraw.readthedocs.io/en/stable/getting_started/quick_start.html
- https://praw.readthedocs.io/en/latest/getting_started/multiple_instances.html#discord-bots-and-asynchronous-environments
[x] Move bot to a system service so it will run on boot and reload on crashes
 - https://www.reddit.com/r/linuxquestions/comments/fwjq0e/run_discord_bot_when_raspberry_pi_boots/
[] If watcher is notified of post from a keyword, they can be notified again if its triggered from their popularity settings
 - Need to update DB when the watcher get notified via a keyword so notifications dont duplicate