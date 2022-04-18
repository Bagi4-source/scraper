import requests
from django.core.management.base import BaseCommand
from requests_html import HTMLSession
import json
from django.conf import settings
import zipfile
import time
from selenium import webdriver
from API.FakeUA import FakeAgent


class Web:
    def __init__(self, ip, capabilities, user_agent=FakeAgent().get_agent(), url="https://www.google.com/", proxy=None):
        try:
            options = webdriver.ChromeOptions()

            if proxy:
                manifest_json = """
                        {
                            "version": "1.0.0",
                            "manifest_version": 2,
                            "name": "Chrome Proxy",
                            "permissions": [
                                "proxy",
                                "tabs",
                                "unlimitedStorage",
                                "storage",
                                "<all_urls>",
                                "webRequest",
                                "webRequestBlocking"
                            ],
                            "background": {
                                "scripts": ["background.js"]
                            },
                            "minimum_chrome_version":"22.0.0"
                        }
                        """
                background_js = """
                        var config = {
                                mode: "fixed_servers",
                                rules: {
                                singleProxy: {
                                    scheme: "http",
                                    host: "%s",
                                    port: parseInt(%s)
                                },
                                bypassList: ["localhost"]
                                }
                            };

                        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

                        function callbackFn(details) {
                            return {
                                authCredentials: {
                                    username: "%s",
                                    password: "%s"
                                }
                            };
                        }

                        chrome.webRequest.onAuthRequired.addListener(
                                    callbackFn,
                                    {urls: ["<all_urls>"]},
                                    ['blocking']
                        );
                        """ % proxy
                with zipfile.ZipFile('extensions/proxy_auth_plugin.zip', 'w') as zp:
                    zp.writestr("manifest.json", manifest_json)
                    zp.writestr("background.js", background_js)
                options.add_extension('extensions/proxy_auth_plugin.zip')

            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_extension('extensions/canvas_extension.crx')
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--enable-javascript")
            options.add_argument("--window-size=1920,1080")
            options.add_argument('--user-agent=%s' % user_agent)
            self.driver = webdriver.Remote(
                command_executor=f'http://{ip}:4444/wd/hub',
                desired_capabilities=capabilities,
                options=options
            )
            self.actions = webdriver.ActionChains(self.driver)
            #if proxy:
                #os.remove('extensions/proxy_auth_plugin.zip')

            self.driver.get(url)
            time.sleep(3)
        except Exception as _ex:
            print(_ex)

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
            proxy = settings.PROXY
            change_proxy_url = settings.CHANGE_PROXY_URL
            proxies = {'http': proxy, 'https': proxy}
            session = HTMLSession()
            r = session.get(link)
            if r.status_code == 200 and js_render:
                r.html.render(sleep = 10)
            session.close()
            if change_proxy_url != "":
                requests.get(change_proxy_url)
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
                        "js_render": js_render,
                        "advanced": advanced,
                    },
                }
            if advanced:
                data["headers"] = headers
                data["cookies"] = cookies

            data["result"] = result

            with open(file=f"temp/{name}.json", mode="w") as f:
                f.write(json.dumps(data))
