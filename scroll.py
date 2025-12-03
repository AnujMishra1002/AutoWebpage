#!/usr/bin/env python3

import time
import random
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException


# ============================================================
#                   MAC UPDATER CLASS
# ============================================================

class MacUpdater:
    def __init__(self):
        pass

    def random_mac(self):
        """Generate a random MAC address (locally administered, unicast)."""
        mac = [
            0xdc, 0xa6, 0x32,
            random.randint(0x00, 0x7f),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff)
        ]
        return ':'.join(f"{x:02x}" for x in mac)

    def change_mac(self, interface, new_mac):
        """Change the MAC address of the given interface."""
        try:
            subprocess.run(["sudo", "ip", "link", "set", interface, "down"], check=True)
            subprocess.run(["sudo", "ip", "link", "set", interface, "address", new_mac], check=True)
            subprocess.run(["sudo", "ip", "link", "set", interface, "up"], check=True)
            print(f"[+] Changed {interface} MAC to {new_mac}")
        except subprocess.CalledProcessError as e:
            print(f"[!] Failed to change MAC: {e}")

    def get_current_mac(self, interface):
        result = subprocess.run(
            ["cat", f"/sys/class/net/{interface}/address"],
            capture_output=True, text=True
        )
        return result.stdout.strip()

    def get_ip_address(self, interface):
        try:
            result = subprocess.run(
                ["ip", "-4", "addr", "show", interface],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.splitlines():
                if "inet " in line:
                    return line.split()[1].split("/")[0]
            return "No IP assigned"
        except subprocess.CalledProcessError:
            return "Error retrieving IP"



# ============================================================
#                VISITOR SIMULATOR CLASS
# ============================================================

class VisitorSimulator:
    def __init__(self):
        # Add proxies here if needed
        self.proxies = []

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148",
        ]

    def create_driver(self):
        options = Options()

        # Required for Raspberry Pi Chromium
        options.binary_location = "/usr/bin/chromium-browser"
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Random user-agent
        ua = random.choice(self.user_agents)
        options.add_argument(f"user-agent={ua}")
        print(f"[INFO] User-Agent: {ua}")

        # Proxy (optional)
        if self.proxies:
            proxy = random.choice(self.proxies)
            options.add_argument(f"--proxy-server={proxy}")
            print(f"[INFO] Proxy used: {proxy}")
        else:
            print("[INFO] No proxy used")

        driver = webdriver.Chrome(options=options)
        return driver

    def simulate_browsing(self, url):
        driver = self.create_driver()

        try:
            print(f"[INFO] Opening: {url}")
            driver.get(url)
            time.sleep(random.uniform(3, 5))

            # Random scrolling
            for _ in range(3):
                scroll_point = random.randint(200, 1500)
                driver.execute_script(f"window.scrollTo(0, {scroll_point});")
                time.sleep(random.uniform(2, 4))

            # Click random link
            links = driver.find_elements(By.TAG_NAME, "a")
            valid_links = [a for a in links if a.get_attribute("href") and a.get_attribute("href").startswith("http")]

            if valid_links:
                link = random.choice(valid_links)
                print(f"[INFO] Clicking: {link.get_attribute('href')}")
                try:
                    link.click()
                    time.sleep(random.uniform(3, 5))
                except WebDriverException:
                    print("[WARN] Failed to click link")

        except Exception as e:
            print(f"[ERROR] Browsing error: {e}")

        finally:
            driver.quit()
            print("[INFO] Browser closed")



# ============================================================
#                     MAIN LOOP
# ============================================================

if __name__ == "__main__":
    interface = "wlan0"
    MU = MacUpdater()
    simulator = VisitorSimulator()
    url = "https://aajkijanta.com"

    while True:
        # Change MAC
        new_mac = MU.random_mac()
        MU.change_mac(interface, new_mac)

        current_mac = MU.get_current_mac(interface)
        ip = MU.get_ip_address(interface)

        print(f"[*] MAC Now: {current_mac}")
        print(f"[*] IP Now:  {ip}")
        print("-" * 50)

        # Simulate real visitor
        simulator.simulate_browsing(url)

        # Sleep 2–5 minutes
        wait = random.uniform(120, 300)
        print(f"[INFO] Waiting {wait:.2f} seconds...\n")
        time.sleep(wait)
