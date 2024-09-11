import os
import io
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ExifTags
from core.models import Event, EventImage
from thread_manager import submit_task
from face_classification.classify import classify_faces
import logging
import logging_config

logger = logging.getLogger(__name__)

main_dir = "C:\\AiuaPhoto\\"


# דף בית לדוגמה
def home(request):
    return HttpResponse("Welcome to the home page")


# דף אודות לדוגמה
def about(request):
    return HttpResponse("This is the about page")


# החזרת רשימת האירועים
def get_events(request):
    events = Event.objects.all()
    events_list = list(events.values())  # המרת ה-QuerySet לרשימה של מילונים
    return JsonResponse(events_list, safe=False)


# פונקציה לתיקון הכיוון של תמונה בהתאם לנתוני EXIF
def correct_orientation(img):
    try:
        exif = img._getexif()
        if exif:
            orientation = next((key for key, val in ExifTags.TAGS.items() if val == 'Orientation'), None)
            if orientation and orientation in exif:
                orientation_value = exif[orientation]
                if orientation_value == 3:
                    img = img.rotate(180, expand=True)
                elif orientation_value == 6:
                    img = img.rotate(270, expand=True)
                elif orientation_value == 8:
                    img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return img


# פונקציה לשינוי גודל התמונה
def resize_image(image_file, max_size=(1500, 1500), quality=90, max_file_size_kb=500):
    with io.BytesIO(image_file.read()) as image_data:
        with Image.open(image_data) as img:
            image_data.seek(0, os.SEEK_END)
            file_size_kb = image_data.tell() / 1024
            image_data.seek(0)

            width, height = img.size
            if file_size_kb <= max_file_size_kb and width <= max_size[0] and height <= max_size[1]:
                image_data.seek(0)  # Rewind to the beginning for return
                return io.BytesIO(image_data.getvalue())

            img = correct_orientation(img)
            img.thumbnail(max_size, Image.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            buffer.seek(0)

    return buffer


# פונקציה לביצוע עיבוד התמונות ברקע
def process_images(event, files, upload_directory, start_index):
    try:
        index = start_index
        paths = []

        for key in files:
            image = files[key]
            resized_image = resize_image(image)

            if resized_image is None:
                logger.info(f"Error resizing image {key}")
                continue

            image_path = os.path.join(upload_directory, f'img_{index}.jpg')

            # כתיבת התמונה לדיסק
            with open(image_path, 'wb') as destination:
                destination.write(resized_image.getvalue())  # כתיבת ה-buffer ישירות לדיסק

            # יצירת אובייקט EventImage
            EventImage.objects.create(path=image_path, event=event)
            paths.append(image_path)
            index += 1

        # קריאה לפונקציה לעיבוד הפנים אחרי שהקבצים נשמרו
        submit_task(classify_faces, event, paths)
    except Exception as e:
        logger.error(f"Error processing images: {e}")


@csrf_exempt
def add_photos(request):
    if request.method == 'POST':
        try:
            event_id = request.GET.get('event-id')
            event = Event.objects.get(id=event_id)

            upload_directory = os.path.join(main_dir, event.directory_path)
            if not os.path.exists(upload_directory):
                os.makedirs(upload_directory)

            index = EventImage.objects.filter(event=event).count()

            # קריאה לפונקציה לעיבוד התמונות ברקע
            files_copy = {key: io.BytesIO(file.read()) for key, file in request.FILES.items()}
            submit_task(process_images, event, files_copy, upload_directory, index)

            # החזרת תגובה ללקוח מיידית
            return JsonResponse(
                {'status': 'success', 'message': 'Images uploaded successfully, processing in background!'})
        except Exception as e:
            logger.error(e)
            return JsonResponse({'status': 'error', 'message': f'Error occurred: {str(e)}'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)
