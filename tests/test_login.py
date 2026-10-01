from playwright.sync_api import expect
from pages.login_page import LoginPage

def test_tc01_valid_login(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login("owner@globex.test", "password123")
    expect(page.get_by_role("heading", name="Projects")).to_be_visible()

def test_tc02_wrong_password(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login("owner@acme.test", "wrong-password")
    expect(page.locator("#login-error")).to_be_visible()


def test_tc03_wrong_email(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login("nobody@acme.test", "password123")
    expect(page.locator("#login-error")).to_be_visible()


def test_tc04_empty_email(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login("", "password123")
    expect(page.locator("#login-error")).to_be_visible()


def test_tc05_empty_password(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login("owner@acme.test", "")
    expect(page.locator("#login-error")).to_be_visible()


def test_tc06_empty_both(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login("", "")
    expect(page.locator("#login-error")).to_be_visible()

    