#!/usr/bin/env python3
"""
mac_updater.py

Features:
- Periodically changes MAC (locally administered unicast) on chosen interface.
- Renews DHCP lease using detected DHCP manager (dhclient, dhcpcd, NetworkManager).
- Uses Selenium (Chromium/Chrome) to visit pages with visible actions.
- Logging to console + file, JSON/YAML config support.
"""

import os
import sys
import time
import json
import random
import shutil
import logging
import argparse
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

try:
    import yaml
except Exception:
    yaml = None

# ----------------------------
# Config Dataclass
# ----------------------------
@dataclass
class Config:
    interface: str = "wlan0"
    interval_minutes: int = 5
    website_list: List[str] = field(default_factory=lambda: ["https://aajkijanta.com"])
    headless: bool = False
    driver_path: Optional[str] = None
    log_file: str = "mac_updater.log"
    use_dhclient_fallback: bool = True
    random_user_agents: bool = True
    stealth_mode: bool = True
    actions_per_session: int = 3
    scroll_positions: List[int] = field(default_factory=lambda: [300, 800, 1200, 2000])
    fontsize_list: List[str] = field(default_factory=lambda: ["10px", "12px", "14px", "16px", "18px", "20px"])
    window_sizes: List[tuple] = field(default_factory=lambda: [(1280, 720), (1024, 768), (640, 480)])


# ----------------------------
# Logging
# ----------------------------
def setup_logger(logfile: str):
    logger = logging.getLogger("mac_updater")
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


# ----------------------------
# Config Loader
# ----------------------------
def load_config(path: Optional[str]) -> Config:
    if not path:
        return Config()

    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8") as f:
        if ext in (".yaml", ".yml") and yaml:
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    cfg = Config()
    if isinstance(data, dict):
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)

    return cfg


def which(program: str) -> Optional[str]:
    return shutil.which(program)


