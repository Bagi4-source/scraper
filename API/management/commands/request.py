from django.core.management.base import BaseCommand
from requests_html import HTMLSession
import json


class Command(BaseCommand):
    help = 'Request'

    def add_arguments(self, parser):
        parser.add_argument('url', nargs='+', type=str)
        parser.add_argument('name', nargs='+', type=str)
        parser.add_argument('json_mode', nargs='+', type=int)
        parser.add_argument('js_render', nargs='+', type=int)
        parser.add_argument('advanced', nargs='+', type=int)

    def handle(self, *args, **options):
        url = options['url'][0]
        name = options['name'][0]
        json_mode = bool(options['json_mode'][0])
        js_render = bool(options['js_render'][0])
        advanced = bool(options['advanced'][0])

        def HTMLrender(link, json_mode=False, js_render=False):
            username, password, ip, port = "j25Ak4", "UK046Q", "46.232.10.21", "8000"
            proxy = f'http://{username}:{password}@{ip}:{port}'
            print(proxy)
            proxies = {'http': proxy, 'https': proxy}
            session = HTMLSession()
            r = session.get(link, proxies=proxies)
            if r.status_code == 200 and js_render:
                r.html.render(timeout=30)
            session.close()
            if json_mode:
                return r.json(), r.status_code, r.headers, r.cookies
            return r.html.html, r.status_code, r.headers, r.cookies

        if url:
            result, status, headers, cookies = HTMLrender(url, json_mode, js_render)
            temp = {}
            for item in headers.items():
                key, value = item
                temp[key] = value
            headers = temp
            temp = {}
            for item in cookies.items():
                key, value = item
                temp[key] = value
            cookies = temp

            data = {
                    "url": url,
                    "status": status,
                    "params": {
                        "json": json_mode,
                        "render_js": js_render,
                        "advanced": advanced,
                    },
                }
            if advanced:
                data["headers"] = headers
                data["cookies"] = cookies

            data["result"] = result

            with open(file=f"temp/{name}.json", mode="w") as f:
                f.write(json.dumps(data))