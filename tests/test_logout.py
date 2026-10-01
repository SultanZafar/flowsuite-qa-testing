from playwright.sync_api import expect
from pages.sidebar import Sidebar
from pages.login_page import LoginPage


def test_tc26_logout_redirects_to_login(logged_in_page):
    sidebar = Sidebar(logged_in_page)
    sidebar.logout()
    expect(logged_in_page.locator("#form-login")).to_be_visible()


def test_tc27_after_logout_protected_page_blocked(logged_in_page):
    sidebar = Sidebar(logged_in_page)
    sidebar.logout()
    logged_in_page.goto("http://localhost:3001/")
    expect(logged_in_page.locator("#form-login")).to_be_visible()


def test_tc28_login_after_logout(logged_in_page):
    sidebar = Sidebar(logged_in_page)
    sidebar.logout()
    login_page = LoginPage(logged_in_page)
    login_page.login("owner@acme.test", "password123")
    expect(logged_in_page.get_by_role("heading", name="Projects", exact=True)).to_be_visible()