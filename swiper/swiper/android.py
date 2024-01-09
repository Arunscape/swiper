from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy


class Swiper:
    def __init__(self):
        capabilities = dict(
            platformName="Android",
            automationName="UiAutomator2",
        )
        appium_server_url = "http://127.0.0.1:4723"
        self.driver = webdriver.Remote(
            appium_server_url,
            options=UiAutomator2Options().load_capabilities(capabilities),
        )
        self.start_app()

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

        try:
            self.click_btn(
                '(//android.widget.ImageView[@resource-id="com.tinder:id/navigation_bar_item_icon_view"])[1]'
            )

        except:
            self.restart()

    def go_back(self):
        self.driver.press_keycode(4, undefined, undefined)

    def swipe(self):
        while True:
            self.swipe_once()

    def click_btn(self, xpath: str):
        btn = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        btn.click()

    def expand_profile(self):
        self.click_btn(
            '(//android.widget.ImageView[@content-desc="Expand Profile"])[1]'
        )

    def like(self):
        self.click_btn(
            '//android.widget.ImageView[@resource-id="com.tinder:id/gamepad_like"]'
        )

    def reject(self):
        self.click_btn(
            '//android.widget.ImageView[@resource-id="com.tinder:id/gamepad_pass"]'
        )

    def swipe_once(self):
        self.ensure_home()
        self.reject()


# todo:
# with Swiper() as s:
#
# quit driver when scope ends

s = Swiper()
s.swipe_once()
s.driver.quit()
