import logging
import os
import platform
import shutil
import time
import traceback
from contextlib import contextmanager
from datetime import datetime

from django.conf import settings
from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
    SESSION_KEY,
    get_user_model,
)
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.utils import override_settings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

SCREEN_DUMP_LOCATION = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "screendumps"
)

# Seconds to sleep in sleep method
DEFAULT_SLEEP = 0.25

# # Change browser driver here
BROWSER_DRIVER = "Chrome"
# BROWSER_DRIVER = 'Firefox'
# BROWSER_DRIVER = 'Opera'

# # Change headless driver here
# HEADLESS_DRIVER = None
HEADLESS_DRIVER = "browser"
# HEADLESS_DRIVER = 'pyvirtualdisplay'
# HEADLESS_DRIVER = 'xvfbwrapper'

# # Change headless backand here - used only by pyvirtualdisplay
HEADLESS_BACKEND = "xvfb"
# HEADLESS_BACKEND = 'xephyr'

TESTING_ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"


@contextmanager
def captured_server_errors():
    """Collect what Django logs to ``django.request`` while the block runs.

    The live server runs in a thread of this process with ``DEBUG`` off, so a
    view that raises renders templates/500.html -- inline CSS, no stylesheet
    links, and no traceback anywhere the browser can see it. The only symptom
    from the browser's side is a page that looks oddly bare. The exception does
    reach this logger, so an assertion can carry it.
    """
    records = []
    handler = logging.Handler()
    handler.emit = records.append
    logger = logging.getLogger("django.request")
    logger.addHandler(handler)
    try:
        yield records
    finally:
        logger.removeHandler(handler)


def describe_errors(records):
    """Render captured log records, with tracebacks, for a failure message."""
    if not records:
        return ""
    out = ["", "  the server logged:"]
    for record in records:
        out.append(f"    {record.getMessage()}")
        if record.exc_info:
            for line in traceback.format_exception(*record.exc_info):
                out.extend("      " + part for part in line.rstrip().splitlines())
    return "\n".join(out)


