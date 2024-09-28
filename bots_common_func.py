import time

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

chrome_driver_path = "C:\\chromeDriver\\chromedriver.exe"
def get_chrome_service():
    return Service(executable_path=chrome_driver_path)


def get_chrome_options(path):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(path)

    return chrome_options

def close_chat(driver):
    close_chat = driver.find_element(By.XPATH, '//*[@id="main"]/header/div[3]/div/div[3]/div/div/span')
    close_chat.click()
    time.sleep(1)
    close_button = driver.find_element(By.XPATH, '//*[@id="app"]/div/span[5]/div/ul/div/div/li[3]/div')
    close_button.click()
