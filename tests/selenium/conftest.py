import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager


@pytest.fixture(scope="session")
def base_url():
    return "http://127.0.0.1:8099"


@pytest.fixture(scope="session", autouse=True)
def frontend_server():
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    process = subprocess.Popen(
        ["python3", "-m", "http.server", "8099", "--bind", "127.0.0.1"],
        cwd=frontend_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1)
    yield
    process.terminate()
    process.wait(timeout=5)


def _chrome_options() -> ChromeOptions:
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return options


def _firefox_options() -> FirefoxOptions:
    options = FirefoxOptions()
    options.add_argument("-headless")
    return options


def _looks_like_offline_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "could not reach host" in text or "connectionerror" in text or "name or service not known" in text


def _is_missing_browser_binary(exc: Exception) -> bool:
    text = str(exc).lower()
    return "cannot find chrome binary" in text or "binary is not a firefox executable" in text


def _is_startup_timeout(exc: Exception) -> bool:
    text = str(exc).lower()
    return "read timed out" in text or "timeout" in text


def _start_chrome_with_local_driver():
    local_driver = os.getenv("CHROMEDRIVER") or shutil.which("chromedriver")
    if not local_driver:
        return None
    return webdriver.Chrome(service=ChromeService(local_driver), options=_chrome_options())


def _start_firefox_with_local_driver():
    local_driver = os.getenv("GECKODRIVER") or shutil.which("geckodriver")
    if not local_driver:
        return None
    return webdriver.Firefox(service=FirefoxService(local_driver), options=_firefox_options())


def _start_chrome_with_manager():
    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=_chrome_options(),
    )


def _start_firefox_with_manager():
    return webdriver.Firefox(
        service=FirefoxService(GeckoDriverManager().install()),
        options=_firefox_options(),
    )


def _first_available(paths):
    return next((p for p in paths if shutil.which(p) is not None), None)


@pytest.fixture
def driver():
    chrome_binary = _first_available(["google-chrome", "chromium", "chromium-browser"])
    firefox_binary = _first_available(["firefox"])

    if not chrome_binary and not firefox_binary:
        pytest.skip("No local browser binary found for Selenium execution")

    attempts = []

    def try_start(name, fn):
        try:
            browser = fn()
            if browser is not None:
                return browser
            attempts.append(f"{name}: no local driver found")
        except Exception as exc:  # noqa: BLE001
            attempts.append(f"{name}: {exc}")
            if _looks_like_offline_error(exc) or _is_missing_browser_binary(exc) or _is_startup_timeout(exc):
                return None
            if isinstance(exc, WebDriverException):
                return None
            return None
        return None

    # Prefer local drivers first (stable for offline environments).
    browser = None

    if chrome_binary:
        browser = try_start("chrome(local-driver)", _start_chrome_with_local_driver)
        if browser is None:
            browser = try_start("chrome(webdriver-manager)", _start_chrome_with_manager)

    if browser is None and firefox_binary:
        browser = try_start("firefox(local-driver)", _start_firefox_with_local_driver)
        if browser is None:
            browser = try_start("firefox(webdriver-manager)", _start_firefox_with_manager)

    if browser is None:
        attempts_text = " | ".join(attempts) if attempts else "no driver startup attempts"
        pytest.skip(f"Selenium browser startup skipped: {attempts_text}")

    browser.implicitly_wait(3)
    yield browser
    browser.quit()
