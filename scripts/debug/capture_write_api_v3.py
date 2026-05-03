"""Capture write API using Selenium's performance logging capability.

Selenium can capture DevTools performance logs which include Network events.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


def main():
    print("Starting Chrome with performance logging...")

    service = Service(str("E:/Code/TEMScript/MiNote/bin/chromedriver.exe"))
    options = Options()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    options.add_argument("--user-data-dir=E:/Code/TEMScript/MiNote/chrome_profile")
    options.add_argument("--profile-directory=Default")

    # Enable performance logging to capture Network events
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://i.mi.com/note/#/")

    # Wait for page
    driver.execute_async_script("""
        var cb = arguments[arguments.length - 1];
        var check = setInterval(function() {
            if (document.querySelector('#folderList')) { clearInterval(check); cb('ok'); }
        }, 500);
        setTimeout(function() { clearInterval(check); cb('timeout'); }, 30000);
    """)
    print("Page loaded")

    def get_todo_posts():
        """Extract POST requests to todo API from performance logs."""
        logs = driver.get_log("performance")
        posts = []
        for entry in logs:
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
                            "requestId": msg.get("params", {}).get("requestId", ""),
                        })
            except:
                pass
        return posts

    # Navigate to pending todos
    driver.execute_script("""
        var items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
        var pending = items.find(el => (el.innerText||'').trim().includes('未完成'));
        if (pending) pending.click();
    """)
    time.sleep(2)

    # Clear initial logs
    _ = driver.get_log("performance")

    # === CREATE ===
    print("\n" + "=" * 60)
    print("=== 1. CREATE ===")
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
        print("  No empty input!")
        driver.quit()
        return

    driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].focus();", target)
    target.send_keys(Keys.CONTROL, "a")
    target.send_keys("__SEL_CREATE__")
    target.send_keys(Keys.TAB)
    time.sleep(3)
    print("  Created '__SEL_CREATE__'")

    posts = get_todo_posts()
    print(f"  Captured {len(posts)} POST requests:")
    for p in posts:
        body = urllib.parse.unquote(p.get("postData", ""))
        print(f"  URL: {p['url']}")
        print(f"  Body (decoded): {body[:3000]}")
        # Parse the body
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

    # === UPDATE ===
    print("\n" + "=" * 60)
    print("=== 2. UPDATE ===")
    print("=" * 60)

    driver.execute_script("""
        var items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
        var pending = items.find(el => (el.innerText||'').trim().includes('未完成'));
        if (pending) pending.click();
    """)
    time.sleep(2)

    inputs = driver.find_elements(By.CSS_SELECTOR, ".item-3HTE8 input.text-field-2euJG")
    for el in inputs:
        if (el.get_attribute("value") or "").strip() == "__SEL_CREATE__":
            el.click()
            el.send_keys(Keys.CONTROL, "a")
            el.send_keys("__SEL_UPDATED__")
            el.send_keys(Keys.TAB)
            time.sleep(3)
            print("  Updated to '__SEL_UPDATED__'")
            break

    posts = get_todo_posts()
    print(f"  Captured {len(posts)} POST requests:")
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

    # === COMPLETE ===
    print("\n" + "=" * 60)
    print("=== 3. COMPLETE ===")
    print("=" * 60)

    driver.execute_script("""
        var items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
        var pending = items.find(el => (el.innerText||'').trim().includes('未完成'));
        if (pending) pending.click();
    """)
    time.sleep(2)

    driver.execute_script("""
        var inputs = Array.from(document.querySelectorAll('.item-3HTE8 input.text-field-2euJG'));
        var match = inputs.find(el => (el.value||'').trim() === '__SEL_UPDATED__');
        if (match) {
            var root = match.closest('.item-3HTE8');
            var cb = root.querySelector("button[data-name='checkbox-main']");
            if (cb) cb.click();
        }
    """)
    time.sleep(3)
    print("  Completed")

    posts = get_todo_posts()
    print(f"  Captured {len(posts)} POST requests:")
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

    # === DELETE ===
    print("\n" + "=" * 60)
    print("=== 4. DELETE ===")
    print("=" * 60)

    driver.execute_script("""
        var items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
        var completed = items.find(el => (el.innerText||'').trim().includes('已完成'));
        if (completed) completed.click();
    """)
    time.sleep(2)

    found = driver.execute_script("""
        var inputs = Array.from(document.querySelectorAll('.item-3HTE8 input.text-field-2euJG'));
        var match = inputs.find(el => (el.value||'').trim() === '__SEL_UPDATED__');
        if (match) { match.scrollIntoView({block:'center'}); return true; }
        return false;
    """)

    if found:
        inputs = driver.find_elements(By.CSS_SELECTOR, ".item-3HTE8 input.text-field-2euJG")
        for el in inputs:
            if (el.get_attribute("value") or "").strip() == "__SEL_UPDATED__":
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

    posts = get_todo_posts()
    print(f"  Captured {len(posts)} POST requests:")
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

    print("\n" + "=" * 60)
    print("CRUD capture complete")
    print("=" * 60)

    driver.quit()


if __name__ == "__main__":
    main()
