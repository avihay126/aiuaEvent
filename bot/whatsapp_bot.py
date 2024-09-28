import glob
import threading

import face_recognition
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
from core.models import Guest, Event, SelfieImage
from bots_common_func import get_chrome_service, get_chrome_options, close_chat
from photos_sender.sender_bot import send_images_to_all
from thread_manager import submit_task, get_faces, force_shutdown, get_encodings
import logging
import logging_config
from constants import *

logger = logging.getLogger(__name__)

events = []
chats = []


def add_chrome_prefs():
    chrome_options = get_chrome_options(DATA_DIR_BOT_1)
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    return chrome_options


def open_whatsapp(driver):
    driver.get("https://web.whatsapp.com/")
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="side"]/div[2]/button[2]'))).click()
    time.sleep(2)


def valid_phone(str):
    if len(str) > 15:
        phone = str[2:-1]
        if len(phone) == 15:
            if phone[:3].isdigit() and phone[4:6].isdigit() and phone[7:10].isdigit() and phone[11:].isdigit():
                return True
    return False


def get_chat_phone(driver):
    profile = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="main"]/header/div[2]')))
    profile.click()
    time.sleep(1)
    phone = None
    try:
        phone_parent = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH,
                                            '//*[@id="app"]/div/div[2]/div[5]/span/div/span/div/div/section/div[1]/div[2]')))
        lst = phone_parent.find_elements(By.XPATH, './*')
        if valid_phone(lst[0].text):
            phone = lst[0].text[2:-1]
        else:
            phone = lst[1].text[2:-1]

        logger.info(phone)
    except Exception as e:
        logger.error("its a group")
        close_chat(driver)

    return phone


def already_exist(phone):
    global chats
    chats = Guest.objects.all()
    for chat in chats:
        if chat.phone == phone:
            return chat
    return None


def get_unread_chats(driver):
    try:
        unread_chats_parent = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="pane-side"]/div[1]/div/div')))
        unread_chats = unread_chats_parent.find_elements(By.XPATH, './*')
        return unread_chats
    except Exception as e:
        logger.error("No messages found")
        return []



def get_current_chat(driver, chat):
    time.sleep(1)
    chat.click()
    phone = get_chat_phone(driver)
    if phone is None:
        return None
    exist = already_exist(phone)
    current_chat = None
    if exist is None:
        current_chat = Guest(name="", phone=phone, event=None, stage=0)
        current_chat.save()

    else:
        current_chat = exist
    return current_chat


def get_chat_event(text):
    global events
    events = Event.objects.all()
    for event in events:
        if event.date in text and event.name in text:
            return event
    return None


def send_message(message, driver):
    message_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
    message_box.send_keys(message)
    message_box.send_keys(Keys.ENTER)
    time.sleep(1)


def detect_faces(image_path):
    """Load an image file, detect faces, and extract face encodings."""
    try:
        image, face_locations = get_faces(image_path)

        if not face_locations:
            logger.info(f"No faces found in image: {image_path}")
            return [], []

        face_encodings = get_encodings(image, face_locations)

        logger.info(f"Detected {len(face_locations)} faces in image: {image_path}")
    except Exception as e:
        logger.error(e, exc_info=True)
        return [], []

    return face_encodings, face_locations


def download_photo(driver, photo_element, phone):
    final_filepath = None
    try:
        photo_element.click()
        download_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="app"]/div/span[3]/div/div/div[2]/div/div[1]/div[2]/div/div[6]/div'))
        )
        download_button.click()

        close_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="app"]/div/span[3]/div/div/div[2]/div/div[1]/div[2]/div/div[8]/div'))
        )
        close_button.click()

        for i in range(3):
            time.sleep(1)
            files = glob.glob(os.path.join(DOWNLOAD_DIR, "*"))
            if files:
                temp_filename = max(files, key=os.path.getctime)
                if temp_filename.endswith(".crdownload"):
                    continue
                else:
                    break

        unique_filename = f"{phone}.JPG"
        final_filepath = os.path.join(DOWNLOAD_DIR, unique_filename)
        os.rename(temp_filename, final_filepath)
    except Exception as e:
        logger.error(e, exc_info=True)

    return final_filepath


