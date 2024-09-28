import threading
import time
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.models import SelfieImage, EventImageToImageGroup, ImageGroup,Guest
from constants import *
from bots_common_func import get_chrome_service, get_chrome_options, close_chat
import logging


logger = logging.getLogger(__name__)


driver = None
lock_send = threading.Lock()

lock_all_send = threading.Lock()


def open_whatsapp():
    global driver
    try:
        driver = webdriver.Chrome(service=get_chrome_service(), options=get_chrome_options(DATA_DIR_BOT_2))
        driver.get("https://web.whatsapp.com/")
    except Exception as e:
        logger.error(e, exc_info=True)


def send_images_to_all():
    try:
        with lock_all_send:
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
                            whatssup_action(paths=paths, guest=selfie.guest, driver=driver)

            else:
                logger.info("driver is None")
    except Exception as e:
        logger.error(e, exc_info=True)



def whatssup_action(paths = None, guest = None, driver = None, event = None):
    with lock_send:
        if paths is None:
            send_thanks_to_all(event)
        else:
            if len(paths) > 0:
                image_upload(paths, guest, driver)



def send_thanks_to_all(event):
    global driver
    guests = Guest.objects.filter(event=event).all()
    for guest in guests:
        search_box = open_chat_with_guest(guest.phone, driver)
        if guest.stage == WAITING_FOR_MORE_PHOTOS:
            send_message("תודה שהשתתפת באירוע שלנו! מקווים שנהנת, צוות AIUA", driver)
        elif guest.stage == WAITING_FOR_GET_PHOTOS:
            send_message("לא מצאנו תמונות שלך באירוע. לא נורא, נתראה באירוע הבא!", driver)
        close_chat(driver)
        search_box.clear()
        guest.delete()





def open_chat_with_guest(phone_number, driver):
    search_box = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
    )
    time.sleep(1)
    search_box.clear()
    time.sleep(1)
    search_box.send_keys(phone_number)
    time.sleep(1)
    search_box.send_keys(Keys.ENTER)
    return search_box



def send_message(message, driver):
    message_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
    message_box.send_keys(message)
    message_box.send_keys(Keys.ENTER)
    time.sleep(1)
def image_upload(image_paths, guest, driver):
    open_chat_with_guest(guest.phone,driver)
    time.sleep(1)
    attach_btn = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="main"]/footer/div[1]/div/span/div/div[1]/div[2]/div/div/div/span'))
    )

    attach_btn.click()
    time.sleep(1)
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
    if not guest.event.is_open:
        time.sleep(1)
        send_message("תודה שהשתתפת באירוע שלנו! מקווים שנהנת, צוות AIUA", driver)
        guest.delete()
    else:
        guest.stage = WAITING_FOR_MORE_PHOTOS
        guest.save()
    close_chat(driver)
    time.sleep(1)
    logger.info(f"Photos have been sent successfully to {guest.phone}")
