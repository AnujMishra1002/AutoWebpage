#!/usr/bin/env python3
import os
import time
import random
import subprocess
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

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
        except:
            print("[!] MAC change failed")

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
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if "inet " in line:
                    return line.split()[1].split("/")[0]
        except:
            pass
        return "No IP"

    def webpage_viewer(self, URL):
        options = Options()
        options.set_preference("general.useragent.override",
                               "Mozilla/5.0 (X11; Linux armv7l) Gecko/20100101 Firefox/102.0")

        driver = webdriver.Firefox(options=options)

        try:
            driver.set_window_size(1280, 720)
            driver.get(URL)
            time.sleep(5)

            home_xpath = '/html/body/div[1]/header/div/h1/a'

            post_list = [
                '/html/body/div[1]/main/div[1]/div[2]/div[1]/div/ul/li/div/h2/a',
                '/html/body/div[1]/main/div[1]/div[2]/div[2]/div/ul/li[1]/div/h2/a',
                '/html/body/div[1]/main/div[1]/div[2]/div[2]/div/ul/li[2]/div/h2/a',
                '/html/body/div[1]/main/div[1]/div[2]/div[2]/div/ul/li[3]/div/h2/a'
            ]

            for post in post_list:
                driver.find_element(By.XPATH, home_xpath).click()
                time.sleep(5)

                driver.find_element(By.XPATH, post).click()
                print("Opened:", post)

                for pixel in [300, 600, 1000, 1500, 2000]:
                    driver.execute_script(f"window.scrollTo(0, {pixel});")
                    time.sleep(random.randint(5, 10))

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)

        except Exception as e:
            print("[ERROR]", e)

        finally:
            driver.quit()

if __name__ == "__main__":
    interface = "wlan0"
    MU = macUpdater()

    while True:
        new_mac = MU.random_mac()
        MU.change_mac(interface, new_mac)

        print("MAC:", MU.get_current_mac(interface))
        print("IP:", MU.get_ip_address(interface))
        time.sleep(10)

        MU.webpage_viewer("https://aajkijanta.com")
        time.sleep(random.randint(100, 200))
