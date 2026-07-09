from django.http import HttpResponse

def home(request):
    return HttpResponse("Hello Isaac! Django is working.")