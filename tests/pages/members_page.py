class MembersPage:
    def __init__(self, page):
        self.page = page

    def invite_member(self, name, email, role="MEMBER"):
        self.page.click("#btn-invite-member")
        self.page.fill("#invite-name", name)
        self.page.fill("#invite-email", email)
        self.page.select_option("#invite-role", value=role)
        self.page.click("#btn-submit-invite")

    def member_row(self, email):
        return self.page.locator("#members-list").get_by_text(email)