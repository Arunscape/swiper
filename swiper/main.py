import inquirer

# from ppadb.client_async import ClientAsync as AdbClient
from ppadb.client import Client as AdbClient
import uiautomator2 as u2
import yaml
import time


# def click_more_info(d):
#     if d(className="android.widget.ImageView", resourceId="com.tinder:id/recsDetailInfo").wait.exists(timeout=100):
#         d(className="android.widget.ImageView", resourceId="com.tinder:id/recsDetailInfo").click()

# def get_bio(d):
#     return d(className="android.widget.TextView", resourceId="com.tinder:id/text_view_bio").info["text"]

# def has_blacklisted_lifestyle(d):
#     lifestyle = d(className="android.view.ViewGroup", resourceId="com.tinder:id/chip_group_descriptors")
#     for l in blacklisted_lifestyles:
#         if lifestyle.child(text=l, className="android.view.View").wait.exists(timeout=1):
#             print(f"Rejected because {l}")
#             return True
#     return False

# def has_blacklisted_interests(d):
#     interests = d(className="android.view.ViewGroup", resourceId="com.tinder:id/chip_group_alibis")
#     for l in blacklisted_interests:
#         if interests.child(text=l, className="android.view.View").wait.exists(timeout=1):
#             print(f"Rejected because {l}")
#             return True
#     return False

# def has_blacklisted_intent(d):
#     for l in blacklisted_intent:
#         if d(text=l, className="android.widget.TextView", resourceId="com.tinder:id/relationship_intent_bottom_prompt").wait.exists(timeout=1):
#             print(f"Rejected because {l}")
#             return True
#     return False

# def has_blacklisted_bio(d):
#     if not d(className="android.widget.TextView", resourceId="com.tinder:id/text_view_bio").wait.exists(timeout=100):
#         return False
#     bio = d(className="android.widget.TextView", resourceId="com.tinder:id/text_view_bio").info["text"]
#     #print(bio)
#     bio = bio.lower()
#     for l in blacklisted_bio:
#         if l in bio:
#             print(f"rejected because '{l}' in bio")
#             return True

#     return False

# def has_blacklisted_job(d):
#     if d(resourceId="com.tinder:id/profile_info_job", className="android.widget.TextView").wait.exists(timeout=100):
#         job = d(resourceId="com.tinder:id/profile_info_job", className="android.widget.TextView").info["text"].lower()
#         for l in blacklisted_jobs:
#             if l in job:
#                 print(f"rejected because {l}")
#                 return True
#     return False

# def reject(d):
#     d(className="android.widget.FrameLayout", resourceId="com.tinder:id/gamepad_pass").click()
# def accept(d):
#     d(className="android.widget.FrameLayout", resourceId="com.tinder:id/gamepad_like").click()

# def main():
#     client = AdbClient(host="127.0.0.1", port=5037)
#     devices = client.devices()
#     devices = [d.serial for d in devices]
#     if len(devices) > 1 :
#         questions = [
#         inquirer.List('device',
#                     message="What device do you wanna connect to?",
#                     choices=devices,
#                 ),
#         ]
#         answers = inquirer.prompt(questions)
#         device = answers['device']
#     else:
#         device = devices[0]
#     #device = await client.device(device)
#     d = u2.connect(device)
#     d.app_start('com.example.hello_world')

#     while True:

#         click_more_info(d)

#         #bio = get_bio(d)
#         #print("Bio: ", bio)

#         if has_blacklisted_interests(d) or has_blacklisted_lifestyle(d) or has_blacklisted_intent(d) or has_blacklisted_bio(d) or has_blacklisted_job(d):
#             reject(d)
#             continue


#         #inquirer.prompt([inquirer.Text('input', message='make a manual decision and press enter to continue')])
#         print('.', end='')
#         x = input("press enter to continue")
#         #time.sleep(1)


class Swiper:
    def __init__(self, device: str):
        self.d = u2.connect(device)
        print(f"Connected to {device}")
        # self.d.app_start("com.tinder"
        self.load_config()
        self.d.open_url("tinder://")

        self.swipe()

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

    def check_job(self):
        if self.d(
            resourceId="com.tinder:id/profile_info_job",
            className="android.widget.TextView",
        ).exists:
            job = (
                self.d(
                    resourceId="com.tinder:id/profile_info_job",
                    className="android.widget.TextView",
                )
                .info["text"]
                .lower()
            )
            for l in self.blacklist["jobs"]["list"]:
                if l in job:
                    self.reject(f"{l} in job: {job}")
                    return True
        return False


if __name__ == "__main__":
    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()
    devices = [d.serial for d in devices]
    if len(devices) < 1:
        print("No devices found")
        exit()
    if len(devices) > 1:
        questions = [
            inquirer.List(
                "device",
                message="What device do you wanna connect to?",
                choices=devices,
            ),
        ]
        answers = inquirer.prompt(questions)
        device = answers["device"]
    else:
        device = devices[0]

    s = Swiper(device)