@override_settings(
    DEBUG_TOOLBAR_CONFIG={
        "SHOW_TOOLBAR_CALLBACK": lambda r: False,
    },
    CSRF_COOKIE_SECURE=False,
    SESSION_COOKIE_SECURE=False,
)
class Setup(StaticLiveServerTestCase):
    """Initial setup methods for functional tests base class"""

    browser_driver = BROWSER_DRIVER
    headless_driver = HEADLESS_DRIVER

    def setUp(self):
        self.setup_platform()
        self.setup_headless()

        self.run_driver()

        if self.headless_driver == "xvfbwrapper":
            self.addCleanup(self.browser.quit)

        # staging_server = os.environ.get('STAGING_SERVER')
        # if staging_server:
        #     self.live_server_url = 'https://' + staging_server
        self.server_url = self.live_server_url

    def tearDown(self):
        if self.headless_driver not in (None, "browser"):
            self.display.stop()

        if self._test_has_failed():
            if not os.path.exists(SCREEN_DUMP_LOCATION):
                os.makedirs(SCREEN_DUMP_LOCATION)

            for ix, handle in enumerate(self.browser.window_handles):
                self._windowid = ix
                self.browser.switch_to.window(handle)
                self.take_screenshot()
                self.dump_html()

        self.browser.quit()
        super().tearDown()

    def setup_platform(self):
        if self.browser_driver == "Chrome":
            self.browser_class = webdriver.Chrome
            self.browser_options = ChromeOptions()
            self.browser_options.add_argument("--disable-extensions")
            self.browser_options.add_argument("--no-sandbox")
            self.browser_options.add_argument("--no-default-browser-check")
            self.browser_options.add_argument("--no-first-run")
            self.browser_options.add_argument("--disable-default-apps")
            self.browser_options.add_argument("--allow-running-insecure-content")
            self.browser_options.add_argument("--ignore-certificate-errors")

        elif self.browser_driver == "Firefox":
            self.browser_class = webdriver.Firefox
            self.firefox_profile = webdriver.FirefoxProfile()
            self.firefox_profile.set_preference(
                "browser.startup.homepage_override.mston‌​e", "ignore"
            )
            self.firefox_profile.set_preference(
                "startup.homepage_welcome_url.additional‌​", "about:blank"
            )
            self.firefox_profile.set_preference(
                "browser.shell.checkDefaultBrowser", False
            )
            self.firefox_profile.set_preference("browser.download.folderList", 2)
            self.firefox_profile.set_preference(
                "browser.download.manager.showWhenStarting", False
            )
            self.firefox_profile.set_preference(
                "browser.helperApps.neverAsk.saveToDisk", "text/csv"
            )
            self.firefox_profile.accept_untrusted_certs = True

        elif self.browser_driver == "Opera":
            self.opera_capabilities = DesiredCapabilities.OPERA
            self.opera_capabilities["chromedriverExecutable"] = (
                "/home/ipaleka/opt/bin/operadriver"
            )
            self.opera_capabilities["app"] = "/usr/bin/opera"
            self.browser_class = webdriver.Opera

    def setup_headless(self):
        if self.headless_driver is None:
            return False

        if self.headless_driver == "browser":
            if self.browser_driver == "Chrome":
                self.browser_options.add_argument("--headless")
            elif self.browser_driver == "Firefox":
                os.environ["MOZ_HEADLESS"] = "1"
            return False

        if self.headless_driver == "xvfbwrapper":
            from xvfbwrapper import Xvfb

            self.display = Xvfb(width=1600, height=1280, colordepth=16)
            self.addCleanup(self.display.stop)
            self.display.start()

        elif self.headless_driver == "pyvirtualdisplay":
            from pyvirtualdisplay import Display

            self.display = Display(
                backend=HEADLESS_BACKEND, visible=0, size=(1600, 1280)
            )

        self.display.start()
        return None

    def run_driver(self):
        if self.browser_driver == "Chrome":
            # Detect if running on Linux ARM64 (like the Raspberry Pi 5)
            is_arm_linux = (
                platform.system() == "Linux"
                and platform.machine().lower() in ("aarch64", "arm64")
            )

            if is_arm_linux:
                # Bypass Selenium Manager and use the system-installed chromedriver
                # shutil.which automatically finds it if it's in your system PATH
                driver_path = shutil.which("chromedriver") or "/usr/bin/chromedriver"
                service = ChromeService(executable_path=driver_path)
                self.browser = self.browser_class(
                    service=service, options=self.browser_options
                )
            else:
                # Standard initialization: uses Selenium Manager on x86_64 Linux, Mac, or Windows
                self.browser = self.browser_class(options=self.browser_options)

        elif self.browser_driver == "Firefox":
            self.browser = self.browser_class(firefox_profile=self.firefox_profile)

        elif self.browser_driver == "Opera":
            self.browser = self.browser_class(capabilities=self.opera_capabilities)

        self.browser.implicitly_wait(2)
        self.browser.set_window_size(1280, 1024)


