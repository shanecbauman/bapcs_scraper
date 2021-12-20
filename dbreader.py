import datetime

import sqlalchemy as db
from sqlalchemy import create_engine, asc
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, joinedload, relationship
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.schema import ForeignKey


engine = create_engine('sqlite:///watchdb.sqlite', echo=False)
Session = sessionmaker(bind=engine)

Base = declarative_base()


class Post(Base):
    __tablename__ = "posts"
    id = Column(String, primary_key=True)
    created_utc = Column(Float)
    title = Column(String)
    num_comments = Column(String)
    score = Column(Integer)
    upvote_ratio = Column(Float)
    url = Column(String)


class Notified_Watcher(Base):
    __tablename__ = "notified_watchers"
    id = Column(Integer, primary_key=True)
    post_id = Column(String, ForeignKey('posts.id'))
    discord_id = Column(Integer)


class Watcher(Base):
    __tablename__ = "watchers"
    username = Column(String, primary_key=True)
    discord_id = Column(Integer)
    target_upvote = Column(Integer)
    target_time = Column(Integer)


class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True)
    word = Column(String, nullable=False)
    username = Column(String, ForeignKey('watchers.username'))
    # user = relationship("Watcher", back_populates="keyword_list")

Watcher.keyword_list = relationship("Keyword", \
    order_by=Keyword.id, \
    cascade="all, delete, delete-orphan")

Post.notified_watcher_list = relationship("Notified_Watcher", \
    order_by=Notified_Watcher.id, \
    cascade="all, delete, delete-orphan")

Base.metadata.create_all(engine)
session = Session()


def query_for_submission(submission_id):
    '''Returns none if submission is not in db'''
    return session.query(Post).filter(Post.id == submission_id).first()

def delete_old_posts():
    '''
    Sort posts by oldest and delete until they are under a day old
    '''
    posts = session.query(Post).order_by(asc(Post.created_utc))
    for post in posts:
        time_since_posted = datetime.datetime.utcnow() - \
            datetime.datetime.utcfromtimestamp(post.created_utc)
        if time_since_posted.days >= 1:
            session.delete(post)
        else:
            push_updates_to_db()
            break

def build_watcher_list():
    '''
    Grabs the whole watcher table,
    builds out a list of a watchers and their relevant variables
    '''
    watcherQuery = session.query(Watcher)
    watchers = []
    for watcher in watcherQuery:
        watchers.append({
            "username": watcher.username,
            "discord_id": watcher.discord_id,
            "target_time": watcher.target_time,
            "target_upvote": watcher.target_upvote,
            "keyword_list": [keyword.word for keyword in watcher.keyword_list],
            "new_posts": []
        })
    return watchers

def return_watcher_info(username):
    watcher = session.query(Watcher).filter(Watcher.username == username).first()
    if watcher is None:
        return watcher
    return {
        "username": watcher.username,
        "discord_id": watcher.discord_id,
        "target_time": watcher.target_time,
        "target_upvote": watcher.target_upvote,
        "keyword_list": [keyword.word for keyword in watcher.keyword_list]
    }

def return_post_info(submission):
    post = session.query(Post).filter(Post.id == submission.id).first()
    if post is None:
        return post
    return {
        "id": post.id,
        "created_utc": post.created_utc,
        "title": post.title,
        "num_comments": post.num_comments,
        "score": post.score,
        "upvote_ratio": post.upvote_ratio,
        "url": post.url,
        "notified_watcher_list": [
            notified_watcher.discord_id for \
            notified_watcher in \
            post.notified_watcher_list
        ]
    }

def prepareDBUpdate(submission):
    post = Post(
        id = submission.id,
        created_utc = submission.created_utc,
        title = submission.title,
        num_comments = submission.num_comments,
        score = submission.score,
        upvote_ratio = submission.upvote_ratio,
        url = submission.shortlink
    )
    return post

def add_post_to_db(submission):
    session.add(prepareDBUpdate(submission))

def update_post_in_db(submission, notified_watcher=None):
    if not notified_watcher:
        session.query(Post).filter(Post.id == submission.id).\
            update({
                "num_comments": submission.num_comments,
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio
            })
    else:
        post = session.query(Post).filter(Post.id == submission.id).first()
        update = Notified_Watcher(
            post_id = submission.id,
            discord_id = notified_watcher
        )
        post.notified_watcher_list.append(update)
    push_updates_to_db()

def push_updates_to_db():
    session.commit()

def add_new_watcher(user_args):
    user = Watcher(
        username=user_args["username"],
        discord_id = user_args["discord_id"],
        target_upvote = user_args["target_upvote"],
        target_time = user_args["target_time"]
    )
    user.keyword_list = [
        Keyword(word=keyword) for keyword in user_args["keyword_list"]
    ]
    session.add(user)
    push_updates_to_db()

def push_pop_settings(user_args):
    session.query(Watcher).\
        filter(Watcher.username == user_args["username"]).\
        update({
            "target_upvote": user_args["target_upvote"],
            "target_time": user_args["target_time"],
        })
    push_updates_to_db()

def update_watcher_pop_settings(username, discord_id, new_target_upvote=None, new_target_time=None):
    # If watcher is already in DB update the current settings
    status = return_watcher_info(username)
    if status == None:
        watcher = {
            "username": username,
            "discord_id": discord_id,
            "target_upvote": new_target_upvote,
            "target_time": new_target_time,
            "keyword_list": []
        }
        add_new_watcher(watcher)
        push_updates_to_db()
    # Otherwise, add new settings to DB for that watcher
    else:
        status["target_upvote"] = new_target_upvote
        status["target_time"] = new_target_time
        push_pop_settings(status)

def update_watcher_keywords(watcher_settings):
    watcher = session.query(Watcher).filter(Watcher.username == watcher_settings["username"]).first()
    session.delete(watcher)
    add_new_watcher(watcher_settings)

def add_remove_keywords(username, discord_id, keyword_list):
    watcher = return_watcher_info(username)
    # If username is not in DB add all keywords
    if watcher is None:
        add_new_watcher({
            'username': username,
            'discord_id': discord_id,
            'target_upvote': None,
            'target_time': None,
            'keyword_list': keyword_list
        })
        return keyword_list
    # Otherwise iterate through current keyword list
    # Add keywords if they are NOT in the list
    # Remove them if they are in the list
    else:
        new_keywords = []
        all_keywords = watcher['keyword_list'] + keyword_list
        all_keywords.sort()
        # List is sorted so all duplicates should be next to each other
        # If the item to the left or the right of the current iterable is a duplicate
        # then remove it from list
        for i, keyword in enumerate(all_keywords):
            # If your checking the last item in the list only check to the left
            if i == len(all_keywords) - 1:
                if keyword == all_keywords[i-1]:
                    continue
                else:
                    new_keywords.append(keyword)
            elif keyword == all_keywords[i-1] or keyword == all_keywords[i+1]:
                continue
            # Otherwise its not a duplicate, add it to updated keyword list
            else:
                new_keywords.append(keyword)
        watcher['keyword_list'] = new_keywords
        update_watcher_keywords(watcher)
        return new_keywords