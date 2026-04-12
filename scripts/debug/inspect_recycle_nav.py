from pathlib import Path
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait


PROJECT_ROOT = Path(__file__).resolve().parent
CHROMEDRIVER_EXE = PROJECT_ROOT / "bin" / "chromedriver.exe"
CHROME_EXE = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
CHROME_USER_DATA_DIR = PROJECT_ROOT / "chrome_profile"
TARGET_URL = "https://i.mi.com/note/#/"


def build_driver() -> webdriver.Chrome:
    service = Service(str(CHROMEDRIVER_EXE))
    options = Options()
    options.binary_location = str(CHROME_EXE)
    options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--headless=new")
    return webdriver.Chrome(service=service, options=options)


def click_sidebar_item(driver: webdriver.Chrome, label: str) -> None:
    script = """
    const label = arguments[0];
    const items = Array.from(document.querySelectorAll('[role="button"]'))
      .filter((el) => el.closest('#folderList') || el.querySelector('.text-10cyJ'));
    const item = items.find((el) => {
      const text = (el.innerText || '').trim();
      const title = (el.querySelector('.text-10cyJ')?.getAttribute('title') || '').trim();
      return text === label || title === label;
    });
    if (!item) return false;
    item.click();
    return true;
    """
    if not driver.execute_script(script, label):
        raise RuntimeError(f"Sidebar item not found: {label}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    driver = build_driver()
    try:
        driver.get(TARGET_URL)
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return !!document.querySelector('#folderList')")
        )
        time.sleep(2)
        click_sidebar_item(driver, "最近删除")
        time.sleep(1)
        result = driver.execute_script(
            r"""
            const clean = (value) => (value || '').replace(/\s+/g, ' ').trim();
            return Array.from(document.querySelectorAll('[role="button"]')).map((el) => ({
              text: clean(el.innerText || ''),
              title: clean(el.querySelector('.text-10cyJ')?.getAttribute('title') || ''),
              className: typeof el.className === 'string' ? el.className : '',
            })).filter((item) => item.text || item.title);
            """
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
