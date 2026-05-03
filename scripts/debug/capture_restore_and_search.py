"""Capture restore (uncomplete) and search API requests via Selenium performance logging."""
from __future__ import annotations

import json
import time
import urllib.parse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def get_todo_posts(driver):
    posts = []
    for entry in driver.get_log("performance"):
        try:
            log = json.loads(entry["message"])
            msg = log.get("message", {})
            method = msg.get("method", "")
            if method == "Network.requestWillBeSent":
                req = msg.get("params", {}).get("request", {})
                url = req.get("url", "")
                req_method = req.get("method", "")
                if req_method == "POST" and "todo" in url:
                    posts.append({
                        "url": url,
                        "method": req_method,
                        "postData": req.get("postData", ""),
                    })
        except Exception:
            pass
    return posts


def print_posts(posts, label=""):
    print(f"\n  [{label}] Captured {len(posts)} POST requests:")
    for p in posts:
        body = urllib.parse.unquote(p.get("postData", ""))
        print(f"  URL: {p['url']}")
        print(f"  Body (decoded): {body[:3000]}")
        try:
            params = urllib.parse.parse_qs(p.get("postData", ""))
            for key, values in params.items():
                val = values[0]
                if key == "record":
                    record = json.loads(val)
                    print(f"  record (parsed):")
                    print(json.dumps(record, indent=2, ensure_ascii=False)[:3000])
                elif key == "serviceToken":
                    print(f"  serviceToken: {val[:30]}...")
                else:
                    print(f"  {key}: {val}")
        except Exception as e:
            print(f"  Parse error: {e}")


