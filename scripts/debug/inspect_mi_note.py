from pathlib import Path
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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


def wait_for_app(driver: webdriver.Chrome) -> None:
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return !!document.querySelector('#folderList')")
    )


def click_sidebar_item(driver: webdriver.Chrome, label: str) -> None:
    script = """
    const label = arguments[0];
    const items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
    const item = items.find((el) => (el.innerText || '').trim() === label);
    if (!item) return false;
    item.click();
    return true;
    """
    if not driver.execute_script(script, label):
        raise RuntimeError(f"Sidebar item not found: {label}")


def read_visible_items(driver: webdriver.Chrome) -> list[dict]:
    script = """
    const clean = (value) => (value || '').replace(/\s+/g, ' ').trim();
    const todoContainer = document.querySelector('.main-group-3qygk.todo-page-2xEZZ.item-list-2UYnn');
    if (todoContainer) {
      const cards = Array.from(todoContainer.querySelectorAll('.item-3HTE8'))
        .map((el) => {
          const titleInput = el.querySelector('input.text-field-2euJG');
          const title = clean(titleInput ? titleInput.value : '');
          const counter = clean(el.querySelector('.finished-counter-3CDy8')?.innerText || '');
          const remind = clean(el.querySelector('.set-remind-KMc61')?.innerText || '');
          const text = clean(el.innerText || '');
          return {
            title,
            counter,
            remind,
            text,
            className: typeof el.className === 'string' ? el.className : '',
          };
        })
        .filter((item) => item.title || item.text)
        .slice(0, 100);

      return {
        summary: clean(todoContainer.innerText || '').slice(0, 500),
        items: cards,
      };
    }

    const main = Array.from(document.querySelectorAll('div')).find((el) => {
      const text = clean(el.innerText || '');
      return text.includes('共 ') && text.includes('条笔记');
    });

    const cards = Array.from(document.querySelectorAll('[role="button"], li, article, .list-item, .note-item'))
      .map((el) => ({
        text: clean(el.innerText || ''),
        className: typeof el.className === 'string' ? el.className : '',
      }))
      .filter((item) => item.text)
      .slice(0, 100);

    return {
      summary: main ? clean(main.innerText || '') : '',
      items: cards,
    };
    """
    result = driver.execute_script(script)
    return result


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    driver = build_driver()
    try:
        driver.get(TARGET_URL)
        wait_for_app(driver)
        time.sleep(2)

        click_sidebar_item(driver, "未完成")
        time.sleep(1)
        pending = read_visible_items(driver)

        click_sidebar_item(driver, "已完成")
        time.sleep(1)
        completed = read_visible_items(driver)

        state = {
            "title": driver.title,
            "url": driver.current_url,
            "pending": pending,
            "completed": completed,
        }

        print(json.dumps(state, ensure_ascii=False, indent=2))
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
