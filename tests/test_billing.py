from playwright.sync_api import expect
from pages.sidebar import Sidebar
from pages.billing_page import BillingPage


def test_tc23_view_current_plan(logged_in_page):
    sidebar = Sidebar(logged_in_page)
    sidebar.go_to_billing()
    expect(logged_in_page.locator("[data-testid='tab-billing']")).to_be_visible()


def test_tc24_plan_limits_visible(logged_in_page):
    sidebar = Sidebar(logged_in_page)
    sidebar.go_to_billing()
    billing = BillingPage(logged_in_page)
    expect(billing.plan_card("FREE")).to_be_visible()
    expect(billing.plan_card("PRO")).to_be_visible()


def test_tc25_upgrade_button_exists(logged_in_page):
    sidebar = Sidebar(logged_in_page)
    sidebar.go_to_billing()
    expect(logged_in_page.locator("[data-testid='btn-select-plan-PRO']")).to_be_visible()