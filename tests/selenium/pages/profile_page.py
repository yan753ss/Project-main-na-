from .base_page import BasePage


class ProfilePage(BasePage):
    PATH = "/profile.html"

    def open_page(self):
        self.open(self.PATH)
