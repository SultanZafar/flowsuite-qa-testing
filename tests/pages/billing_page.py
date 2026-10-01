class BillingPage:
    def __init__(self, page):
        self.page = page

    def plan_card(self, plan):
        # plan = "FREE" ya "PRO"
        return self.page.locator(f"[data-testid='plan-card-{plan}']")

    def select_plan(self, plan):
        self.page.click(f"[data-testid='btn-select-plan-{plan}']")