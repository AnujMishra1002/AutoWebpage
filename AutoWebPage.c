#!/usr/bin/env python3

import time
import random
import subprocess
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException


class macUpdater:
    def __init__(self):
        pass

    def random_mac(self):
        mac = [0xdc, 0xa6, 0x32,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
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
        result = subprocess.run(["cat", f"/sys/class/net/{interface}/address"],
                                capture_output=True, text=True)
        return result.stdout.strip()

    def get_ip_address(self, interface):
        try:
            result = subprocess.run(["ip", "-4", "addr", "show", interface],
                                    capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if "inet " in line:
                    return line.split()[1].split("/")[0]
            return "No IP assigned"
        except:
            return "Error retrieving IP"


class VisitorSimulator:
    def __init__(self):
        self.proxies = []
        self.user_agents = [
            "Mozilla/5.0 (X11; Ubuntu; Linux armv7l; rv:102.0) Gecko/20100101 Firefox/102.0",
            "Mozilla/5.0 (Linux; arm; rv:91.0) Gecko/91.0 Firefox/91.0",
        ]

    def create_driver(self):
        options = Options()
        options.set_preference("general.useragent.override", random.choice(self.user_agents))

        driver = webdriver.Firefox(options=options)
        driver.set_window_size(1280, 720)
        return driver

    def simulate_browsing(self, URL):
        driver = self.create_driver()
        try:
            driver.get(URL)
            time.sleep(random.uniform(3, 6))

            action = ActionChains(driver)
            action.move_by_offset(200, 200).perform()
            time.sleep(2)

            # Scroll
            for _ in range(5):
                driver.execute_script("window.scrollBy(0, 400);")
                time.sleep(random.uniform(2, 4))

            # Try clicking one link
            links = driver.find_elements(By.TAG_NAME, "a")
            if links:
                link = random.choice(links)
                href = link.get_attribute("href")
                if href:
                    link.click()
                    time.sleep(5)

        except Exception as e:
            print(f"[ERROR] {e}")

        finally:
            driver.quit()
            print("[INFO] Closed Firefox")


if __name__ == "__main__":
    interface = "wlan0"
    MU = macUpdater()
    simulator = VisitorSimulator()
    url = "https://aajkijanta.com"

    while True:
        new_mac = MU.random_mac()
        MU.change_mac(interface, new_mac)

        print(f"[*] MAC: {MU.get_current_mac(interface)}")
        print(f"[*] IP : {MU.get_ip_address(interface)}")

        simulator.simulate_browsing(url)

        delay = random.uniform(120, 300)
        print(f"[INFO] Waiting {delay:.1f} seconds...\n")
        time.sleep(delay)
