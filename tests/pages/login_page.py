class LoginPage:
    def __init__(self, page):
        self.page = page

    def open(self):
        self.page.goto("http://localhost:3001/")

    def login(self, email, password):
        self.page.fill("#login-email", email)
        self.page.fill("#login-password", password)
        self.page.click("#btn-login")
        



