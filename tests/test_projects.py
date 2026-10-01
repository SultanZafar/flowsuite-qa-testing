import uuid
from playwright.sync_api import expect
from pages.projects_page import ProjectsPage


def unique_name(prefix="Test Project"):
    return f"{prefix}-{uuid.uuid4().hex[:6]}"


def test_tc07_create_project(logged_in_page):
    projects = ProjectsPage(logged_in_page)
    name = unique_name()
    projects.create_project(name)
    expect(projects.project_card(name)).to_be_visible()


def test_tc08_empty_project_name(logged_in_page):
    projects = ProjectsPage(logged_in_page)
    
    # 1. Wait for existing project cards to be visible on the page
    logged_in_page.wait_for_selector(".project-card")
    before = logged_in_page.locator(".project-card").count()

    # 2. Try creating a project with an empty name
    projects.create_project("")

    # 3. Give a short delay to ensure no new project card was created
    logged_in_page.wait_for_timeout(1000)
    after = logged_in_page.locator(".project-card").count()

    # 4. Verify that the total card count remains unchanged
    assert after == before


def test_tc09_duplicate_project_name(logged_in_page):
    projects = ProjectsPage(logged_in_page)
    name = unique_name()
    projects.create_project(name)
    projects.create_project(name)
    expect(logged_in_page.get_by_text(name)).to_have_count(2)


def test_tc10_project_persists_after_refresh(logged_in_page):
    projects = ProjectsPage(logged_in_page)
    name = unique_name()
    projects.create_project(name)
    logged_in_page.reload()
    expect(projects.project_card(name)).to_be_visible()


def test_tc11_open_project(logged_in_page):
    projects = ProjectsPage(logged_in_page)
    name = unique_name()
    projects.create_project(name)
    projects.project_card(name).click()
    expect(logged_in_page.locator("[data-testid='tab-project-detail']")).to_be_visible()


def test_tc12_free_plan_limit(logged_in_page):
    projects = ProjectsPage(logged_in_page)
    names = [unique_name(f"Limit-{i}") for i in range(4)]
    for name in names:
        projects.create_project(name)
    for name in names:
        expect(projects.project_card(name)).to_be_visible()
    # BUG: FREE plan ki limit "3 projects" hai, lekin app 4th ko block nahi karti


def test_tc13_projects_count_in_list(logged_in_page):
    projects = ProjectsPage(logged_in_page)
    name = unique_name()
    projects.create_project(name)
    expect(projects.project_list()).to_contain_text(name)