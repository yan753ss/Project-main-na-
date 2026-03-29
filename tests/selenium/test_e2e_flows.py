from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from tests.selenium.pages.home_page import HomePage
from tests.selenium.pages.login_page import LoginPage
from tests.selenium.pages.profile_page import ProfilePage


def test_home_page_elements_visible(driver, base_url):
    page = HomePage(driver, base_url)
    page.open_page()

    assert page.is_visible("#page-title")
    assert page.text("#page-title") == "Интернет-магазин"
    assert page.is_visible("#nav-login")
    assert page.is_visible("#nav-profile")


def test_login_validation_for_empty_fields(driver, base_url):
    page = LoginPage(driver, base_url)
    page.open_page()

    page.click("#login-btn")

    assert page.is_visible("#login-error")
    assert page.text("#login-error") == "Заполните email и пароль"


def test_success_login_redirects_to_profile(driver, base_url):
    page = LoginPage(driver, base_url)
    page.open_page()

    page.login("student@example.com", "Password123")

    WebDriverWait(driver, 5).until(ec.url_contains("/profile.html"))
    assert "/profile.html" in driver.current_url

    profile_message = driver.find_element(By.CSS_SELECTOR, "#profile-message").text
    assert "student@example.com" in profile_message


def test_profile_redirects_to_login_if_user_not_authorized(driver, base_url):
    profile = ProfilePage(driver, base_url)
    profile.open_page()

    driver.execute_script("localStorage.removeItem('currentUserEmail');")
    profile.open_page()

    WebDriverWait(driver, 5).until(ec.url_contains("/login.html"))
    assert "/login.html" in driver.current_url
