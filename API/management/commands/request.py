import requests
from django.core.management.base import BaseCommand
import json
from django.conf import settings
import zipfile
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from API.FakeUA import FakeAgent
import os
from bs4 import BeautifulSoup


class Web:
    def __init__(self, ip, capabilities, js_render, json_mode, user_agent=FakeAgent().get_agent(),
                 url="https://www.google.com/", proxy=None):
        self.page = ""
        self.status = 0
        self.headers = ""
        self.cookies = []
        self.user_agent = user_agent
        self.js_status = False
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
                with zipfile.ZipFile('temp/proxy_auth_plugin.zip', 'w') as zp:
                    zp.writestr("manifest.json", manifest_json)
                    zp.writestr("background.js", background_js)
                options.add_extension('temp/proxy_auth_plugin.zip')

            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            #options.add_extension('extensions/canvas_extension.crx')
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            if js_render:
                options.add_argument("--enable-javascript")
            else:
                options.add_experimental_option("prefs", {'profile.managed_default_content_settings.javascript': 2})
            options.add_argument("--window-size=1920,1080")
            options.add_argument('--user-agent=%s' % self.user_agent)
            self.driver = webdriver.Remote(
                command_executor=f'http://{ip}:4444/wd/hub',
                desired_capabilities=capabilities,
                options=options
            )
            self.actions = webdriver.ActionChains(self.driver)
            if proxy:
                os.remove('temp/proxy_auth_plugin.zip')

            self.driver.get(url)
            self.status = 0
            self.headers = self.driver.execute_script("var req = new XMLHttpRequest();req.open('GET', document.location, false);req.send(null);return req.getAllResponseHeaders()")
            self.headers = self.headers.splitlines()
            self.page = self.driver.page_source
            self.cookies = self.driver.get_cookies()

            if json_mode and self.page != "":
                soup = BeautifulSoup(self.page, 'lxml')
                pre = soup.find_all('pre')
                if bool(len(pre)):
                    self.page = json.loads(soup.find('pre').text)
                    self.js_status = True
        finally:
            self.driver.close()
            self.driver.quit()

    def get_status_code(self):
        return self.status

    def get_page(self):
        return self.page

    def get_cookies(self):
        return self.cookies

    def get_headers(self):
        return self.headers

    def get_agent(self):
        return self.user_agent

    def get_js_status(self):
        return self.js_status


capabilities = {
    "browserName": "chrome",
    "browserVersion": "100.0",
    "selenoid:options": {
        "enableVNC": True,
        "enableVideo": False
    }
}


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
            change_proxy_url = settings.CHANGE_PROXY_URL
            session = Web(
                ip=settings.SERVER_IP,
                url=link,
                json_mode=json_mode,
                capabilities=capabilities,
                proxy=settings.PROXY,
                js_render=js_render
            )
            if change_proxy_url != "":
                requests.get(change_proxy_url)
            return session.get_page(),\
                   session.get_status_code(),\
                   session.get_cookies(),\
                   session.get_headers(),\
                   session.get_agent(), \
                   session.get_js_status()

        if url:
            result, status, cookies, headers, u_agent, js_render = HTMLrender(url, json_mode, js_render)
            #temp = {}
            #for item in headers.items():
            #    key, value = item
            #    temp[key] = value
            #headers = temp
            #temp = {}
            #for item in cookies.items():
            #    key, value = item
            #    temp[key] = value
            #cookies = temp

            data = {
                    "url": url,
                    "status_code": status,
                    "user_agent": u_agent,
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
