import sys
import yaml
import requests
import json
import sqlite3
import logging
import os
import time
from typing import TypedDict, Literal
from collections.abc import Iterable
import functools
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class LikedReasons(TypedDict):
    interest: set[str]
    music_artist: set[str]

class RejectedReasons(TypedDict):
    intent: set[str]
    bio: set[str]
    job: set[str]
    interest: set[str]
    lifestyle: set[str]

class User:
    def __init__(self, data: dict):
        self.data = data

    @functools.cached_property
    def bio(self) -> str:
        return self.data["user"]["bio"]
    
    @functools.cached_property
    def name(self) -> str:
        return self.data["user"]["name"]

    @functools.cached_property
    def interests(self) -> list[str]:
        x = self.data.get("experiment_info", {}).get("user_interests", {}).get("selected_interests", [])
        return [i["name"] for i in x]
    
    @functools.cached_property
    def lifestyles(self) -> list[str]:
        x = self.data["user"].get("selected_descriptors", [])

        ret = {}

        for lifestyle in x:
            name = lifestyle.get("name", None)
            if name is None:
                continue
            choices = lifestyle["choice_selections"]
            choices = [c["name"] for c in choices]

            ret[name] = choices
        return [i for j in ret.values() for i in j]


    @functools.cached_property
    def job_titles(self) -> list[str]:
        x = self.data["user"]["jobs"]
        res = []
        for i in x:
            if "title" in i:
                if "name" in i:
                    res.append(i["title"]["name"])
        return res

    @functools.cached_property
    def intent(self) -> str:
        x = self.data["user"].get("relationship_intent", {}).get("body_text", "")
        return x

    @functools.cached_property
    def music_artists(self) -> list[str]:
        top_artists = self.data["spotify"]["spotify_top_artists"]
        top_artists = [i["name"] for i in top_artists]

        anthem = self.data["spotify"].get("spotify_theme_track", {}).get("artists", [])
        anthem = [i["name"] for i in anthem]
        artists = top_artists + anthem

        return artists

    @functools.cached_property
    def id(self) -> str:
        return self.data["user"]["_id"]

    @functools.cached_property
    def s_number(self) -> str:
        return self.data["s_number"]

    @functools.cached_property
    def photos(self) -> list[str]:
        photos = self.data["user"]["photos"]
        return [p["url"] for p in photos]

    def __repr__(self) -> str:
        x = {
            "name": self.name,
            "bio": self.bio,
            "interests": self.interests,
            "job_titles": self.job_titles,
            "lifestyles": self.lifestyles,
            "intent": self.intent,
            "music_artists": self.music_artists,
        }
        return json.dumps(x, indent=2, ensure_ascii=False)
    
    def check_job(self, blacklist: Iterable[str]) -> set[str]:
        jobs = self.job_titles
        jobs = (j.lower() for j in jobs)

        ret = set()
        for j in jobs:
            for b in blacklist:
                if b in j:
                    ret.add(b)
        return ret

    def check_bio(self, blacklist: Iterable[str]) -> set[str]:
        bio = self.bio.lower()

        return {b for b in blacklist if b in bio }

    def check_interests(self, blacklist: Iterable[str]) -> set[str]:
        interests = self.interests
        interests = (i.lower() for i in interests)

        return {i for i in interests if i in blacklist}

    def check_intent(self, blacklist: Iterable[str]) -> set[str]:
        intent = self.intent.lower()
        return {intent} if intent in blacklist else set()

    def check_lifestyle(self, blacklist: Iterable[str]) -> set[str]:
        lifestyles = self.lifestyles
        lifestyles = (l.lower() for l in lifestyles)

        return {l for l in lifestyles if l in blacklist}

    def check_music(self, whitelist: Iterable[str]) -> set[str]:
        artists = self.music_artists
        artists = (a.lower() for a in artists)

        return {a for a in artists if a in whitelist}


