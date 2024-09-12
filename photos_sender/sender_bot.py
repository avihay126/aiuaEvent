import time
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.models import SelfieImage, EventImageToImageGroup, ImageGroup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bots_common_func import get_chrome_service, get_chrome_options, close_chat
import logging
import logging_config

logger = logging.getLogger(__name__)

user_data_dir = "user-data-dir=C:\\Users\\DELL\\AppData\\Local\\Google\\Chrome\\User Data\\BOT2"
driver = None

def open_whatsapp():
    global driver
    try:
        driver = webdriver.Chrome(service=get_chrome_service(), options=get_chrome_options(user_data_dir))
        driver.get("https://web.whatsapp.com/")
    except Exception as e:
        logger.error(e)


def send_images_to_all():
    try:
        global driver
        logger.info("searching for selfies")

        if driver is not None:
            unsent_images_groups = ImageGroup.objects.filter(
                image_group_to_event_images__sent=False
            ).distinct()
            for group in unsent_images_groups:
                event_selfies = SelfieImage.objects.filter(event=group.event)
                for selfie in event_selfies:
                    if group.is_same_person(selfie.get_encoding()):
                        group.guest = selfie.guest
                        group.save()
                        unsent_images = EventImageToImageGroup.objects.filter(sent=False).filter(
                            image_group=group)
                        paths = []
                        for img in unsent_images:
                            paths.append(img.event_image.path)
                            img.sent = True
                            img.save()
                        image_upload(paths, selfie.guest, driver)

        else:
            logger.info("driver is None")
    except Exception as e:
        logger.error(e)


def image_upload(image_paths, guest, driver):
    search_box = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
    )
    search_box.send_keys(guest.phone)
    search_box.send_keys(Keys.ENTER)
    time.sleep(2)

    attach_btn = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[1]/div[2]/div/div'))
    )
    time.sleep(2)
    attach_btn.click()
    time.sleep(2)
    image_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'))
    )
    all_image_paths = '\n'.join(image_paths)
    image_input.send_keys(all_image_paths)
    time.sleep(2)

    send_button = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/div[2]/div[2]/div[2]/span/div/div/div/div[2]/div/div[2]/div[2]/div/div'))
    )
    send_button.click()
    time.sleep(1)
    guest.stage = 3
    guest.save()

    logger.info("Photos have been sent successfully")
    search_box.clear()
    close_chat(driver)