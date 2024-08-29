from django.http import HttpResponse

def some_view(request):
    return HttpResponse("This is a response from bot app")
