import time
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.models import IdGuestImage, SelfieImage, EventImageToImageGroup, ImageGroup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

chrome_driver_path = "C:\\chromeDriver\\chromedriver.exe"


# הגדר את ה-ChromeOptions
def get_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("user-data-dir=C:\\Users\\DELL\\AppData\\Local\\Google\\Chrome\\User Data\\BOT2")
    return chrome_options


# הגדר את ה-Service של ChromeDriver
def get_chrome_service():
    return Service(executable_path=chrome_driver_path)


def open_whatsapp(driver):
    driver.get("https://web.whatsapp.com/")


def send_images_to_all():
    driver = webdriver.Chrome(service=get_chrome_service(), options=get_chrome_options())
    open_whatsapp(driver)
    while True:
        unsent_id_guest_images = IdGuestImage.objects.filter(
            image_group__image_group_to_event_images__sent=False
        ).distinct()
        for id_guest in unsent_id_guest_images:
            event_selfies = SelfieImage.objects.filter(event=id_guest.image_group.event)
            for selfie in event_selfies:
                if id_guest.is_same_person(selfie.get_encoding()):
                    id_guest.set_encoding(selfie.get_encoding())
                    id_guest.image_group.guest = selfie.guest
                    id_guest.image_group.save()
                    id_guest.save()
                    unsent_images = EventImageToImageGroup.objects.filter(sent=False).filter(
                        image_group=id_guest.image_group)
                    paths = []
                    for img in unsent_images:
                        paths.append(img.event_image.path)
                        img.sent = True
                        img.save()
                    image_upload(paths, selfie.guest, driver)
        time.sleep(2)
    driver.quit()


def image_upload(image_paths, guest, driver):
    # חיפוש מספר טלפון
    search_box = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
    )
    search_box.send_keys(guest.phone)
    search_box.send_keys(Keys.ENTER)
    time.sleep(2)

    # לחיצה על כפתור ההוספה
    attach_btn = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[1]/div[2]/div/div'))
    )
    time.sleep(2)
    attach_btn.click()
    time.sleep(2)
    # שליחת הנתיב של התמונה לרכיב ה-input
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

    print("הנתיב נשלח בהצלחה לרכיב ה-input")

    # המתנה לבדיקה
