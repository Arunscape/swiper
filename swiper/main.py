import yaml
import requests
import json
import sqlite3
import logging
import os
import time
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class User:
    def __init__(self, data: dict):
        self.data = data

    def bio(self) -> str:
        return self.data["user"]["bio"]
    def name(self) -> str:
        return self.data["user"]["name"]

    def interests(self) -> list[str]:
        x = self.data.get("experiment_info", {}).get("user_interests", {}).get("selected_interests", [])
        return [i["name"] for i in x]
    
    def lifestyles(self) -> list[str]:
        x = self.data["user"].get("selected_descriptors", [])

        ret = {}

        for lifestyle in x:
            name = lifestyle["name"]
            choices = lifestyle["choice_selections"]
            choices = [c["name"] for c in choices]

            ret[name] = choices
        return [i for j in ret.values() for i in j]


    def job_titles(self) -> str:
        x = self.data["user"]["jobs"]
        res = []
        for i in x:
            if "title" in i:
                if "name" in i:
                    res.append(i["title"]["name"])
        return res

    def intent(self) -> list[str]:
        x = self.data["user"].get("relationship_intent", {}).get("body_text", "")
        return x

    def music_artists(self) -> list[str]:
        top_artists = self.data["spotify"]["spotify_top_artists"]
        top_artists = [i["name"] for i in top_artists]

        anthem = self.data["spotify"].get("spotify_theme_track", {}).get("artists", [])
        anthem = [i["name"] for i in anthem]
        artists = top_artists + anthem

        return artists

    def id(self) -> str:
        return self.data["user"]["_id"]

    def s_number(self) -> str:
        return self.data["s_number"]

    def photos(self) -> list[str]:
        photos = self.data["user"]["photos"]
        return [p["url"] for p in photos]

    def __repr__(self) -> str:
        x = {
            "name": self.name(),
            "bio": self.bio(),
            "interests": self.interests(),
            "job_titles": self.job_titles(),
            "lifestyles": self.lifestyles(),
            "intent": self.intent(),
            "music_artists": self.music_artists(),
        }
        return json.dumps(x, indent=2, ensure_ascii=False)
    
    def check_job(self, blacklist: list[str]) -> str | None:
        jobs = self.job_titles()
        jobs = (j.lower() for j in jobs)
        for j in jobs:
            for b in blacklist:
                if b in j:
                    return b
        return None
                

    def check_bio(self, blacklist: list[str]) -> set[str]:
        bio = self.bio().lower()

        return {b for b in blacklist if b in bio }

    def check_interests(self, blacklist: list[str]) -> set[str]:
        interests = self.interests()
        interests = (i.lower() for i in interests)

        return {i for i in interests if i in blacklist}

    def check_intent(self, blacklist: list[str]) -> str | None:
        intent = self.intent().lower()
        return intent if intent in blacklist else None


    def check_lifestyle(self, blacklist: list[str]) -> set[str]:
        lifestyles = self.lifestyles()
        lifestyles = (l.lower() for l in lifestyles)

        return {l for l in lifestyles if l in blacklist}

    def check_music(self, whitelist: list[str]) -> set[str]:
        artists = self.music_artists()
        artists = (a.lower() for a in artists)

        return {a for a in artists if a in whitelist}