class Stats:
    def __init__(self):
        cwd = cwd = os.path.dirname(__file__) 
        self.con = sqlite3.connect(os.path.join(cwd, "stats.db"))
        self.cur = self.con.cursor()

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id TEXT PRIMARY KEY,
            name TEXT,
            bio TEXT,
            intent TEXT,
            action TEXT,
            seen_times INTEGER,
            time INTEGER
            )""")
        self.cur.execute("CREATE TABLE IF NOT EXISTS interests (id TEXT, interest TEXT)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS lifestyles (id TEXT, lifestyle TEXT)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT, job TEXT)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS music_artists (id TEXT, music_artist TEXT)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS photos (id TEXT, photo TEXT)")

        self.cur.execute("CREATE TABLE IF NOT EXISTS rejected (id TEXT, category TEXT, value TEXT)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS approved (id TEXT, category TEXT, value TEXT)")

    def add(self, user: User, action: Literal["like", "reject", "skip"], reasons: LikedReasons | RejectedReasons | None):
        self.cur.execute("""
        INSERT INTO stats VALUES (:id, :name, :bio, :intent, :action, 1, strftime('%s', 'now'))
        ON CONFLICT(id) DO UPDATE SET
        name = :name,
        bio = :bio,
        intent = :intent,
        action = :action,
        seen_times = seen_times + 1,
        time = strftime('%s', 'now')
        """, {
            "id": user.id,
            "name": user.name,
            "bio": user.bio,
            "intent": user.intent,
            "action": action,
        })
        
        self.cur.executemany("INSERT OR IGNORE INTO interests VALUES (?, ?)", ((user.id, i) for i in user.interests))
        self.cur.executemany("INSERT OR IGNORE INTO lifestyles VALUES (?, ?)", ((user.id, l) for l in user.lifestyles))
        self.cur.executemany("INSERT OR IGNORE INTO jobs VALUES (?, ?)", ((user.id, j) for j in user.job_titles))
        self.cur.executemany("INSERT OR IGNORE INTO music_artists VALUES (?, ?)", ((user.id, m) for m in user.music_artists))
        self.cur.executemany("INSERT OR IGNORE INTO photos VALUES (?, ?)", ((user.id, p) for p in user.photos))

        if action == "like":
            for k, v in reasons.items():
                if v is None:
                    break
                self.cur.executemany("INSERT OR IGNORE INTO approved VALUES (?, ?, ?)", ((user.id, k, i) for i in v))

        elif action == "reject":
            for k, v in reasons.items():
                if v is None:
                    break
                self.cur.executemany("INSERT OR IGNORE INTO rejected VALUES (?, ?, ?)", ((user.id, k, i) for i in v))

        else:
            assert action == "skipped"

        self.con.commit()


class ApiClient:
    def __init__(self, token: str):
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/109.0.5414.112 Mobile/15E148 Safari/604.1"
        self.headers = {
            "User-agent": user_agent,
            "Content-Type": "application/json",
            "X-Auth-Token": token,
        }
        self.baseurl = "https://api.gotinder.com"
        # self.baseurl = "http://localhost:5000"

    def get_recs(self) -> dict:
        res = requests.get(self.baseurl+"/v2/recs/core?locale=en", headers=self.headers)
        # logging.info(f"got recs {res.status_code}")
        # logging.info(res.text)
        if res.status_code == 200:
            return res.json()

        if res.status_code == 401:
            logging.error("unauthorized: invalid token")
            sys.exit(1)
        
        logging.error(f"failed to get recs {res.status_code} {res.text}")
        return {}

    def recs_to_users(self, recs: dict) -> list[User]:
        return [User(r) for r in recs.get("data", {}).get("results", [])]

    def get_users(self) -> list[User]:
        recs = self.get_recs()
        return self.recs_to_users(recs)

    def like(self, id: str, s_number: str):
        
        res = requests.get(self.baseurl+ f"/like/{id}", headers=self.headers, params={"locale": "en"})

        if res.status_code == 200:
            pass
        else:
            logging.warning(f"failed to like {id}")
        return res.text

    def reject(self, id: str, s_number: str):

        res = requests.get(self.baseurl+ f"/pass/{id}", headers=self.headers, params={"locale": "en", "s_number": s_number})
        
        if res.status_code == 200:
            pass
        else:
            logging.warning(f"failed to reject {id} with s_number {s_number}: {res.text}")
        return res.text

class Swiper:
    def __init__(self, token: str):
        self.client = ApiClient(token)
        self.stats = Stats()
        self.load_config()
        
    def load_config(self):
        cwd = os.path.dirname(__file__) 
        with open(os.path.join(cwd, "blacklist.yml")) as f:
            self.blacklist = yaml.safe_load(f)
        logging.info(f"loaded blacklist: {self.blacklist}")

        with open(os.path.join(cwd, "whitelist.yml")) as f:
            self.whitelist = yaml.safe_load(f)
        logging.info(f"loaded whitelist: {self.whitelist}")
        
        if self.blacklist is None or self.whitelist is None:
            logging.error("failed to load config")
            exit(1)

        # lowercase the items
        for k, v in self.blacklist.items(): 
            self.blacklist[k] = [i.lower() for i in v]
        for k, v in self.whitelist.items():
            self.whitelist[k] = [i.lower() for i in v]

    def swipe(self, testing: bool = False):
        while True:
            time.sleep(5)
            users = self.client.get_users()

            for user in users:
                time.sleep(5)
                reasons = self.check_whitelist(user)
                if reasons:
                    self.client.like(user.id, user.s_number)
                    self.stats.add(user, "like", reasons)
                    logging.info(f"liked {user.id} {user.name} because: {reasons}")
                    continue

                reasons = self.check_blacklist(user)
                if reasons:
                    self.client.reject(user.id, user.s_number)
                    self.stats.add(user, "reject", reasons)
                    logging.info(f"rejected {user.id} {user.name} because: {reasons}")
                    continue

                logging.info(f"skipped {user.id} {user.name}")
                self.stats.add(user, "skipped", None)
            if testing:
                break
            

    def check_whitelist(self, user: User) -> LikedReasons | None:
        result: LikedReasons = dict()

        result["interests"] = user.check_interests(self.whitelist["interests"])           
        result["music"] = user.check_music(self.whitelist["music_artists"])

        if any(result.values()):
            return result
        
        return None

    def check_blacklist(self, user: User) -> RejectedReasons | None:
        result: RejectedReasons = dict()
    
        result["lifestyle"] = user.check_lifestyle(self.blacklist["lifestyles"])
        result["interests"] = user.check_interests(self.blacklist["interests"])
        result["intent"] = user.check_intent(self.blacklist["intent"])
        result["job"] = user.check_job(self.blacklist["jobs"])  
        result["bio"] = user.check_bio(self.blacklist["bio"])
    
        if any(result.values()):
            return result
        
        return None


if __name__ == "__main__":
    import os

    token = os.environ.get("TOKEN")
    if not token:
        raise Exception("no token")
    # a = ApiClient(token)

    # x = a.get_recs()
    # x = json.dumps(x, indent=4)

    # with open("testdata.json", "w") as f:
    #     f.write(x)

    # print(x)
    s = Swiper(token)
    s.swipe()
