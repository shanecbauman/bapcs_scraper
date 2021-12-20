import dbreader

jim = {
    "username": "jim",
    "discord_id": 1234,
    "target_upvote": None,
    "target_time": None,
    "keyword_list": ["psu", "case", "mouse"]
}

bob = {
    "username": "bob",
    "discord_id": 4321,
    "target_upvote": 8,
    "target_time": 9000,
    "keyword_list": ["ssd", "ram", "fan"]
}

# dbreader.push_pop_settings(jim)

dbreader.add_new_watcher(jim)
dbreader.add_new_watcher(bob)