class Stats:
    def __init__(self):
        cwd = cwd = os.path.dirname(__file__) 
        self.con = sqlite3.connect(os.path.join(cwd, "stats.db"))
        self.cur = self.con.cursor()

        self.cur.execute("CREATE TABLE IF NOT EXISTS stats (id TEXT PRIMARY KEY, name TEXT, bio TEXT, intent TEXT, action TEXT, reason TEXT)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS interests (id TEXT, interest TEXT)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS lifestyles (id TEXT, lifestyle TEXT)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT, job TEXT)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS music_artists (id TEXT, music_artist TEXT)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS photos (id TEXT, photo TEXT)")

    def add(self, user: User, action: str, reason: str):
        self.cur.execute("INSERT OR IGNORE INTO stats VALUES (?, ?, ?, ?, ?, ?)", (user.id(), user.name(), user.bio(), user.intent(), action, reason))
        for i in user.interests():
            self.cur.execute("INSERT OR IGNORE INTO interests VALUES (?, ?)", (user.id(), i))
        for l in user.lifestyles():
            self.cur.execute("INSERT OR IGNORE INTO lifestyles VALUES (?, ?)", (user.id(), l))
        for j in user.job_titles():
            self.cur.execute("INSERT OR IGNORE INTO jobs VALUES (?, ?)", (user.id(), j))
        for m in user.music_artists():
            self.cur.execute("INSERT OR IGNORE INTO music_artists VALUES (?, ?)", (user.id(), m))
        for p in user.photos():
            self.cur.execute("INSERT OR IGNORE INTO photos VALUES (?, ?)", (user.id(), p))

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
        return res.json()

    def recs_to_users(self, recs: dict) -> list[User]:
        return [User(r) for r in recs["data"]["results"]]

    def get_users(self) -> list[User]:
        recs = self.get_recs()
        return self.recs_to_users(recs)

    def like(self, id: str, s_number: str):
        
        res = requests.get(self.baseurl+ f"/like/{id}", headers=self.headers, params={"_id": id, "s_number": s_number})

        if res.status_code == 200:
            # logging.info(f"liked {id} with s_number {s_number}")
            pass
        else:
            logging.warning(f"failed to like {id} with s_number {s_number}: {res.text}")
        return res.text

    def dislike(self, id: str, s_number: str):

        res = requests.get(self.baseurl+ f"/pass/{id}", headers=self.headers, params={"_id": id, "s_number": s_number})
        
        if res.status_code == 200:
            # logging.info(f"liked {id} with s_number {s_number}")
            pass
        else:
            logging.warning(f"failed to like {id} with s_number {s_number}: {res.text}")
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

        # lowercase the items
        for k, v in self.blacklist.items(): 
            self.blacklist[k] = [i.lower() for i in v]
        for k, v in self.whitelist.items():
            self.whitelist[k] = [i.lower() for i in v]

    def swipe(self):
        while True:
            time.sleep(5)
            users = self.client.get_users()

            for user in users:
                time.sleep(5)
                reason = self.check_whitelist(user)
                if reason:
                    self.client.like(user.id(), user.s_number())
                    self.stats.add(user, "like", reason)
                    logging.info(f"liked {user.id()} {user.name()} because: {reason}")
                    continue

                reason = self.check_blacklist(user)
                if reason:
                    self.client.dislike(user.id(), user.s_number())
                    self.stats.add(user, "dislike", reason)
                    logging.info(f"rejected {user.id()} {user.name()} because: {reason}")
                    continue

                logging.info(f"skipped {user.id()} {user.name()}")
                self.stats.add(user, "skipped", "")
            

            

    def check_whitelist(self, user: User) -> str | None:
        result = ""

        matching_interests = user.check_interests(self.whitelist["interests"])
        if matching_interests:
            result +=  f"{matching_interests} in interests "
            

        matching_music = user.check_music(self.whitelist["music_artists"])
        if user.check_music(self.whitelist["music_artists"]):
            result += f"{matching_music} in music "

        return result if result else None

    def check_blacklist(self, user: User) -> str | None:
    
            result = ""
    
            lifestyles = user.check_lifestyle(self.blacklist["lifestyles"])
            if lifestyles:
                result += f"{lifestyles} in lifestyle "

            interests = user.check_interests(self.blacklist["interests"])
            if interests:
                result += f"{interests} in interests "

            intent = user.check_intent(self.blacklist["intent"])
            if intent:
                result += f"{intent} in intent "

            job = user.check_job(self.blacklist["jobs"])  
            if job:
                result += f"{job} in job "

            bio = user.check_bio(self.blacklist["bio"])
            if bio:
                result += f"{bio} in bio "
    
            return result if result else None
    

   

       


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
