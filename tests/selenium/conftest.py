import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest
from selenium import webdriver
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


def _start_chrome_from_local_driver():
    local_driver = os.getenv("CHROMEDRIVER") or shutil.which("chromedriver")
    if not local_driver:
        return None
    return webdriver.Chrome(service=ChromeService(local_driver), options=_chrome_options())


def _start_firefox_from_local_driver():
    local_driver = os.getenv("GECKODRIVER") or shutil.which("geckodriver")
    if not local_driver:
        return None
    return webdriver.Firefox(service=FirefoxService(local_driver), options=_firefox_options())


def _looks_like_offline_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "could not reach host" in text or "connectionerror" in text or "name or service not known" in text


@pytest.fixture
def driver():
    browser_available = any(
        shutil.which(binary) is not None
        for binary in ["google-chrome", "chromium", "chromium-browser", "firefox"]
    )

    if not browser_available:
        pytest.skip("No local browser binary found for Selenium execution")

    # 1) Prefer local drivers in offline/air-gapped environments.
    browser = _start_chrome_from_local_driver() or _start_firefox_from_local_driver()
    if browser is None:
        # 2) Fallback to webdriver-manager downloads.
        try:
            browser = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=_chrome_options(),
            )
        except Exception as chrome_exc:
            if _looks_like_offline_error(chrome_exc):
                pytest.skip(
                    "WebDriver download failed (offline). Install local chromedriver/geckodriver "
                    "and optionally export CHROMEDRIVER/GECKODRIVER."
                )
            try:
                browser = webdriver.Firefox(
                    service=FirefoxService(GeckoDriverManager().install()),
                    options=_firefox_options(),
                )
            except Exception as firefox_exc:
                if _looks_like_offline_error(firefox_exc):
                    pytest.skip(
                        "WebDriver download failed (offline). Install local chromedriver/geckodriver "
                        "and optionally export CHROMEDRIVER/GECKODRIVER."
                    )
                raise

    browser.implicitly_wait(3)
    yield browser
    browser.quit()
