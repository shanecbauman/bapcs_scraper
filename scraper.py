#!/usr/bin/python3

# v3 Adds time since posted
# v4 Adds lists/shelves for data control
# v5 Adds SMTP support
# v6 Adds environment variables, keywords
# v7 Replaces shelve with sqlite3
# v8 replaces sqlite3 with sqlalchemy, removes all notification logic

# import logging
import datetime

import asyncio
import asyncpraw
import asyncprawcore

import dbreader

# logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

# Returns time since submission was posted
async def find_time_since_posted(submission):
    postdate = datetime.datetime.utcfromtimestamp(submission.created_utc)
    return datetime.datetime.utcnow() - postdate

async def execute():
    dbreader.delete_old_posts()
    watchers = dbreader.build_watcher_list()
    # PRAW reddit instance
    reddit = asyncpraw.Reddit('bot1')

    try:
        subreddit = await reddit.subreddit("buildapcsales")
        async for submission in subreddit.new(limit=24):
            # If the post is over a day old do not process it or anything after it
            dif = await find_time_since_posted(submission)
            if dif.days >= 1:
                break
            # If post is in database update values
            query = dbreader.query_for_submission(submission.id)
            # print(f"Query: {query}")
            if not query:
                dbreader.add_post_to_db(submission)
            else:
                dbreader.update_post_in_db(submission)
                post_info = dbreader.return_post_info(submission)
            for i, watcher in enumerate(watchers):
                if not query:
                    for j, word in enumerate(watcher["keyword_list"]):
                        if word.lower() in submission.title.lower():
                            watcher["new_posts"].append({
                                "submission": submission,
                                "match_reason": "keyword",
                                "match_info": word
                            })
                            break
                # If time or upvote are none skip popularity check
                elif watcher["target_upvote"] == None or \
                    watcher["target_time"] == None:
                    continue
                else:
                    if watcher['discord_id'] not in post_info['notified_watcher_list'] and \
                        submission.score >= watcher["target_upvote"] and \
                        int(round(dif.total_seconds())) <= watcher["target_time"]:
                        watcher["new_posts"].append({
                            "submission": submission,
                            "match_reason": "popularity",
                            "match_info": dif
                        })
                        # Add watcher to db of notified watchers for this post
                        dbreader.update_post_in_db(submission,
                            notified_watcher=watcher['discord_id'])


        # Print all output as a test
        # for k, watcher in enumerate(watchers):
        #     print(f"{watcher['username']} matches:")
        #     for l, post in enumerate(watcher["new_posts"]):
        #         print(f"Post: {post['submission'].title}",
        #             f"Match reason: {post['match_reason']}",
        #             f"Match Info: {post['match_info']}",
        #             sep="\n"
        #         )

        await reddit.close()
        # Update DB with new posts
        dbreader.push_updates_to_db()
        return watchers

    except Exception as e:
        await reddit.close()
        print(e)
        return e

if __name__ == "__main__":
    asyncio.run(execute())