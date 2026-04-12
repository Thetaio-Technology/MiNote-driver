from pathlib import Path
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait


PROJECT_ROOT = Path(__file__).resolve().parent
CHROMEDRIVER_EXE = PROJECT_ROOT / "bin" / "chromedriver.exe"
CHROME_EXE = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
CHROME_USER_DATA_DIR = PROJECT_ROOT / "chrome_profile"
TARGET_URL = "https://i.mi.com/note/#/"
OLD_TITLE = "test"
NEW_TITLE = "明天中午11点和欢欢宝贝喝咖啡"


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
    const items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
    const item = items.find((el) => (el.innerText || '').trim() === label);
    if (!item) return false;
    item.click();
    return true;
    """
    if not driver.execute_script(script, label):
        raise RuntimeError(f"Sidebar item not found: {label}")


def find_todo_input(driver: webdriver.Chrome, title: str):
    script = """
    const wanted = arguments[0];
    const clean = (value) => (value || '').trim();
    const items = Array.from(document.querySelectorAll('.main-group-3qygk.todo-page-2xEZZ.item-list-2UYnn .item-3HTE8'));
    const match = items.find((el) => {
      const input = el.querySelector('input.text-field-2euJG');
      return clean(input ? input.value : '') === wanted;
    });
    if (!match) return null;
    const input = match.querySelector('input.text-field-2euJG');
    if (!input) return null;
    input.scrollIntoView({ block: 'center' });
    return true;
    """
    found = driver.execute_script(script, title)
    if not found:
        return None

    for element in driver.find_elements(By.CSS_SELECTOR, ".main-group-3qygk.todo-page-2xEZZ.item-list-2UYnn .item-3HTE8 input.text-field-2euJG"):
        if element.get_attribute("value").strip() == title:
            return element
    return None


def read_titles(driver: webdriver.Chrome) -> list[str]:
    return driver.execute_script(
        """
        return Array.from(document.querySelectorAll('.main-group-3qygk.todo-page-2xEZZ.item-list-2UYnn .item-3HTE8 input.text-field-2euJG'))
          .map((el) => (el.value || '').trim())
          .filter(Boolean);
        """
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    driver = build_driver()
    try:
        driver.get(TARGET_URL)
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return !!document.querySelector('#folderList')")
        )
        time.sleep(2)
        click_sidebar_item(driver, "未完成")
        time.sleep(1)

        todo_input = find_todo_input(driver, OLD_TITLE)
        if todo_input is None:
            raise RuntimeError(f"Pending todo not found: {OLD_TITLE}")

        todo_input.click()
        todo_input.send_keys(Keys.CONTROL, "a")
        todo_input.send_keys(NEW_TITLE)
        todo_input.send_keys(Keys.TAB)
        time.sleep(2)

        titles = read_titles(driver)
        result = {
            "updated": NEW_TITLE in titles,
            "old_title_present": OLD_TITLE in titles,
            "new_title_present": NEW_TITLE in titles,
            "titles": titles,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
