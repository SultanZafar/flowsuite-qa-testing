from playwright.sync_api import expect
from pages.sidebar import Sidebar
from pages.members_page import MembersPage


def test_tc18_view_members_list(logged_in_page):
    sidebar = Sidebar(logged_in_page)
    sidebar.go_to_members()
    expect(logged_in_page.locator("[data-testid='tab-members']")).to_be_visible()


def test_tc19_invite_member(logged_in_page):
    sidebar = Sidebar(logged_in_page)
    sidebar.go_to_members()
    members = MembersPage(logged_in_page)
    members.invite_member("New User", "newuser@acme.test")
    expect(members.member_row("newuser@acme.test")).to_be_visible()


def test_tc20_invite_invalid_email(logged_in_page):
    sidebar = Sidebar(logged_in_page)
    sidebar.go_to_members()
    members = MembersPage(logged_in_page)
    members.invite_member("Bad Email", "not-an-email")
    # TODO: is app mein invalid email par kya hota hai, haath se check karke likhein


def test_tc21_invite_duplicate_email(logged_in_page):
    sidebar = Sidebar(logged_in_page)
    sidebar.go_to_members()
    members = MembersPage(logged_in_page)
    members.invite_member("Owner Again", "owner@acme.test")
    expect(logged_in_page.locator("#toast")).to_be_visible()


def test_tc22_owner_role_visible(logged_in_page):
    sidebar = Sidebar(logged_in_page)
    sidebar.go_to_members()
    expect(
        logged_in_page.locator("select.role-select option[value='OWNER'][selected]")
    ).to_have_count(1)