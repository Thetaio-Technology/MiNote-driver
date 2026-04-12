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
NAVS = ["全部笔记", "未分类", "最近删除", "未完成", "已完成"]


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


def inspect_current_page(driver: webdriver.Chrome) -> dict:
    return driver.execute_script(
        r"""
        const clean = (value) => (value || '').replace(/\s+/g, ' ').trim();
        const root = document.querySelector('.main-1uw-J') || document.querySelector('.main-group-3qygk') || document.querySelector('#root');
        const searchInputs = Array.from(document.querySelectorAll('input'))
          .map((el) => ({
            placeholder: el.getAttribute('placeholder') || '',
            value: el.value || '',
            className: typeof el.className === 'string' ? el.className : '',
            visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length),
          }))
          .filter((item) => item.visible);

        const buttons = Array.from(document.querySelectorAll('[role="button"], button'))
          .map((el) => clean(el.innerText || el.getAttribute('title') || el.getAttribute('aria-label') || ''))
          .filter(Boolean)
          .slice(0, 80);

        return {
          pageText: clean(root ? root.innerText : '').slice(0, 1500),
          searchInputs,
          buttons,
        };
        """
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    result = {}
    for nav in NAVS:
        driver = build_driver()
        try:
            driver.get(TARGET_URL)
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return !!document.querySelector('#folderList')")
            )
            time.sleep(2)
            print(f"INSPECTING: {nav}")
            click_sidebar_item(driver, nav)
            time.sleep(1)
            result[nav] = inspect_current_page(driver)
        finally:
            driver.quit()

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