# ----------------------------
# MAC + Network Manager
# ----------------------------
class MacUpdater:
    def __init__(self, config: Config, logger: logging.Logger):
        self.cfg = config
        self.logger = logger
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15"
        ]

    def generate_random_mac(self) -> str:
        first = random.randint(0x00, 0xff) & 0b11111100
        first |= 0b00000010
        mac = [first] + [random.randint(0, 255) for _ in range(5)]
        return ":".join(f"{b:02x}" for b in mac)

    def change_mac(self, interface: str, new_mac: str) -> bool:
        cmds = [
            ["ip", "link", "set", interface, "down"],
            ["ip", "link", "set", interface, "address", new_mac],
            ["ip", "link", "set", interface, "up"],
        ]
        try:
            for cmd in cmds:
                subprocess.run(["sudo"] + cmd, check=True, capture_output=True)
            self.logger.info(f"Changed MAC to {new_mac} on {interface}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"MAC change failed: {e}")
            return False

    def get_current_mac(self, interface: str) -> Optional[str]:
        try:
            with open(f"/sys/class/net/{interface}/address") as f:
                return f.read().strip()
        except:
            return None

    def detect_dhcp_agent(self) -> str:
        if which("dhclient"):
            return "dhclient"
        if which("dhcpcd"):
            return "dhcpcd"
        if which("nmcli"):
            return "nmcli"
        if which("systemctl"):
            return "systemctl"
        return "none"

    def renew_ip(self, interface: str) -> bool:
        agent = self.detect_dhcp_agent()
        try:
            if agent == "dhclient":
                subprocess.run(["sudo", "dhclient", "-r", interface], check=False)
                subprocess.run(["sudo", "dhclient", interface], check=True)
            elif agent == "dhcpcd":
                subprocess.run(["sudo", "systemctl", "restart", "dhcpcd"], check=True)
            elif agent == "nmcli":
                subprocess.run(["sudo", "nmcli", "device", "disconnect", interface], check=False)
                subprocess.run(["sudo", "nmcli", "device", "connect", interface], check=True)
            elif agent == "systemctl":
                subprocess.run(["sudo", "systemctl", "restart", "networking"], check=True)
            else:
                self.logger.warning("No DHCP client detected")
                return False

            self.logger.info(f"DHCP renewed using {agent}")
            return True
        except Exception as e:
            self.logger.error(f"DHCP renewal failed: {e}")
            return False

    def get_ip_address(self, interface: str) -> str:
        try:
            r = subprocess.run(["ip", "-4", "addr", "show", interface],
                               text=True, capture_output=True, check=True)
            for line in r.stdout.splitlines():
                line = line.strip()
                if line.startswith("inet "):
                    return line.split()[1].split("/")[0]
            return "No IP assigned"
        except:
            return "Error retrieving IP"

    def _find_chromedriver(self) -> Optional[str]:
        if self.cfg.driver_path and os.path.exists(self.cfg.driver_path):
            return self.cfg.driver_path
        return which("chromedriver") or which("msedgedriver") or which("chromium-chromedriver")

    def _build_chrome_options(self) -> Options:
        opts = Options()
        if self.cfg.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        if self.cfg.random_user_agents:
            opts.add_argument(f"--user-agent={random.choice(self.user_agents)}")

        return opts

    # ----------------------------
    # UPDATED visible Selenium function
    # ----------------------------
    def webpage_viewer(self, url: str):
        path = self._find_chromedriver()
        if not path:
            self.logger.error("No chromedriver found")
            return

        opts = self._build_chrome_options()

        try:
            driver = webdriver.Chrome(service=Service(path), options=opts)
        except Exception as e:
            self.logger.error(f"WebDriver error: {e}")
            return

        w, h = random.choice(self.cfg.window_sizes)
        driver.set_window_size(w, h)

        try:
            # 1. Open the webpage
            driver.get(url)
            time.sleep(3)

            # 2. Click the first post/article if available
            try:
                first_link = driver.find_element(By.TAG_NAME, "a")
                driver.execute_script("arguments[0].scrollIntoView();", first_link)
                time.sleep(1)
                first_link.click()
                time.sleep(3)
            except Exception:
                self.logger.info("No clickable post found, staying on homepage")

            # 3. Scroll slowly down the page
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            current_position = 0

            while current_position < scroll_height:
                scroll_step = random.randint(200, 600)
                current_position += scroll_step
                driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(1.0, 2.5))

            time.sleep(2)

            # 4. Close the browser
            driver.quit()

        except Exception as e:
            self.logger.error(f"Selenium error: {e}")
            try:
                driver.quit()
            except:
                pass

    # ----------------------------
    # Run one full cycle
    # ----------------------------
    def run_once(self):
        interface = self.cfg.interface
        mac = self.generate_random_mac()
        self.logger.info(f"Setting MAC: {mac}")

        if not self.change_mac(interface, mac):
            return

        time.sleep(1)

        if not self.renew_ip(interface):
            self.logger.warning("IP renewal failed")

        mac_now = self.get_current_mac(interface)
        ip_now = self.get_ip_address(interface)
        self.logger.info(f"MAC Now: {mac_now}")
        self.logger.info(f"IP Now: {ip_now}")

        for url in self.cfg.website_list[:2]:
            self.logger.info(f"Visiting {url}")
            self.webpage_viewer(url)


# ----------------------------
# CLI
# ----------------------------
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--config", "-c")
    p.add_argument("--once", action="store_true")
    p.add_argument("--interface", "-i")
    return p.parse_args()


def main():
    args = parse_args()

    try:
        cfg = load_config(args.config) if args.config else Config()
    except Exception as e:
        print(f"Config error: {e}")
        sys.exit(1)

    if args.interface:
        cfg.interface = args.interface

    logger = setup_logger(cfg.log_file)
    mu = MacUpdater(cfg, logger)

    logger.info(f"Starting updater for {cfg.interface}")

    if args.once:
        mu.run_once()
        return

    try:
        while True:
            mu.run_once()
            time.sleep(max(10, cfg.interval_minutes * 60))
    except KeyboardInterrupt:
        logger.info("Stopped")


if __name__ == "__main__":
    main()
