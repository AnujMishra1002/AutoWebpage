#!/usr/bin/env python3

import time
import random
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException

class macUpdater:
    def __init__(self):      # FIXED
        pass
    
    def random_mac(self):
        mac = [
            0xdc, 0xa6, 0x32,
            random.randint(0x00, 0x7f),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff),
        ]
        return ':'.join(f"{x:02x}" for x in mac)
    
    def change_mac(self, interface, new_mac):
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


class VisitorSimulator:
    def __init__(self):      # FIXED
        self.proxies = []
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        ]
    
    def create_driver(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        user_agent = random.choice(self.user_agents)
        options.add_argument(f"user-agent={user_agent}")

        if self.proxies:
            proxy = random.choice(self.proxies)
            options.add_argument(f"--proxy-server={proxy}")
            print(f"[INFO] Using proxy: {proxy}")
        else:
            print("[INFO] No proxy used")

        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1280, 720)
        return driver
    
    def simulate_browsing(self, URL):
        driver = self.create_driver()

        try:
            driver.get(URL)
            print(f"[INFO] Opened URL: {URL}")
            time.sleep(random.uniform(3, 6))
            
            scroll_points = [
                random.randint(200, 600),
                random.randint(600, 1200),
                random.randint(1200, 1800),
            ]
            for sp in scroll_points:
                driver.execute_script(f"window.scrollTo(0, {sp});")
                time.sleep(random.uniform(2, 4))
            
            links = driver.find_elements(By.TAG_NAME, 'a')
            links = [a for a in links if a.get_attribute("href")]
            
            if links:
                link = random.choice(links)
                try:
                    print("[INFO] Clicking:", link.get_attribute("href"))
                    link.click()
                    time.sleep(random.uniform(5, 10))
                except WebDriverException:
                    print("[WARN] Failed to click link")
            else:
                print("[INFO] No clickable links found")

        except Exception as e:
            print("[ERROR] Browsing:", e)

        finally:
            driver.quit()
            print("[INFO] Browser closed")


# -------------------------------------------------------------
# FIXED MAIN CONDITION
# -------------------------------------------------------------
if __name__ == "__main__":     # FIXED
    interface = "wlan0"
    MU = macUpdater()
    simulator = VisitorSimulator()
    url = "https://aajkijanta.com"
    
    while True:
        new_mac = MU.random_mac()
        MU.change_mac(interface, new_mac)

        current_mac = MU.get_current_mac(interface)
        ip = MU.get_ip_address(interface)

        print(f"[*] MAC: {current_mac}")
        print(f"[*] IP: {ip}")
        print("-" * 50)

        simulator.simulate_browsing(url)
        
        delay = random.uniform(120, 300)
        print(f"[INFO] Sleeping {delay:.2f} sec...")
        time.sleep(delay)

