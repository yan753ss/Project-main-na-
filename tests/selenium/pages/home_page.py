from .base_page import BasePage


class HomePage(BasePage):
    PATH = "/index.html"

    def open_page(self):
        self.open(self.PATH)
