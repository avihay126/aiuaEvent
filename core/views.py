from django.http import HttpResponse

def event_list(request):
    return HttpResponse("This is the list of events")
