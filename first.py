!/usr/bin/env python3


import time
import random
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException

class macUpdater:
    def _init_(self):
        pass
    
    def random_mac(self):
        """Generate a random MAC address (locally administered, unicast)."""
        mac = [0xdc, 0xa6, 0x32,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
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
        result = subprocess.run(["cat", f"/sys/class/net/{interface}/address"],
                                capture_output=True, text=True)
        return result.stdout.strip()
    
    def get_ip_address(self, interface):
        try:
            result = subprocess.run(
                ["ip", "-4", "addr", "show", interface],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("inet "):
                    return line.split()[1].split("/")[0]
            return "No IP assigned"
        except subprocess.CalledProcessError:
            return "Error retrieving IP"

class VisitorSimulator:
    def _init_(self):
        # Insert real proxies here like: "http://user:pass@proxy:port"
        self.proxies = [
            # "http://username:password@proxy1:port",
            # "http://username:password@proxy2:port",
        ]
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            # Add more real user agents to diversify
        ]
    
    def create_driver(self):
        options = Options()
        # Avoid headless so visits count realistically
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        user_agent = random.choice(self.user_agents)
        options.add_argument(f"user-agent={user_agent}")
        
        if self.proxies:
            proxy = random.choice(self.proxies)
            options.add_argument(f'--proxy-server={proxy}')
            print(f"[INFO] Using proxy: {proxy}")
        else:
            print("[INFO] No proxy used")
        
        driver = webdriver.Chrome(options=options)
        window_sizes = [(1280, 720), (1366, 768), (1440, 900), (1600, 900), (1920, 1080)]
        size = random.choice(window_sizes)
        driver.set_window_size(size[0], size[1])
        print(f"[INFO] Window size set to: {size}")
        return driver
    
    def simulate_browsing(self, URL):
        driver = self.create_driver()
        try:
            driver.get(URL)
            print(f"[INFO] Opened URL: {URL}")
            time.sleep(random.uniform(4, 8))  # Wait for load
            
            action = ActionChains(driver)
            action.move_by_offset(random.randint(100, 300), random.randint(100, 300)).perform()
            time.sleep(random.uniform(1, 3))
            
            scroll_points = [random.randint(400, 800), random.randint(800, 1300), random.randint(1300, 1800)]
            for sp in scroll_points:
                driver.execute_script(f"window.scrollTo({{top: {sp}, behavior: 'smooth'}});")
                time.sleep(random.uniform(3, 6))
            
            links = []
            attempts = 0
            while not links and attempts < 3:
                try:
                    links = driver.find_elements(By.TAG_NAME, 'a')
                except Exception as e:
                    print(f"[WARN] Error finding links: {e}")
                attempts += 1
                time.sleep(2)
            
            if links:
                random_link = random.choice(links)
                href = random_link.get_attribute('href')
                if href and href.startswith("http"):
                    print(f"[INFO] Clicking link: {href}")
                    try:
                        random_link.click()
                        time.sleep(random.uniform(5, 10))
                    except WebDriverException as e:
                        print(f"[WARN] Click failed: {e}")
                else:
                    print("[INFO] Selected link's href invalid or not clickable")
            else:
                print("[INFO] No links to click")
                
        except Exception as e:
            print(f"[ERROR] Browsing error: {e}")
        finally:
            driver.quit()
            print("[INFO] Browser closed")

if _name_ == "_main_":
    interface = "wlan0"
    MU = macUpdater()
    simulator = VisitorSimulator()
    url = "https://aajkijanta.com"
    
    while True:
        # Change MAC address (note: may require sudo privileges)
        new_mac = MU.random_mac()
        MU.change_mac(interface, new_mac)
        current_mac = MU.get_current_mac(interface)
        ip_address = MU.get_ip_address(interface)
        print(f"[*] Verified MAC: {current_mac}")
        print(f"[*] Current IP: {ip_address}\n{'-'*50}")
        
        # Simulate realistic visitor browsing
        simulator.simulate_browsing(url)
        
        delay = random.uniform(120, 300)  # Delay 2-5 minutes between visits
        print(f"[INFO] Sleeping for {delay:.2f} seconds before next iteration...")
        time.sleep(delay)