def save_photo(guest, face):
    selfi = SelfieImage(event=guest.event, guest=guest)
    selfi.set_encoding(face)
    selfi.save()
    time.sleep(1)


def get_photo_element(driver):
    time.sleep(1)
    message_list_parent = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="main"]/div[3]/div/div[2]/div[3]'))
    )
    message_list = message_list_parent.find_elements(By.XPATH, './*')
    last_message = message_list[-1]
    image = last_message.find_elements(By.CSS_SELECTOR,
                                       '.x15kfjtz.x1c4vz4f.x2lah0s.xdl72j9.x127lhb5.x4afe7t.xa3vuyk.x10e4vud')
    if image:
        return last_message
    return None


def check_photo(driver, photo_element, phone, guest):
    try:
        file_path = download_photo(driver, photo_element, phone)
        if os.path.exists(file_path):
            logger.info(f"File {file_path} exists.")
            faces, location = detect_faces(file_path)
            logger.info(f"Number of faces detected: {len(faces)}")
            if len(faces) == 1:
                logger.info("good")
                save_photo(guest, faces[0])
                send_message("תודה רבה! נשלח לך את התמונות כשהצלם יעלה אותן!", driver)
                os.remove(file_path)
                submit_task(send_images_to_all)
                return True
            elif len(faces) > 1:
                logger.info("too much faces")
                send_message("יש יותר מפרצוף אחד. נא לשלוח תמונה עם פרצוף אחד בלבד!", driver)
            else:
                logger.info("there is no face")
                send_message("לא זוהו פנים בתמונה. נסה שנית!", driver)
            os.remove(file_path)
        else:
            logger.info(f"Error: File {file_path} does not exist.")
    except Exception as e:
        logger.error(e, exc_info=True)
    return False



def contains_keywords(text, keywords):
    for word in keywords:
        if word in text:
            return True
    return False

def check_messages():
    driver = webdriver.Chrome(service=get_chrome_service(), options=add_chrome_prefs())
    open_whatsapp(driver)
    while True:
        try:
            if force_shutdown():
                break
            unread_chats = get_unread_chats(driver)
            for chat in unread_chats:
                current_chat = get_current_chat(driver, chat)
                if current_chat is not None:
                    text = ""
                    try:
                        text = chat.text.split("\n")[2]
                    except Exception as e:
                        logger.info("emojie sent")
                        close_chat(driver)
                        continue
                    if current_chat.stage == 0:
                        if "aiua" in text.lower():
                            event = get_chat_event(text)
                            if event == None:
                                send_message(
                                    "נא לשלוח הודעה בפורמט הבא: היי Aiua, אפשר לקבל בבקשה את התמונות שלי מ *שם האירוע* בתאריך *dd/mm/yyyy*?",
                                    driver)
                            else:
                                current_chat.event = event
                                send_message("בוודאי! נא לשלוח סלפי שלך במקום מואר וברור.", driver)
                                current_chat.stage = 1
                                current_chat.save()
                    elif current_chat.stage == 1:
                        if text == "תמונה":
                            photo_element = get_photo_element(driver)
                            time.sleep(1)
                            if photo_element is not None:
                                if check_photo(driver, photo_element, current_chat.phone.replace(' ', ''), current_chat):
                                    current_chat.stage = 2
                                    current_chat.save()
                    elif current_chat.stage == 2:
                        if contains_keywords(["תודה"]):
                            send_message("בשמחה! נשלח לך את התמונות כשיהיו מוכנות", driver)
                        elif contains_keywords(text, ["מתי","איפה","איך","מה "]):
                            send_message("לא שכחנו אותך! התמונות שלך יגיעו אליך מיד אחרי שהצלם יעלה אותן", driver)
                    elif current_chat.stage == 3:
                        send_message("הצלם טרם העלה את כל התמונות, ייתכן שיש עוד תמונות שאתה מופיע בהן", driver)
                    close_chat(driver)
            time.sleep(3)
        except Exception as e:
            logger.error(f"error", exc_info=True)
            time.sleep(3)

    driver.quit()
