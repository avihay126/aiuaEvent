# Face Recognition Event Bot

This project is a facial recognition system designed for events. Guests at an event can scan a QR code to open a WhatsApp chat with a bot, send a selfie, and later receive all the photos in which they appear directly through WhatsApp. The system uses advanced machine learning algorithms and facial recognition libraries to classify and deliver the photos.

## Features
- **WhatsApp Bot:** Guests interact with the system by sending selfies and receiving event photos.
- **Facial Recognition:** Classifies and matches guest faces using machine learning.
- **Event Photographer Integration:** Allows photographers to upload event photos, which are automatically processed and classified.
- **Backend:** Built with Django.
- **Frontend:** Developed separately with React (see [newaiuaphotographer](https://github.com/uriel123bm/newAiuaPhotographer)).

---

## Prerequisites
1. Python 3.8 or higher.
2. MySQL database.
3. Chrome browser and [ChromeDriver](https://sites.google.com/chromium.org/driver/).
4. [CMake](https://cmake.org/) installed and added to the system PATH (required for `dlib`).
5. WhatsApp account for bot integration.

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/avihay126/aiuaEvent.git
cd aiuaEvent
```

### 2. Set Up a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up the Database
- Create a MySQL database for the project.
- Update `DATABASES` settings in `settings.py` with your database credentials.

### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Add Selenium and ChromeDriver Paths
- Update the paths for Selenium and ChromeDriver in the project configuration files. Ensure `chromedriver.exe` is accessible from the defined paths.

### 7. Start the Server
```bash
python manage.py runserver
```
The server will be available at `http://127.0.0.1:8000/`.

---

## How to Use
1. **Event Setup:**
   - The photographer uploads event photos to the system.
2. **Guest Interaction:**
   - Guests scan the event QR code, which opens a WhatsApp chat with the bot.
   - Guests send a selfie to the bot.
3. **Facial Recognition and Photo Delivery:**
   - The system processes and classifies the photos.
   - All photos containing the guest are sent directly to them via WhatsApp.

---

## Troubleshooting
- **dlib Installation Issues:** Ensure `CMake` is installed and properly configured in your system's PATH.
- **ChromeDriver Compatibility:** Make sure the ChromeDriver version matches your Chrome browser version.

---

## Contribution
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Submit a pull request.

---

## Additional Information
- Frontend repository: [newaiuaphotographer](https://github.com/uriel123bm/newAiuaPhotographer)
- Developed using multiple libraries, including Selenium, TensorFlow, and DeepFace.

---

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

