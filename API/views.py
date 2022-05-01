import json
import time
import random
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from threading import Thread


def Request(request):
    data = request.GET
    url = data.get("url")
    json_mode = 0
    if str(data.get("json")).lower() == "true":
        json_mode = 1

    js_render = 0
    if str(data.get("js_render")).lower() == "true":
        js_render = 1

    advanced = 0
    if str(data.get("advanced")).lower() == "true":
        advanced = 1

    result = ""
    name = random.getrandbits(128)

    os.system(f'python3 manage.py request "{url}" "{name}" {json_mode} {js_render} {advanced}')

    k = 0
    while not os.path.isfile(f"temp/{name}.json") and k <= 150:
        time.sleep(0.3)
        k += 1

    if os.path.isfile(f"temp/{name}.json"):
        with open(f"temp/{name}.json", "r") as File:
            result = json.loads(File.read())
        os.remove(f"temp/{name}.json")
    return JsonResponse(result)


def Home(request):
    def get_client_ip(r):
        x_forwarded_for = r.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return r.META.get('REMOTE_ADDR')

    ip = get_client_ip(request)
    context = {
        'ip': ip,
    }
    return render(request, 'API/templates/API/index.html', context=context)
