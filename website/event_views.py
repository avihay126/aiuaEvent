import os
import io
import qrcode
import urllib.parse
import cv2
import numpy as np
from corsheaders.middleware import CorsMiddleware
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ExifTags
from django.views.decorators.http import require_POST
from django.http import FileResponse, Http404
from rest_framework.decorators import api_view
from constants import *

from core.models import Event, EventImage, Photographer
from thread_manager import submit_task
from face_classification.classify import classify_faces, event_locking
from django.core.exceptions import ValidationError
from datetime import datetime
import logging
import logging_config
from core.serializers import EventSerializer, PhotographerSerializer

logger = logging.getLogger(__name__)





@api_view(['GET'])
def get_events(request):
    photographer = get_token(request)
    events = Event.objects.filter(photographer=photographer)
    serializer = EventSerializer(events, many=True)
    return JsonResponse(serializer.data, safe=False, status=200)


@api_view(['GET'])
def get_user_details(request):
    photographer = get_token(request)
    serializer = PhotographerSerializer(photographer)
    return JsonResponse(serializer.data, safe=False, status=200)


def get_token(request):
    token = request.COOKIES.get('auth_token')

    if not token:
        return JsonResponse({'error': 'Authentication token missing'}, status=401)

    try:
        photographer = Photographer.objects.get(secret=token)
    except Photographer.DoesNotExist:
        return JsonResponse({'error': 'Invalid token or photographer not found'}, status=401)
    return photographer


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


def resize_image(image_file, max_size=(1500, 1500), quality=90, max_file_size_kb=500):
    with io.BytesIO(image_file.read()) as image_data:
        with Image.open(image_data) as img:
            image_data.seek(0, os.SEEK_END)
            file_size_kb = image_data.tell() / 1024
            image_data.seek(0)

            width, height = img.size
            if file_size_kb <= max_file_size_kb and width <= max_size[0] and height <= max_size[1]:
                image_data.seek(0)
                return io.BytesIO(image_data.getvalue())

            img = correct_orientation(img)
            img.thumbnail(max_size, Image.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            buffer.seek(0)

    return buffer


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

            with open(image_path, 'wb') as destination:
                destination.write(resized_image.getvalue())

            EventImage.objects.create(path=image_path, event=event)
            paths.append(image_path)
            index += 1

        submit_task(classify_faces, event, paths)
    except Exception as e:
        logger.error(f"Error processing images: {e}")


@csrf_exempt
def add_photos(request):
    if request.method == 'POST':
        try:
            event_id = request.GET.get('event-id')
            event = Event.objects.get(id=event_id)

            upload_directory = os.path.join(MAIN_DIR, "photographer_" + str(event.photographer.id),
                                            event.directory_path)
            if not os.path.exists(upload_directory):
                os.makedirs(upload_directory)

            index = EventImage.objects.filter(event=event).count()

            files_copy = {key: io.BytesIO(file.read()) for key, file in request.FILES.items()}
            submit_task(process_images, event, files_copy, upload_directory, index)

            return JsonResponse(
                {'status': 'success', 'message': 'Images uploaded successfully, processing in background!'})
        except Exception as e:
            logger.error(e)
            return JsonResponse({'status': 'error', 'message': f'Error occurred: {str(e)}'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)


@csrf_exempt
def create_event(request):
    try:

        name = request.POST.get('name')
        date_str = request.POST.get('date')
        location = request.POST.get('location')
        photographer = get_token(request)
        photographer_id = photographer.id

        if not name or not date_str or not location or not photographer_id:
            return JsonResponse({'error': 'All fields are required: name, date, location, photographer_id'}, status=400)

        try:
            date = set_date_format(date_str)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Expected format: dd/mm/yyyy'}, status=400)

        try:
            photographer = Photographer.objects.get(id=photographer_id)
        except Photographer.DoesNotExist:
            return JsonResponse({'error': 'Photographer with the provided ID does not exist'}, status=404)

        event = Event(name=name, date=date, location=location, photographer=photographer)
        event.save()
        event.directory_path = create_event_dir(event, photographer_id)
        event.qr_path = create_qr(event)
        event.save()
        events = Event.objects.filter(photographer=photographer)
        serializer = EventSerializer(events, many=True)

        return JsonResponse({'success': 'Event created successfully!', 'events': serializer.data}, status=201)

    except ValidationError as e:
        return JsonResponse({'error': f'Validation error: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


def create_event_dir(event, photographer_id):
    event_dir = f'event_{event.id}'
    path_to_dir = os.path.join(MAIN_DIR, f'photographer_{photographer_id}', event_dir)

    try:
        if not os.path.exists(path_to_dir):
            os.makedirs(path_to_dir)
        return event_dir
    except Exception as e:
        logger.error(f"Error creating directory for event {event.id}: {e}")
        return None


def create_qr(event):
    phone_number = QR_PHONE
    message = f"היי AIUA, אפשר לקבל בבקשה את התמונות שלי מ{event.name} בתאריך {event.date}?"
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(whatsapp_url)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white').convert('RGB')
    img = np.array(img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    if not os.path.exists(QRS_DIR):
        os.makedirs(QRS_DIR)
    file_path = os.path.join(QRS_DIR, f'event_{event.id}_whatsapp_qr.png')
    cv2.imwrite(file_path, img)
    print(f"QR SAVED! {file_path}")
    return file_path


def get_qr(request):
    try:
        event_id = request.GET.get('event-id')
        event = Event.objects.get(id=event_id)
        qr_path = event.qr_path
        if os.path.exists(qr_path):
            return FileResponse(open(qr_path, 'rb'), content_type='image/jpeg')
        else:
            raise Http404('Image not found')
    except Event.DoesNotExist:
        raise Http404('Event not found')


def set_date_format(date_str):
    date_lst = date_str.split('-')
    date = date_lst[2] + "/" + date_lst[1] + "/" + date_lst[0]
    return date


@api_view(['GET'])
def lock_event(request):
    try:
        event_id = request.GET.get('event-id')
        event = Event.objects.get(id=event_id)
        submit_task(event_locking, event)
        event.is_open = False
        event.save()
        serializer = EventSerializer(event).data
        return JsonResponse({'success': 'event locked', 'event': serializer}, status=201)
    except Exception as e:
        return JsonResponse({'error': 'action faild'}, status=401)


