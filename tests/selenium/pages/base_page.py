from selenium.webdriver.common.by import By


class BasePage:
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url

    def open(self, path):
        self.driver.get(f"{self.base_url}{path}")

    def text(self, css):
        return self.driver.find_element(By.CSS_SELECTOR, css).text

    def is_visible(self, css):
        return self.driver.find_element(By.CSS_SELECTOR, css).is_displayed()

    def click(self, css):
        self.driver.find_element(By.CSS_SELECTOR, css).click()

    def fill(self, css, value):
        field = self.driver.find_element(By.CSS_SELECTOR, css)
        field.clear()
        field.send_keys(value)
