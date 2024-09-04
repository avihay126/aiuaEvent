import os
import threading
from queue import Queue
from django.http import HttpResponse,JsonResponse
from core.models import Event, EventImage
from django.views.decorators.csrf import csrf_exempt

from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ExifTags
import os
import io








main_dir = "C:\\AiuaPhoto\\"
def home(request):
    return HttpResponse("Welcome to the home page")

def about(request):
    return HttpResponse("This is the about page")

def get_events(request):
    events = Event.objects.all()
    events_list = list(events.values())  # המרת ה-QuerySet לרשימה של מילונים
    return JsonResponse(events_list, safe=False)


def correct_orientation(img):
    """Correct the orientation of the image based on EXIF data."""
    try:
        exif = img._getexif()
        if exif is not None:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            else:
                orientation = None

            if orientation and orientation in exif:
                orientation_value = exif[orientation]
                if orientation_value == 3:
                    img = img.rotate(180, expand=True)
                elif orientation_value == 6:
                    img = img.rotate(270, expand=True)
                elif orientation_value == 8:
                    img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # Cases where EXIF data is not available or doesn't contain orientation
        pass
    return img


def resize_image(image_file, max_size=(1500, 1500), quality=90, max_file_size_kb=500):
    # פתיחת התמונה המקורית
    img = Image.open(image_file)

    # בדיקת משקל הקובץ
    image_file.seek(0, os.SEEK_END)
    file_size_kb = image_file.tell() / 1024
    image_file.seek(0)  # חזרה לתחילת הקובץ

    # בדיקת גודל התמונה (רוחב או אורך)
    width, height = img.size
    if file_size_kb <= max_file_size_kb and width <= max_size[0] and height <= max_size[1]:
        return image_file  # אם הקובץ קטן או שווה ל-500 ק"ב והתמונה בגודל המקסימלי או פחות, מחזירים את התמונה המקורית

    # תיקון ה-orientation ושינוי גודל
    img = correct_orientation(img)
    img.thumbnail(max_size, Image.LANCZOS)

    # שמירה בתמונה באיכות נמוכה
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    buffer.seek(0)
    return buffer

@csrf_exempt
def add_photos(request):
    if request.method == 'POST':
        try:
            event_id = request.GET.get('event-id')
            event = Event.objects.get(id=event_id)

            upload_directory = os.path.join(main_dir, event.directory_path, f'photos_{event_id}')
            if not os.path.exists(upload_directory):
                os.makedirs(upload_directory)

            index = EventImage.objects.filter(event=event).count()
            for key in request.FILES:
                image = request.FILES[key]
                resized_image = resize_image(image)

                image_path = os.path.join(upload_directory, f'img_{index}.jpg')
                with open(image_path, 'wb') as destination:
                    destination.write(resized_image.read())

                EventImage.objects.create(path=image_path, event=event)
                index += 1

            return JsonResponse({'status': 'success', 'message': 'Images uploaded successfully!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error occurred: {str(e)}'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)