class FunctionalTest(Setup):
    """Functional tests base class with attached helpers methods"""

    def accept_cookie(self):
        pass
        # button = self.browser.find_element(By.CLASS_NAME, "accept-all")
        # button.click()
        # self.sleep(0.1)

    def sleep(self, seconds=DEFAULT_SLEEP):
        time.sleep(seconds)

    def find_elem_by_id(self, elem_id):
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.ID, elem_id))
        )
        return self.browser.find_element(By.ID, elem_id)

    def find_elem_by_tag(self, elem_tag):
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, elem_tag))
        )
        return self.browser.find_element(By.TAG_NAME, elem_tag)

    def find_elems_by_tag(self, elem_tag):
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, elem_tag))
        )
        return self.browser.find_elements(By.TAG_NAME, elem_tag)

    def find_elem_by_link_text(self, elem_text):
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.LINK_TEXT, elem_text))
        )
        return self.browser.find_element(By.LINK_TEXT, elem_text)

    def find_elem_by_class(self, class_name):
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, class_name))
        )
        return self.browser.find_element(By.CLASS_NAME, class_name)

    def find_elems_by_class(self, class_name):
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, class_name))
        )
        return self.browser.find_elements(By.CLASS_NAME, class_name)

    def find_elem_by_css(self, selector):
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return self.browser.find_element(By.CSS_SELECTOR, selector)

    def find_elems_by_css(self, selector):
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return self.browser.find_elements(By.CSS_SELECTOR, selector)

    def wait_until(self, predicate, timeout=5):
        """Block until `predicate()` returns something truthy, and return it.

        For state that no `expected_conditions` helper covers -- an attribute
        settling, a JS-driven re-render -- where polling beats a fixed sleep.
        """
        return WebDriverWait(self.browser, timeout).until(lambda _: predicate())

    def page_state(self):
        """Return {ready, sheets, title, text} for the current page in one call.

        One ``execute_script`` round trip rather than a Selenium query per
        element: every ``find_elements`` pays the implicit wait, which adds up
        across a test that walks several pages.
        """
        return self.browser.execute_script(
            "return {"
            "  ready: document.readyState,"
            "  sheets: Array.from("
            "    document.querySelectorAll('link[rel=\"stylesheet\"]')"
            "  ).map(function (l) { return l.getAttribute('href'); }),"
            "  title: document.title,"
            "  text: (document.body ? document.body.innerText : '').slice(0, 300)"
            "};"
        )

    def visit(self, url):
        """Load ``url``, wait for it to settle, and describe what arrived.

        The returned state carries a ``why`` string holding everything a
        failure needs to name itself -- url, title, a body excerpt, and the
        server-side traceback if the view raised.
        """
        with captured_server_errors() as errors:
            self.browser.get(url)
            self.wait_until(lambda: self.page_state()["ready"] == "complete")
            state = self.page_state()
        state["why"] = (
            f"\n  url:   {url}"
            f"\n  title: {state['title']!r}"
            f"\n  body:  {state['text']!r}" + describe_errors(errors)
        )
        return state

    def record_javascript_errors(self):
        """Install an error recorder that survives navigation.

        Call once, before the first ``get()``. Every page loaded afterwards
        starts with a ``window.__jsErrors`` array that collects uncaught
        exceptions and unhandled rejections, so ``javascript_errors()`` can
        report what a page threw while it was loading -- which is the part a
        test arriving after the fact can never see.
        """
        self.browser.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": "window.__jsErrors = [];"
                "window.addEventListener('error', function (e) {"
                "  window.__jsErrors.push(String(e.message) + '  (' +"
                "    String(e.filename).split('/').pop() + ':' + e.lineno + ')');"
                "});"
                "window.addEventListener('unhandledrejection', function (e) {"
                "  window.__jsErrors.push('unhandled rejection: ' + String(e.reason));"
                "});"
            },
        )

    def javascript_errors(self):
        """Return what the current page threw since it started loading."""
        return self.browser.execute_script("return window.__jsErrors || [];")

    def take_screenshot(self):
        filename = self._get_filename() + ".png"
        print("screenshotting to", filename)
        self.browser.get_screenshot_as_file(filename)

    def dump_html(self):
        filename = self._get_filename() + ".html"
        print("dumping page HTML to", filename)
        with open(filename, "w") as f:
            f.write(self.browser.page_source)

    def _test_has_failed(self):
        # for _, error in self._outcome.errors:
        #     if error:
        #         return True
        return False

    def _get_filename(self):
        timestamp = datetime.now().isoformat().replace(":", ".")[:19]
        return "{folder}/{clsname}.{method}-window{winid}-{timestamp}".format(
            folder=SCREEN_DUMP_LOCATION,
            clsname=self.__class__.__name__,
            method=self._testMethodName,
            winid=self._windowid,
            timestamp=timestamp,
        )

    def get_bundlename_input_box(self):
        return self.find_elem_by_id("id_name")

    def get_bundlename_addresses_input_box(self):
        return self.find_elem_by_id("id_addresses")

    def submit_bundlename_name(self, name, addresses):
        input_box = self.get_bundlename_input_box()
        input_box.send_keys(f"{name}")
        input_box = self.get_bundlename_addresses_input_box()
        input_box.send_keys(f"{addresses}")
        self.find_elem_by_id("id_submit").click()
        self.sleep()

    @contextmanager
    def wait_for_page_load(self, timeout=30):
        old_page = self.browser.find_element(By.TAG_NAME, "html")
        yield
        WebDriverWait(self.browser, timeout).until(EC.staleness_of(old_page))

    def check_for_entry_in_home_collection(self, name):
        cards = self.browser.find_elements(By.CLASS_NAME, "card-content")
        self.assertIn(
            name, [card.find_element(By.TAG_NAME, "span").text for card in cards]
        )

    def sign_new_user(self, email, password="password01"):
        self.browser.get(self.server_url + "/accounts/signup")
        self.find_elem_by_id("id_email").send_keys(email)
        self.find_elem_by_id("id_password1").send_keys("{}".format(password))
        with self.wait_for_page_load(timeout=5):
            self.find_elem_by_id("id_password2").send_keys("{}\n".format(password))

    def create_session_cookie(self, username, password, permission=100):
        # First, create a new test user
        user_model = get_user_model()
        user_model.objects.filter(username=username).delete()
        user = user_model.objects.create_user(username=username, password=password)
        if permission != 0:
            user.profile.permission = permission
            user.profile.address = TESTING_ADDRESS
            user.profile.authorized = (
                "H5G2PTZSXGRSWLMEAWE24DGJTIBSTHND3ANAVGEVROWOVBMCXULQ"
            )
            user.profile.save()

        # Then create the authenticated session using the new user credentials
        session = SessionStore()
        session[SESSION_KEY] = user.pk
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()

        # Finally, create the cookie dictionary
        cookie = {
            "name": settings.SESSION_COOKIE_NAME,
            "value": session.session_key,
            "secure": False,
            "path": "/",
        }
        return cookie

    def create_cookie_and_go_to_index_page_tier(self, email, permission=0):
        session_cookie = self.create_session_cookie(
            username=email, password="top_secret", permission=permission
        )

        # visit some url in your domain to setup Selenium.
        # (404 pages load the quickest)
        self.browser.get(self.server_url + "/404.html")

        # add the newly created session cookie to selenium webdriver.
        self.browser.add_cookie(session_cookie)

        # refresh to exchange cookies with the server.
        self.browser.refresh()

        # This time user should present as logged in.
        self.browser.get(self.server_url)

    def create_cookie_and_go_to_index_page(self, email):
        return self.create_cookie_and_go_to_index_page_tier(email, permission=0)

    def create_cookie_and_go_to_bundlename_add_page(self, email, permission=0):
        session_cookie = self.create_session_cookie(
            username=email, password="top_secret", permission=permission
        )

        # visit some url in your domain to setup Selenium.
        # (404 pages load the quickest)
        self.browser.get(self.server_url + "/404.html")

        # add the newly created session cookie to selenium webdriver.
        self.browser.add_cookie(session_cookie)

        # refresh to exchange cookies with the server.
        self.browser.refresh()

        # This time user should present as logged in.
        self.browser.get(self.server_url + "/profile/add-bundle")

    def create_cookie_and_go_to_authorize_page(self, email, address=TESTING_ADDRESS):
        session_cookie = self.create_session_cookie(
            username=email, password="top_secret", permission=0
        )

        # Give the user an unauthorized address so the authorize page is reachable
        user_model = get_user_model()
        user = user_model.objects.get(username=email)
        user.profile.address = address
        user.profile.save()

        # visit some url in your domain to setup Selenium.
        # (404 pages load the quickest)
        self.browser.get(self.server_url + "/404.html")

        # add the newly created session cookie to selenium webdriver.
        self.browser.add_cookie(session_cookie)

        # refresh to exchange cookies with the server.
        self.browser.refresh()

        # This time user should present as logged in, on the authorize page.
        self.browser.get(self.server_url + "/profile/authorize/")
