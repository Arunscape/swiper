from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

from selenium.webdriver.remote.webelement import WebElement
import logging
"""
{
  "platformName": "Android",
  "automationName": "uiautomator2"
}
"""

# go back is driver.back()
class Swiper:

    def __init__(self):
        capabilities = dict(
            platformName="Android",
            automationName="UiAutomator2",
            espressoBuildConfig="{\"additionalAndroidTestDependencies\": [\"androidx.activity:activity-compose:1.3.1\", \"androidx.lifecycle:lifecycle-extensions:2.2.0\",\"androidx.fragment:fragment:1.3.6\"]}"

        )
        appium_server_url = "http://127.0.0.1:4723"
        self.driver = webdriver.Remote(
            appium_server_url,
            options=UiAutomator2Options().load_capabilities(capabilities),
        )
        self.start_app()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.driver.quit()

    def start_app(self):
        self.driver.activate_app("com.tinder")

    def restart(self):
        self.driver.terminate_app("com.tinder")
        self.start_app()

    def ensure_home(self):
        if self.driver.current_package != "com.tinder":
            self.start_app()

        elif self.driver.current_activity != ".activities.MainActivity":
            self.restart()


        if not len(self.driver.find_elements(by=AppiumBy.ID, value="com.tinder:id/gamepad_like")) > 0:
            self.restart()

    def swipe(self):
        while True:
            self.swipe_once()

    def expand_profile(self):
        self.driver.find_element(by=AppiumBy.XPATH, value='(//android.widget.ImageView[@content-desc="Expand Profile"])[1]').click()

    def like(self):
        self.driver.find_element(by=AppiumBy.ID, value="com.tinder:id/gamepad_like").click()

    def reject(self):
        self.driver.find_element(by=AppiumBy.ID, value="com.tinder:id/gamepad_pass").click()

    def extract_name(self) -> str:
        return self.driver.find_element(by=AppiumBy.ID, value="com.tinder:id/recs_card_user_headline_name").text

    def extract_age(self) -> int:
        age = self.driver.find_element(by=AppiumBy.ID, value="com.tinder:id/recs_card_user_headline_age").text
        return int(age)


    def extract_essentials(self) -> WebElement:
        self.driver.update_settings({"driver": "compose"})
        x = self.driver.find_element(by=AppiumBy.XPATH, value='*')
        logging.warning(x.text)
        return None


    def swipe_once(self):
        self.ensure_home()
        logging.info("am home")

        #name = self.extract_name()
        #logging.warning(f"Name: {name}")

        #age = self.extract_age()
        #logging.warning(f"Age: {age}")

        self.expand_profile()
        self.extract_essentials()
        #self.reject()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    with Swiper() as s:
        s.swipe_once()
