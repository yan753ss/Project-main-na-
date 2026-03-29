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


@pytest.fixture
def driver():
    browser_available = any(
        shutil.which(binary) is not None
        for binary in ["google-chrome", "chromium", "chromium-browser", "firefox"]
    )

    if not browser_available:
        pytest.skip("No local browser binary found for Selenium execution")

    browser = None

    try:
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    except Exception:
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("-headless")
        browser = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=firefox_options)

    browser.implicitly_wait(3)
    yield browser
    browser.quit()