def main():
    print("Starting Chrome with performance logging...")

    service = Service(str("E:/Code/TEMScript/MiNote/bin/chromedriver.exe"))
    options = Options()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    options.add_argument("--user-data-dir=E:/Code/TEMScript/MiNote/chrome_profile")
    options.add_argument("--profile-directory=Default")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://i.mi.com/note/#/")

    # Wait for page load
    driver.execute_async_script("""
        var cb = arguments[arguments.length - 1];
        var check = setInterval(function() {
            if (document.querySelector('#folderList')) { clearInterval(check); cb('ok'); }
        }, 500);
        setTimeout(function() { clearInterval(check); cb('timeout'); }, 30000);
    """)
    print("Page loaded")

    # Navigate to pending section
    driver.execute_script("""
        var items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
        var pending = items.find(el => (el.innerText||'').trim().includes('未完成'));
        if (pending) pending.click();
    """)
    time.sleep(2)

    # === STEP 1: Create a test todo, then complete it ===
    print("\n" + "=" * 60)
    print("=== SETUP: Create test item ===")
    print("=" * 60)

    driver.execute_script("""
        const btn = document.querySelector('.btn-add-1bJh_');
        if (btn) btn.click();
    """)
    time.sleep(0.5)

    inputs = driver.find_elements(By.CSS_SELECTOR, ".item-3HTE8 input.text-field-2euJG")
    target = None
    for el in inputs:
        val = (el.get_attribute("value") or "").strip()
        ph = (el.get_attribute("placeholder") or "").strip()
        if not val or ph == "请输入待办标题":
            target = el
            break

    if not target:
        print("  No empty input! Trying to find existing test item...")
        # Try to find an existing test item
        for el in inputs:
            val = (el.get_attribute("value") or "").strip()
            if val.startswith("__RESTORE_TEST__"):
                target = el
                break

    if not target:
        print("  ERROR: Cannot find or create test item. Aborting.")
        driver.quit()
        return

    driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].focus();", target)
    target.send_keys(Keys.CONTROL, "a")
    target.send_keys("__RESTORE_TEST__")
    target.send_keys(Keys.TAB)
    time.sleep(3)
    print("  Created '__RESTORE_TEST__'")

    # Clear logs
    _ = driver.get_log("performance")

    # Complete it
    print("\n" + "=" * 60)
    print("=== SETUP: Complete the test item ===")
    print("=" * 60)

    driver.execute_script("""
        var items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
        var pending = items.find(el => (el.innerText||'').trim().includes('未完成'));
        if (pending) pending.click();
    """)
    time.sleep(2)

    driver.execute_script("""
        var inputs = Array.from(document.querySelectorAll('.item-3HTE8 input.text-field-2euJG'));
        var match = inputs.find(el => (el.value||'').trim() === '__RESTORE_TEST__');
        if (match) {
            var root = match.closest('.item-3HTE8');
            var cb = root.querySelector("button[data-name='checkbox-main']");
            if (cb) cb.click();
        }
    """)
    time.sleep(3)
    print("  Completed '__RESTORE_TEST__'")

    # Clear logs
    _ = driver.get_log("performance")

    # === STEP 2: RESTORE (uncomplete) ===
    print("\n" + "=" * 60)
    print("=== CAPTURE: RESTORE (uncomplete) ===")
    print("=" * 60)

    driver.execute_script("""
        var items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
        var completed = items.find(el => (el.innerText||'').trim().includes('已完成'));
        if (completed) completed.click();
    """)
    time.sleep(2)

    # Find and click checkbox on completed item (this restores it)
    driver.execute_script("""
        var inputs = Array.from(document.querySelectorAll('.item-3HTE8 input.text-field-2euJG'));
        var match = inputs.find(el => (el.value||'').trim() === '__RESTORE_TEST__');
        if (match) {
            match.scrollIntoView({block:'center'});
            var root = match.closest('.item-3HTE8');
            var cb = root.querySelector("button[data-name='checkbox-main']");
            if (cb) cb.click();
        }
    """)
    time.sleep(3)
    print("  Restored (clicked checkbox in completed section)")

    posts = get_todo_posts(driver)
    print_posts(posts, "RESTORE")

    # Verify it's back in pending
    driver.execute_script("""
        var items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
        var pending = items.find(el => (el.innerText||'').trim().includes('未完成'));
        if (pending) pending.click();
    """)
    time.sleep(2)
    found = driver.execute_script("""
        var inputs = Array.from(document.querySelectorAll('.item-3HTE8 input.text-field-2euJG'));
        return inputs.some(el => (el.value||'').trim() === '__RESTORE_TEST__');
    """)
    print(f"  Item back in pending: {found}")

    # Clear logs
    _ = driver.get_log("performance")

    # === STEP 3: SEARCH ===
    print("\n" + "=" * 60)
    print("=== CAPTURE: SEARCH ===")
    print("=" * 60)

    # First, navigate to pending section for search context
    driver.execute_script("""
        var items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
        var pending = items.find(el => (el.innerText||'').trim().includes('未完成'));
        if (pending) pending.click();
    """)
    time.sleep(2)

    # Find search input and type a search query
    driver.execute_script("""
        var inputs = Array.from(document.querySelectorAll('input'));
        var searchInput = inputs.find(el => (el.getAttribute('placeholder')||'').startsWith('搜索'));
        if (searchInput) {
            searchInput.focus();
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input', {bubbles: true}));
            searchInput.value = '__RESTORE_TEST__';
            searchInput.dispatchEvent(new Event('input', {bubbles: true}));
            searchInput.dispatchEvent(new Event('change', {bubbles: true}));
        }
    """)
    time.sleep(3)
    print("  Typed search query '__RESTORE_TEST__'")

    posts = get_todo_posts(driver)
    print_posts(posts, "SEARCH")

    # Also capture GET requests during search
    get_posts = []
    for entry in driver.get_log("performance"):
        try:
            log = json.loads(entry["message"])
            msg = log.get("message", {})
            method = msg.get("method", "")
            if method == "Network.requestWillBeSent":
                req = msg.get("params", {}).get("request", {})
                url = req.get("url", "")
                req_method = req.get("method", "")
                if req_method == "GET" and "todo" in url:
                    get_posts.append({"url": url, "method": req_method})
        except Exception:
            pass

    print(f"\n  [SEARCH GET] Captured {len(get_posts)} GET requests:")
    for p in get_posts:
        print(f"  URL: {p['url']}")

    # Clear logs
    _ = driver.get_log("performance")

    # === CLEANUP: Delete test item ===
    print("\n" + "=" * 60)
    print("=== CLEANUP: Delete test item ===")
    print("=" * 60)

    # Clear search first
    driver.execute_script("""
        var inputs = Array.from(document.querySelectorAll('input'));
        var searchInput = inputs.find(el => (el.getAttribute('placeholder')||'').startsWith('搜索'));
        if (searchInput) {
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input', {bubbles: true}));
        }
    """)
    time.sleep(1)

    driver.execute_script("""
        var items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
        var pending = items.find(el => (el.innerText||'').trim().includes('未完成'));
        if (pending) pending.click();
    """)
    time.sleep(2)

    # Delete using context menu
    from selenium.webdriver.common.action_chains import ActionChains
    inputs = driver.find_elements(By.CSS_SELECTOR, ".item-3HTE8 input.text-field-2euJG")
    for el in inputs:
        if (el.get_attribute("value") or "").strip() == "__RESTORE_TEST__":
            root = el.find_element(By.XPATH, "./ancestor::div[contains(@class,'item-3HTE8')]")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", root)
            ActionChains(driver).context_click(root).perform()
            time.sleep(1)
            driver.execute_script("""
                const menuItem = Array.from(document.querySelectorAll('[role="menuitem"], .ant-dropdown-menu-item, li'))
                    .find(el => (el.innerText||'').trim().includes('删除'));
                if (menuItem) menuItem.click();
            """)
            time.sleep(1)
            driver.execute_script("""
                const buttons = Array.from(document.querySelectorAll('[role="dialog"] button, .miui-modal button'));
                const confirm = buttons.find(el => (el.innerText||'').trim() === '删除');
                if (confirm) confirm.click();
            """)
            time.sleep(2)
            print("  Deleted")
            break

    print("\n" + "=" * 60)
    print("Capture complete")
    print("=" * 60)

    driver.quit()


if __name__ == "__main__":
    main()
