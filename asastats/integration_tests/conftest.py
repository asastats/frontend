import os
import subprocess
import tempfile
import time

import pytest
import requests
from django.conf import settings

TEST_ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"

# Confirm against the engine's manage.py setdefault. Your frontend uses a settings
# *package* (asastats.settings.development), so the engine is almost certainly the
# same shape — NOT the bare "engine.settings", which loads an empty package.
BACKEND_SETTINGS_MODULE = "engine.settings"
BACKEND_URL = "http://127.0.0.1:8001"


@pytest.fixture(scope="session", autouse=True)
def backend_server():
    """Start the engine on :8001 with its OWN environment for integration tests.

    The engine loads its own .env (cwd is the engine dir); we deliberately do not
    inherit the frontend's environment, because load_dotenv() will not override
    vars already present in the process and the frontend's DB/Redis/settings would
    win. Only SIMPLE_JWT_KEY is forced, so JWTs minted by the frontend validate on
    the backend.
    """
    backend_python = os.path.expanduser("~/dev/venvs/backend/bin/python")
    backend_manage = os.path.expanduser("~/dev/backend/engine/manage.py")
    backend_dir = os.path.expanduser("~/dev/backend/engine/")

    if not os.path.exists(backend_python):
        pytest.fail(f"Backend Python executable not found at: {backend_python}")

    backend_env = {
        "PATH": os.environ["PATH"],
        "HOME": os.environ["HOME"],
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "DJANGO_SETTINGS_MODULE": BACKEND_SETTINGS_MODULE,
        "SIMPLE_JWT_KEY": settings.SIMPLE_JWT_KEY,
    }
    if "VIRTUAL_ENV" in os.environ:
        backend_env["VIRTUAL_ENV"] = os.path.expanduser("~/dev/venvs/backend")

    log = tempfile.NamedTemporaryFile(mode="w+", suffix=".backend.log", delete=False)
    process = subprocess.Popen(
        [backend_python, backend_manage, "runserver", "8001", "--noreload"],
        env=backend_env,
        cwd=backend_dir,
        stdout=log,
        stderr=subprocess.STDOUT,
    )

    def _fail(reason):
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        log.flush()
        with open(log.name) as handle:
            output = handle.read()
        pytest.fail(f"{reason}\n--- backend output ---\n{output}")

    deadline = time.time() + 20
    while time.time() < deadline:
        if process.poll() is not None:
            _fail(f"Backend exited during startup (code {process.returncode}).")
        try:
            requests.get(f"{BACKEND_URL}/api/v2/{TEST_ADDRESS}/", timeout=1)
            break
        except requests.ConnectionError:
            time.sleep(0.5)
    else:
        _fail("Backend server failed to respond in time.")

    yield BACKEND_URL

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
