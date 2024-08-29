
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
from core.models import Guest,Event,SelfieImage



events = []
chats = []

# ציין את הנתיב ל-ChromeDriver שלך
chrome_driver_path = "C:\\chromeDriver\\chromedriver.exe"
download_dir = "C:\\AiuaPhoto\\check"

# הגדר את ה-ChromeOptions
def get_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("user-data-dir=C:\\Users\\DELL\\AppData\\Local\\Google\\Chrome\\User Data\\BOT1")
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    return chrome_options


# הגדר את ה-Service של ChromeDriver
def get_chrome_service():
    return Service(executable_path=chrome_driver_path)

def open_whatsapp(driver):
    driver.get("https://web.whatsapp.com/")
    WebDriverWait(driver, 60).until(
                 EC.presence_of_element_located((By.XPATH, '//*[@id="side"]/div[2]/button[2]'))).click()
    time.sleep(2)



def get_chat_phone(driver):

    profile = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="main"]/header/div[2]')))
    profile.click()
    time.sleep(1)
    phone = None
    try:

        phone = WebDriverWait(driver,3).until(
            EC.presence_of_element_located((By.XPATH,'//*[@id="app"]/div/div[2]/div[5]/span/div/span/div/div/section/div[1]/div[2]/div/span/span')))
        print(phone.text[2:-1])
    except Exception as e:
        close_chat = driver.find_element(By.XPATH, '//*[@id="main"]/header/div[3]/div/div[3]/div/div/span')
        close_chat.click()
        close_button = driver.find_element(By.XPATH, '//*[@id="app"]/div/span[5]/div/ul/div/div/li[3]/div')
        close_button.click()

    return phone.text[2:-1]

def already_exist(phone):
    global chats
    chats = Guest.objects.all()
    print(chats.values())
    for chat in chats:
        if chat.phone == phone:
            return chat
    return None

def get_unread_chats(driver):
    unread_chats_parent = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="pane-side"]/div[1]/div/div')))
    unread_chats = unread_chats_parent.find_elements(By.XPATH, './*')
    return unread_chats

def get_current_chat(driver, chat):
    chat.click()
    phone = get_chat_phone(driver)
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



def send_message(message,driver):
    message_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
    message_box.send_keys(message)
    message_box.send_keys(Keys.ENTER)
    time.sleep(1)


def detect_faces(image_path):
    """Load an image file, detect faces, and extract face encodings."""
    # טוען את התמונה מהנתיב שסופק
    image = face_recognition.load_image_file(image_path)

    # מזהה את מיקומי הפנים בתמונה
    face_locations = face_recognition.face_locations(image)

    # בדיקה אם נמצאו פנים
    if not face_locations:
        print(f"No faces found in image: {image_path}")
        return [], []

    # מחשב את ה-encodings עבור כל פרצוף שזוהה
    face_encodings = face_recognition.face_encodings(image, face_locations)

    # מדפיס כמה פנים זוהו בתמונה
    print(f"Detected {len(face_locations)} faces in image: {image_path}")

    return face_encodings, face_locations
def download_photo(driver, photo_element, phone):
    photo_element.click()
    download_button = WebDriverWait(driver,5).until(
        EC.presence_of_element_located((By.XPATH,'//*[@id="app"]/div/span[3]/div/div/div[2]/div/div[1]/div[2]/div/div[6]/div'))
    )
    download_button.click()
    close_button = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/span[3]/div/div/div[2]/div/div[1]/div[2]/div/div[8]/div'))
    )
    close_button.click()

    # שימוש בשם מספר הטלפון לשם הקובץ
    time.sleep(3)  # להמתין שההורדה תסתיים. יש לשנות את הזמן בהתאם לצורך.
    # שם קובץ זמני בתיקיית ההורדות
    temp_filename = max([download_dir + "\\" + f for f in os.listdir(download_dir)], key=os.path.getctime)
    # שינוי שם הקובץ לשם מותאם אישית
    unique_filename = f"{phone}.JPG"
    final_filepath = os.path.join(download_dir, unique_filename)
    os.rename(temp_filename, final_filepath)

    return final_filepath

def save_photo(guest, face):
    selfi = SelfieImage(event=guest.event, guest=guest)
    selfi.set_encoding(face)
    selfi.save()
    time.sleep(2)



def get_photo_element(driver):
    message_list_parent = driver.find_element(By.XPATH,'//*[@id="main"]/div[3]/div/div[2]/div[3]')
    message_list = message_list_parent.find_elements(By.XPATH,'./*')
    last_message = message_list[-1]
    image = last_message.find_elements(By.CSS_SELECTOR, '.x15kfjtz.x1c4vz4f.x2lah0s.xdl72j9.x127lhb5.x4afe7t.xa3vuyk.x10e4vud')
    if image:
        return last_message
    return None


def check_photo(driver, photo_element, phone, guest):
    file_path = download_photo(driver, photo_element, phone)
    if os.path.exists(file_path):
        print(f"File {file_path} exists.")
        faces, location = detect_faces(file_path)
        print(f"Number of faces detected: {len(faces)}")
        if len(faces) == 1:
            print("good")
            save_photo(guest, faces[0])
            send_message("תודה רבה! תקבל את התמונות שלך אחרי שהצלם יעלה אותן!", driver)
            os.remove(file_path)
            return True
        elif len(faces) > 1:
            print("too much faces")
            send_message("יש יותר מפרצוף אחד. נא לשלוח תמונה עם פרצוף אחד בלבד!", driver)
        else:
            print("there is no face")
            send_message("לא זוהו פנים בתמונה. נסה שנית!", driver)
        os.remove(file_path)
    else:
        print(f"Error: File {file_path} does not exist.")
    return False



def close_chat(driver):
    close_chat = driver.find_element(By.XPATH, '//*[@id="main"]/header/div[3]/div/div[3]/div/div/span')
    close_chat.click()
    close_button = driver.find_element(By.XPATH, '//*[@id="app"]/div/span[5]/div/ul/div/div/li[3]/div')
    close_button.click()
    time.sleep(2)


def check_messages():
    driver = webdriver.Chrome(service=get_chrome_service(), options=get_chrome_options())
    open_whatsapp(driver)
    while True:
        try:
            unread_chats = get_unread_chats(driver)
            for chat in unread_chats:
                current_chat = get_current_chat(driver,chat)
                text = chat.text.split("\n")[2]
                if current_chat.stage == 0:
                    if "aiua" in text.lower():
                        event = get_chat_event(text)
                        if event == None:
                            send_message("נא לשלוח הודעה בפורמט הבא: היי Aiua, אפשר לקבל בבקשה את התמונות שלי מ *שם האירוע* בתאריך *dd/mm/yyyy*?", driver)
                        else:
                            current_chat.event = event
                            send_message("בוודאי! נא לשלוח סלפי שלך במקום מואר וברור.", driver)
                            current_chat.stage = 1
                            current_chat.save()
                elif current_chat.stage == 1:
                    if text == "תמונה":
                        time.sleep(1)
                        photo_element = get_photo_element(driver)
                        time.sleep(1)
                        if photo_element is not None:
                            if check_photo(driver, photo_element, current_chat.phone.replace(' ', ''),current_chat):
                                current_chat.stage = 2
                                current_chat.save()
                elif current_chat.stage == 2:
                    send_message("לא שכחנו אותך! התמונות שלך יגיעו אליך מיד אחרי שהצלם יעלה אותן", driver)
                close_chat(driver)
            time.sleep(1)
        except Exception as e:
            print(f"Error checking messages: {e}")
            time.sleep(3)

    driver.quit()



