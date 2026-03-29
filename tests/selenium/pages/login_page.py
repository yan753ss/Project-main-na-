from .base_page import BasePage


class LoginPage(BasePage):
    PATH = "/login.html"

    def open_page(self):
        self.open(self.PATH)

    def login(self, email, password):
        self.fill("#email", email)
        self.fill("#password", password)
        self.click("#login-btn")
