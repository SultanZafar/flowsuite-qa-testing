class ProjectsPage:
    def __init__(self, page):
        self.page = page

    def create_project(self, name):
        self.page.once("dialog", lambda dialog: dialog.accept(name))
        self.page.click("#btn-new-project")

    def cancel_create_project(self):
        self.page.once("dialog", lambda dialog: dialog.dismiss())
        self.page.click("#btn-new-project")

    def project_card(self, name):
        return self.page.get_by_text(name)

    def project_list(self):
        return self.page.locator("[data-testid='project-list']")