# from ppadb.client_async import ClientAsync as AdbClient
import yaml
import time
import sys
import requests
import json


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
        return [i["title"]["name"] for i in x]

    def intent(self) -> list[str]:
        x = self.data["user"].get("relationship_intent", {}).get("body_text", "")
        return x

    def __repr__(self) -> str:
        x = {
            "name": self.name(),
            "bio": self.bio(),
            "interests": self.interests(),
            "job_titles": self.job_titles(),
            "lifestyles": self.lifestyles(),
            "intent": self.intent(),
        }
        return json.dumps(x, indent=2, ensure_ascii=False)
    
    def check_job(self, blacklist: list[str]):
        blacklist = {b.lower() for b in blacklist}
        jobs = self.job_titles()
        jobs = (j.lower() for j in jobs)
        for j in jobs:
            for b in blacklist:
                if b in j:
                    return True
        return False
                

    def check_bio(self, blacklist: list[str]):
        blacklist = {b.lower() for b in blacklist}
        bio = self.bio().lower()
        for b in blacklist:
            if b in bio:
                return True
        return False

    def check_interests(self, blacklist: list[str]):
        blacklist = {b.lower() for b in blacklist}
        interests = self.interests()
        interests = (i.lower() for i in interests)
        for i in interests:
            if i in blacklist:
                return True
        return False

    def check_intent(self, blacklist: list[str]):
        blacklist = {b.lower() for b in blacklist}
        if self.intent().lower() in blacklist:
            return True
        return False

    def check_lifestyle(self, blacklist: list[str]):
        blacklist = {b.lower() for b in blacklist}
        lifestyles = self.lifestyles()
        lifestyles = (l.lower() for l in lifestyles)
        for l in lifestyles:
            if l in blacklist:
                return True
        return False

class ApiClient:
    def __init__(self, token: str):
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/109.0.5414.112 Mobile/15E148 Safari/604.1"
        self.headers = {
            "User-agent": user_agent,
            "Content-Type": "application/json",
            "X-Auth-Token": token,
        }
        self.baseurl = "https://api.gotinder.com"

    def get_recs(self) -> dict:
        # res = requests.get(self.baseurl+"/v2/recs/core?locale=en", headers=self.headers)
        # return res.json()
        raise Exception("Unimplemented")

    def recs_to_users(self, recs: dict) -> list[User]:
        return [User(r) for r in recs["data"]["results"]]


class Swiper:
    def __init__(self, device: str):
        self.client = ApiClient("token")    
        print(f"Connected to {device}")
        # self.d.app_start("com.tinder"
        self.load_config()
        self.d.open_url("tinder://")

        while True:
            try:
                self.swipe()
            except Exception as e:
                print(e, file=sys.stderr)

    def load_config(self):
        with open("blacklist.yml") as f:
            self.blacklist = yaml.safe_load(f)

    def swipe(self):
        while True:
            self.click_more_info()

            if self.check_bio():
                continue

            if self.check_job():
                continue

            if self.check_lifestyle():
                continue

            if self.check_interests():
                continue

            if self.check_intent():
                continue

            print(".", end="", flush=True)
            time.sleep(0.5)

    def reject(self, reason: str):
        print(f"\nRejected because {reason}")
        self.d(
            className="android.widget.FrameLayout",
            resourceId="com.tinder:id/gamepad_pass",
        ).click()

    def accept(self):
        self.d(
            className="android.widget.FrameLayout",
            resourceId="com.tinder:id/gamepad_like",
        ).click()

    def click_more_info(self):
        if self.d(
            className="android.widget.ImageView",
            resourceId="com.tinder:id/recsDetailInfo",
        ).exists:
            self.d(
                className="android.widget.ImageView",
                resourceId="com.tinder:id/recsDetailInfo",
            ).click()

    def check_lifestyle(self):
        lifestyle = self.d(
            className="android.view.ViewGroup",
            resourceId="com.tinder:id/chip_group_descriptors",
        )
        for l in self.blacklist["lifestyles"]["list"]:
            if lifestyle.child(text=l, className="android.view.View").exists:
                self.reject(f"{l} in lifestyle")
                return True
        return False

    def check_interests(self):
        interests = self.d(
            className="android.view.ViewGroup",
            resourceId="com.tinder:id/chip_group_alibis",
        )
        for l in self.blacklist["interests"]["list"]:
            if interests.child(text=l, className="android.view.View").exists:
                self.reject(f"{l} in interests")
                return True
        return False

    def check_intent(self):
        for l in self.blacklist["intent"]["list"]:
            if self.d(
                text=l,
                className="android.widget.TextView",
                resourceId="com.tinder:id/relationship_intent_bottom_prompt",
            ).exists:
                self.reject(f"{l} in intent")
                return True
        return False

    def check_bio(self):
        if not self.d(
            className="android.widget.TextView",
            resourceId="com.tinder:id/text_view_bio",
        ).exists:
            return False
        bio = self.d(
            className="android.widget.TextView",
            resourceId="com.tinder:id/text_view_bio",
        ).info["text"]
        bio = bio.lower()
        for l in self.blacklist["bio"]["list"]:
            if l in bio:
                self.reject(f"{l} in bio: {bio}")
                return True

        return False

   

       


if __name__ == "__main__":
    import os

    token = os.environ.get("TOKEN")
    if not token:
        raise Exception("no token")
    a = ApiClient(token)

    x = a.get_recs()
    x = json.dumps(x, indent=4)

    with open("testdata.json", "w") as f:
        f.write(x)

    print(x)
