import pytest
import requests

from api_helpers import first_project_id, login
from pages.login_page import LoginPage


@pytest.fixture(scope="session", autouse=True)
def server_is_running():
    """Stop early with a clear message if the FlowSuite server is not up."""
    try:
        requests.get("http://localhost:3001/health", timeout=3)
    except requests.exceptions.RequestException:
        pytest.exit("FlowSuite server is not running. Start it with: npm start", returncode=2)


# ---- UI fixture (Playwright) ----

@pytest.fixture
def logged_in_page(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login("owner@acme.test", "password123")
    return page


# ---- API users (each login happens once per test run) ----

@pytest.fixture(scope="session")
def acme_owner():
    return login("owner@acme.test", "Acme Inc")


@pytest.fixture(scope="session")
def acme_admin():
    return login("admin@acme.test", "Acme Inc")


@pytest.fixture(scope="session")
def globex_owner():
    return login("owner@globex.test", "Globex Corp")


@pytest.fixture(scope="session")
def globex_member():
    return login("member@globex.test", "Globex Corp")


# ---- Seeded project ids (used by the multi-tenancy tests) ----

@pytest.fixture(scope="session")
def acme_project_id(acme_owner):
    return first_project_id(acme_owner, acme_owner["org_id"])


@pytest.fixture(scope="session")
def globex_project_id(globex_owner):
    return first_project_id(globex_owner, globex_owner["org_id"])