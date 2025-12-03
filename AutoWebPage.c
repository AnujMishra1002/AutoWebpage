#!/usr/bin/env python3
import os
import time
import random
import subprocess
from selenium import webdriver
from selenium.webdriver.edge.service import Service  # Import the Service class
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class macUpdater:
    def _init_(self):
        self.name = "ABC" # Instance attribute
        self.age = "20" # Instance attribute
    
    def random_mac(self):
        """Generate a random MAC address (locally administered, unicast)."""
        mac = [0xdc, 0xa6, 0x32,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: "%02x" % x, mac))
    
    def change_mac(self, interface, new_mac):
        """Change the MAC address of the given interface."""
        try:
            subprocess.run(["sudo", "ip", "link", "set", interface, "down"], check=True)
            subprocess.run(["sudo", "ip", "link", "set", interface, "address", new_mac], check=True)
            subprocess.run(["sudo", "ip", "link", "set", interface, "up"], check=True)
            print(f"[+] Changed {interface} MAC address to {new_mac}")
        except subprocess.CalledProcessError as e:
            print(f"[!] Failed to change MAC: {e}")
        
    def get_current_mac(self, interface):
        """Return the current MAC address of the given interface."""
        result = subprocess.run(["cat", f"/sys/class/net/{interface}/address"],
                            capture_output=True, text=True)
        return result.stdout.strip()
    
    def get_ip_address(self, interface):
        """Get the current IP address assigned to the interface."""
        try:
            result = subprocess.run(
                ["ip", "-4", "addr", "show", interface],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("inet "):
                    # Extract IP address before the slash
                    return line.split()[1].split("/")[0]
            return "No IP assigned"
        except subprocess.CalledProcessError:
            return "Error retrieving IP"
            
    def webpage_viewer(self, URL):
        #myglobalip=nslookup myip.opendns.com resolver1.opendns.com
        #result = subprocess.run('nslookup myip.opendns.com resolver1.opendns.com', shell=True, capture_output=True, text=True)
        #output = result.stdout
        #print("Global IP {}".format(output.split('\n')[4]))
        
        # Specify the path to your Edge WebDriver
        edge_driver_path = "C:/Users/Mr.Face/Downloads/edgedriver/msedgedriver.exe"
        
        # Path to your chromedriver executable
        chromedriver_path = "/usr/lib/chromium-browser/chromedriver"
        
        # Chromium binary location
        chromium_binary_path = "/usr/bin/chromium-browser"
        
        # Set Chrome options
        options = Options()
        options.binary_location = chromium_binary_path
        
        # Optional: run in headless mode (no GUI window)
        # options.add_argument("--headless")
        
        # Required options for Raspberry Pi / headless environment
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Use the Service class to specify the driver path
        service = Service(chromedriver_path)
        
        # Initialize the Edge WebDriver
        # options = webdriver.EdgeOptions()
        # options.use_chromium = True
        driver = webdriver.Chrome(service=service, options=options)
        Toss = random.randint(0,1)
        if Toss:
            driver.set_window_size(1280, 720)
        else:
            driver.set_window_size(640, 480)
        fontsize_list = ["10px", "12px", "14px", "16px", "18px", "20px"]
        font_size = random.choice(fontsize_list)
    
        try:
            # Open the website
            driver.get(URL)
            driver.execute_script(f"""
                            var style = document.createElement('style');
                            style.innerHTML = 'body {{ font-size: {font_size} !important; }}';
                            document.head.appendChild(style);
                            """)
            time.sleep(5)  # Allow some time for the page to load
            homePage= '/html/body/div[1]/header/div/h1/a'
            post_list = ['/html/body/div[1]/main/div[1]/div[2]/div[1]/div/ul/li/div/h2/a',
                         '/html/body/div[1]/main/div[1]/div[2]/div[2]/div/ul/li[1]/div/h2/a',
                         '/html/body/div[1]/main/div[1]/div[2]/div[2]/div/ul/li[2]/div/h2/a',
                         '/html/body/div[1]/main/div[1]/div[2]/div[2]/div/ul/li[3]/div/h2/a']
            for posts in post_list:
                home = driver.find_element(By.XPATH, homePage)
                home.click()
                time.sleep(5)
                post_element = driver.find_element(By.XPATH, posts)
                post_element.click()
                
                print("Post has been opened!")
                target_pixel = 1000  # Change this value to your desired scroll position
                driver.execute_script(f"""
                    window.scrollTo({{
                    top: {target_pixel},
                    behavior: 'smooth'
                    }});
                    """)
                time.sleep(random.randint(5, 15))
                
                target_pixel = 1500  # Change this value to your desired scroll position
                driver.execute_script(f"""
                    window.scrollTo({{
                    top: {target_pixel},
                    behavior: 'smooth'
                    }});
                    """)
                time.sleep(random.randint(5, 15))
                
                target_pixel = 2000  # Change this value to your desired scroll position
                driver.execute_script(f"""
                    window.scrollTo({{
                    top: {target_pixel},
                    behavior: 'smooth'
                    }});
                    """)
                time.sleep(random.randint(5, 15))
                
                # Scroll to the bottom of the page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
                # Scroll back to the top of the page
                target_pixel = 50  # Change this value to your desired scroll position
                driver.execute_script(f"""
                    window.scrollTo({{
                    top: {target_pixel},
                    behavior: 'smooth'
                    }});
                    """)
                time.sleep(random.randint(5, 15))
                print('complete : {}'.format(posts))
        
        finally:
            # Clear cookies and Close the browser
            driver.delete_all_cookies()
            driver.quit()

if _name_ == "_main_":
    interface = "wlan0"
    interval = 1 * 60  # 5 minutes in seconds
    MU = macUpdater()
    print(f"[*] Starting automatic MAC changer for {interface} (every {interval/60} minutes)")
    while True:
        new_mac = MU.random_mac()
        MU.change_mac(interface, new_mac)
        current_mac = MU.get_current_mac(interface)
        ip_address = MU.get_ip_address(interface)
        print(f"[*] Verified MAC: {current_mac}")
        print(f"[*] Current IP: {ip_address}\n{'-'*50}")
        time.sleep(20)
        MU.webpage_viewer("https://aajkijanta.com")
