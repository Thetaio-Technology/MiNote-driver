from __future__ import annotations

import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from ._types import (
    SECTION_ALL_NOTES,
    SECTION_UNCATEGORIZED,
    SECTION_COMPLETED,
    SECTION_PENDING,
    SECTION_RECYCLE_BIN,
    SUPPORTED_SEARCH_SECTIONS,
    TodoItem,
)
from .config import CHROMEDRIVER_EXE, CHROME_EXE, CHROME_USER_DATA_DIR, TARGET_URL


class MiNoteClient:
    def __init__(self, *, headless: bool = True) -> None:
        self._headless = headless
        self.driver: webdriver.Chrome | None = None

    def __enter__(self) -> "MiNoteClient":
        self.driver = self._build_driver()
        self.driver.get(TARGET_URL)
        self._wait_for_app()
        time.sleep(1)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    def _build_driver(self) -> webdriver.Chrome:
        service = Service(str(CHROMEDRIVER_EXE))
        options = Options()
        options.binary_location = str(CHROME_EXE)
        options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
        options.add_argument("--profile-directory=Default")
        if self._headless:
            options.add_argument("--headless=new")
        return webdriver.Chrome(service=service, options=options)

    def _require_driver(self) -> webdriver.Chrome:
        if self.driver is None:
            raise RuntimeError("MiNoteClient is not started. Use it as a context manager.")
        return self.driver

    def _wait_for_app(self) -> None:
        driver = self._require_driver()
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return !!document.querySelector('#folderList')")
        )

    def open_section(self, section: str) -> None:
        driver = self._require_driver()
        script = r"""
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
        if not driver.execute_script(script, section):
            raise RuntimeError(f"Sidebar item not found: {section}")
        time.sleep(1)

    def list_sidebar_items(self) -> list[str]:
        driver = self._require_driver()
        return driver.execute_script(
            r"""
            const clean = (value) => (value || '').replace(/\s+/g, ' ').trim();
            return Array.from(document.querySelectorAll('#folderList [role="button"]'))
              .map((el) => clean(el.querySelector('.text-10cyJ')?.getAttribute('title') || el.innerText || ''))
              .filter(Boolean);
            """
        )

    def get_search_placeholder(self) -> str | None:
        driver = self._require_driver()
        placeholders = driver.execute_script(
            r"""
            return Array.from(document.querySelectorAll('input'))
              .filter((el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length))
              .map((el) => el.getAttribute('placeholder') || '')
              .filter(Boolean);
            """
        )
        return placeholders[0] if placeholders else None

    def search(self, section: str, keyword: str) -> dict:
        if section not in SUPPORTED_SEARCH_SECTIONS:
            raise ValueError(f"Search is not supported for section: {section}")

        self.open_section(section)
        driver = self._require_driver()
        search_input = self._find_search_input()
        if search_input is None:
            raise RuntimeError(f"Search input not found for section: {section}")

        driver.execute_script(
            """
            const input = arguments[0];
            const value = arguments[1];
            input.scrollIntoView({ block: 'center' });
            input.focus();
            input.value = '';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.value = value;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            """,
            search_input,
            keyword,
        )
        time.sleep(1)

        if section in {SECTION_PENDING, SECTION_COMPLETED}:
            items = [item.__dict__ for item in self.read_todos(section)]
        else:
            items = self._read_note_list_items()

        return {
            "section": section,
            "keyword": keyword,
            "placeholder": search_input.get_attribute("placeholder") or "",
            "items": items,
        }

    def read_todos(self, section: str) -> list[TodoItem]:
        if section not in {SECTION_PENDING, SECTION_COMPLETED}:
            raise ValueError(f"Todo reading only supports pending/completed sections, got: {section}")

        self.open_section(section)
        driver = self._require_driver()
        items = driver.execute_script(
            r"""
            const clean = (value) => (value || '').replace(/\s+/g, ' ').trim();
            const todoContainer = document.querySelector('.main-group-3qygk.todo-page-2xEZZ.item-list-2UYnn');
            if (!todoContainer) return [];
            return Array.from(todoContainer.querySelectorAll('.item-3HTE8')).map((el) => {
              const titleInput = el.querySelector('input.text-field-2euJG');
              return {
                title: clean(titleInput ? titleInput.value : ''),
                counter: clean(el.querySelector('.finished-counter-3CDy8')?.innerText || ''),
                remind: clean(el.querySelector('.set-remind-KMc61')?.innerText || ''),
                status: el.className.includes('finished-3B8zm') ? 'completed' : 'pending',
              };
            }).filter((item) => item.title);
            """
        )
        return [TodoItem(**item) for item in items]

    def update_todo_title(self, old_title: str, new_title: str, *, section: str = SECTION_PENDING) -> bool:
        if section not in {SECTION_PENDING, SECTION_COMPLETED}:
            raise ValueError(f"Todo updates only support pending/completed sections, got: {section}")

        self.open_section(section)
        todo_input = self._find_todo_input_by_title(old_title)
        if todo_input is None:
            return False

        todo_input.click()
        todo_input.send_keys(Keys.CONTROL, "a")
        todo_input.send_keys(new_title)
        todo_input.send_keys(Keys.TAB)
        time.sleep(1)
        return new_title in [item.title for item in self.read_todos(section)]

    def create_todo(self, title: str, *, section: str = SECTION_PENDING) -> bool:
        if section not in {SECTION_PENDING, SECTION_COMPLETED}:
            raise ValueError(f"Todo creation only supports pending/completed sections, got: {section}")

        self.open_section(section)
        driver = self._require_driver()
        before_titles = [item.title for item in self.read_todos(section)]
        driver.execute_script(
            """
            const button = document.querySelector('.main-group-3qygk.todo-page-2xEZZ.item-list-2UYnn .btn-add-1bJh_');
            if (button) button.click();
            """
        )
        time.sleep(1)

        inputs = driver.find_elements(By.CSS_SELECTOR, ".main-group-3qygk.todo-page-2xEZZ.item-list-2UYnn .item-3HTE8 input.text-field-2euJG")
        target = None
        for element in inputs:
            value = (element.get_attribute("value") or "").strip()
            placeholder = (element.get_attribute("placeholder") or "").strip()
            if not value or placeholder == "请输入待办标题":
                target = element
                break

        if target is None:
            return False

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].focus();", target)
        target.send_keys(Keys.CONTROL, "a")
        target.send_keys(title)
        target.send_keys(Keys.TAB)
        time.sleep(1)
        after_titles = [item.title for item in self.read_todos(section)]
        return title in after_titles and len(after_titles) >= len(before_titles)

    def complete_todo(self, title: str) -> bool:
        return self._toggle_todo_status(title, from_section=SECTION_PENDING, to_section=SECTION_COMPLETED)

    def restore_todo(self, title: str) -> bool:
        return self._toggle_todo_status(title, from_section=SECTION_COMPLETED, to_section=SECTION_PENDING)

    def delete_todo(self, title: str, *, section: str = SECTION_PENDING) -> bool:
        if section not in {SECTION_PENDING, SECTION_COMPLETED}:
            raise ValueError(f"Todo deletion only supports pending/completed sections, got: {section}")

        self.open_section(section)
        driver = self._require_driver()
        todo_input = self._find_todo_input_by_title(title)
        if todo_input is None:
            return False

        root = todo_input.find_element(By.XPATH, "./ancestor::div[contains(@class,'item-3HTE8')]")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", root)
        ActionChains(driver).context_click(root).perform()
        time.sleep(1)

        deleted = driver.execute_script(
            """
            const menuItem = Array.from(document.querySelectorAll('.ant-dropdown [role="menuitem"], [role="menuitem"], .miui-dropdown-menu-item, li'))
              .find((el) => (el.innerText || '').trim().includes('删除'));
            if (!menuItem) return false;
            menuItem.click();
            return true;
            """
        )
        if not deleted:
            return False

        time.sleep(1)
        confirmed = driver.execute_script(
            """
            const buttons = Array.from(document.querySelectorAll('.miui-modal .miui-btn, .miui-modal button, [role="dialog"] button'));
            const confirm = buttons.find((el) => (el.innerText || '').trim() === '删除' || (el.className || '').includes('miui-btn-danger'));
            if (!confirm) return false;
            confirm.click();
            return true;
            """
        )
        if not confirmed:
            return False

        time.sleep(1)
        remaining = [item.title for item in self.read_todos(section)]
        return title not in remaining

    def _find_search_input(self):
        driver = self._require_driver()
        inputs = driver.find_elements(By.CSS_SELECTOR, "input")
        for element in inputs:
            placeholder = (element.get_attribute("placeholder") or "").strip()
            if placeholder.startswith("搜索"):
                return element
        return None

    def _find_todo_input_by_title(self, title: str):
        driver = self._require_driver()
        script = r"""
        const wanted = arguments[0];
        const clean = (value) => (value || '').trim();
        const items = Array.from(document.querySelectorAll('.main-group-3qygk.todo-page-2xEZZ.item-list-2UYnn .item-3HTE8'));
        const match = items.find((el) => {
          const input = el.querySelector('input.text-field-2euJG');
          return clean(input ? input.value : '') === wanted;
        });
        if (!match) return false;
        match.scrollIntoView({ block: 'center' });
        return true;
        """
        found = driver.execute_script(script, title)
        if not found:
            return None

        for element in driver.find_elements(By.CSS_SELECTOR, ".main-group-3qygk.todo-page-2xEZZ.item-list-2UYnn .item-3HTE8 input.text-field-2euJG"):
            if (element.get_attribute("value") or "").strip() == title:
                return element
        return None

    def _toggle_todo_status(self, title: str, *, from_section: str, to_section: str) -> bool:
        self.open_section(from_section)
        driver = self._require_driver()
        todo_input = self._find_todo_input_by_title(title)
        if todo_input is None:
            return False

        root = todo_input.find_element(By.XPATH, "./ancestor::div[contains(@class,'item-3HTE8')]")
        checkbox = root.find_element(By.CSS_SELECTOR, "button[data-name='checkbox-main']")
        driver.execute_script("arguments[0].click();", checkbox)
        time.sleep(1)

        source_titles = [item.title for item in self.read_todos(from_section)]
        target_titles = [item.title for item in self.read_todos(to_section)]
        return title not in source_titles and title in target_titles

    def _read_note_list_items(self) -> list[dict]:
        driver = self._require_driver()
        return driver.execute_script(
            r"""
            const clean = (value) => (value || '').replace(/\s+/g, ' ').trim();
            const containers = Array.from(document.querySelectorAll('div'));
            const listContainer = containers.find((el) => {
              const text = clean(el.innerText || '');
              return text.includes('共 ') && text.includes('条笔记');
            });

            if (!listContainer) {
              return [];
            }

            const items = Array.from(listContainer.querySelectorAll('[role="button"], li, article, div'))
              .map((el) => clean(el.innerText || ''))
              .filter(Boolean)
              .filter((text) => !['按编辑时间', '新建笔记'].includes(text))
              .slice(0, 80);

            return Array.from(new Set(items)).map((text) => ({ text }));
            """
        )
