from playwright.sync_api import expect
from pages.login_page import LoginPage


def test_tc14_acme_login_shows_acme_org(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login("owner@acme.test", "password123")
    expect(page.locator("#org-select")).to_contain_text("Acme Inc")


def test_tc15_globex_login_shows_globex_org(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login("owner@globex.test", "password123")
    expect(page.locator("#org-select")).to_contain_text("Globex Corp")


def test_tc16_acme_cannot_see_globex_project(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login("owner@acme.test", "password123")
    expect(page.get_by_text("Q4 Marketing Campaign")).not_to_be_visible()


def test_tc17_org_select_only_shows_own_org(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login("owner@acme.test", "password123")
    expect(page.locator("#org-select")).not_to_contain_text("Globex Corp")