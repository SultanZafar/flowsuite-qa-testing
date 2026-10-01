import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "app.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def test_tc56_can_connect_and_list_tables():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cursor.fetchall()]
    conn.close()
    assert tables, "No tables found"


def test_tc57_passwords_are_hashed_not_plaintext():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email, password_hash FROM Users")
    rows = cursor.fetchall()
    conn.close()
    assert rows, "No users found"
    for row in rows:
        assert row["password_hash"] != "password123", (
            f"BUG-10: password stored in plaintext for {row['email']}"
        )
        assert len(row["password_hash"]) > 20, (
            f"password_hash too short to be a real hash for {row['email']}"
        )


def test_tc58_no_orphan_projects():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.project_id, p.org_id FROM Projects p
        LEFT JOIN Organizations o ON p.org_id = o.org_id
        WHERE o.org_id IS NULL
    """)
    orphans = cursor.fetchall()
    conn.close()
    assert not orphans, f"Orphan projects with no matching org: {[dict(r) for r in orphans]}"


def test_tc59_each_org_has_exactly_one_owner():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT org_id, COUNT(*) as owner_count
        FROM Memberships
        WHERE role = 'OWNER'
        GROUP BY org_id
    """)
    rows = cursor.fetchall()
    conn.close()
    bad = [dict(r) for r in rows if r["owner_count"] != 1]
    assert not bad, f"BUG-11: orgs with more/less than 1 owner: {bad}"


def test_tc60_task_assignee_belongs_to_same_org_as_project():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.task_id, t.assignee_id, p.org_id AS project_org
        FROM Tasks t
        JOIN Projects p ON t.project_id = p.project_id
        LEFT JOIN Memberships m
            ON t.assignee_id = m.user_id AND m.org_id = p.org_id
        WHERE t.assignee_id IS NOT NULL AND m.membership_id IS NULL
    """)
    bad = cursor.fetchall()
    conn.close()
    assert not bad, f"BUG-05: tasks assigned to users outside the project's org: {[dict(r) for r in bad]}"


def test_tc61_free_plan_project_limit_at_db_level():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.org_id, COUNT(p.project_id) as project_count
        FROM Subscriptions s
        JOIN Projects p ON p.org_id = s.org_id
        WHERE s.plan = 'FREE'
        GROUP BY s.org_id
        HAVING COUNT(p.project_id) > 3
    """)
    bad = cursor.fetchall()
    conn.close()
    assert not bad, f"BUG-04: FREE-plan orgs exceeding 3 projects: {[dict(r) for r in bad]}"


def test_tc62_no_duplicate_user_emails():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email, COUNT(*) as c FROM Users GROUP BY email HAVING c > 1")
    dupes = cursor.fetchall()
    conn.close()
    assert not dupes, f"Duplicate emails found: {[dict(r) for r in dupes]}"


def test_tc63_invoice_amounts_non_negative():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT invoice_id, amount FROM Invoices WHERE amount < 0")
    bad = cursor.fetchall()
    conn.close()
    assert not bad, f"Negative invoice amounts found: {[dict(r) for r in bad]}"


def test_tc64_no_orphan_memberships():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.membership_id FROM Memberships m
        LEFT JOIN Users u ON m.user_id = u.user_id
        LEFT JOIN Organizations o ON m.org_id = o.org_id
        WHERE u.user_id IS NULL OR o.org_id IS NULL
    """)
    bad = cursor.fetchall()
    conn.close()
    assert not bad, f"Orphan memberships: {[dict(r) for r in bad]}"