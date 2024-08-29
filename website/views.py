import os
import threading

from django.http import HttpResponse,JsonResponse
from core.models import Event, EventImage
from django.views.decorators.csrf import csrf_exempt
from face_classification.views import classify_faces



main_dir = "C:\\AiuaPhoto\\"
def home(request):
    return HttpResponse("Welcome to the home page")

def about(request):
    return HttpResponse("This is the about page")

def get_events(request):
    events = Event.objects.all()
    events_list = list(events.values())  # המרת ה-QuerySet לרשימה של מילונים
    return JsonResponse(events_list, safe=False)


@csrf_exempt
def add_photos(request):
    if request.method == 'POST':
        try:
            event_id = request.GET.get('event-id')  # קבלת ה-ID של האירוע מה-Query Parameters
            event = Event.objects.get(id=event_id)

            upload_directory = os.path.join(main_dir, event.directory_path, f'photos_{event_id}')

            if not os.path.exists(upload_directory):
                os.makedirs(upload_directory)

            index = EventImage.objects.filter(event=event).count()
            paths = []
            for key in request.FILES:
                image = request.FILES[key]
                image_path = os.path.join(upload_directory, f'img_{index}.JPG')
                paths.append(image_path)
                index += 1

                # שמירת הקובץ בתיקיה
                with open(image_path, 'wb+') as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)

                # שמירת נתיב התמונה בבסיס הנתונים
                event_image = EventImage(path=image_path, event=event)
                event_image.save()

            thread = threading.Thread(target=classify_faces, args=(event, paths))
            thread.start()


            # אם הכל עבר בהצלחה
            return JsonResponse({'status': 'success', 'message': 'Images uploaded successfully!'})

        except Exception as e:
            # טיפול בשגיאה והחזרת תגובה
            return JsonResponse({'status': 'error', 'message': f'Error occurred: {str(e)}'}, status=500)

    # אם הבקשה אינה POST
    return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)