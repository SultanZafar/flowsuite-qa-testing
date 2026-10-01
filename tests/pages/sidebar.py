class Sidebar:
    def __init__(self, page):
        self.page = page

    def go_to_projects(self):
        self.page.click("[data-testid='nav-projects']")

    def go_to_members(self):
        self.page.click("[data-testid='nav-members']")

    def go_to_billing(self):
        self.page.click("[data-testid='nav-billing']")

    def switch_org(self, org_name):
        self.page.select_option("#org-select", label=org_name)

    def current_user_text(self):
        return self.page.locator("#current-user-name").text_content()

    def logout(self):
        self.page.click("#btn-logout")