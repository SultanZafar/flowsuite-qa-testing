"""
RBAC (Role-Based Access Control) tests: TC29 - TC34

Each test asserts the SECURE behaviour. Where the app has a bug, the test
FAILS on purpose - that failure is your bug evidence.
"""
from api_helpers import change_role, find_member, invite

BLOCKED = (401, 403)


def test_tc29_member_cannot_invite_owner(globex_member):
    """RBAC-01: a plain MEMBER must not be able to invite someone as OWNER."""
    resp, _ = invite(globex_member, globex_member["org_id"], "OWNER")
    assert resp.status_code in BLOCKED, (
        f"BUG-02: MEMBER invited an OWNER (HTTP {resp.status_code}, expected 403)"
    )


def test_tc30_member_cannot_invite_admin(globex_member):
    """RBAC-02: a plain MEMBER must not be able to invite someone as ADMIN."""
    resp, _ = invite(globex_member, globex_member["org_id"], "ADMIN")
    assert resp.status_code in BLOCKED, (
        f"BUG-02: MEMBER invited an ADMIN (HTTP {resp.status_code}, expected 403)"
    )


def test_tc31_member_cannot_promote_self_to_owner(globex_member, globex_owner):
    """RBAC-03: a MEMBER must not be able to make themselves OWNER."""
    org_id = globex_member["org_id"]
    resp = change_role(globex_member, org_id, globex_member["user_id"], "OWNER")

    # Cleanup FIRST: if the bug exists, the member is now an OWNER and would
    # break the other tests. The real owner puts the role back to MEMBER.
    change_role(globex_owner, org_id, globex_member["user_id"], "MEMBER")

    assert resp.status_code in BLOCKED, (
        f"BUG-03: MEMBER promoted themselves to OWNER (HTTP {resp.status_code}, expected 403)"
    )


def test_tc32_member_cannot_change_another_members_role(globex_member, globex_owner):
    """RBAC-04: a MEMBER must not be able to change someone else's role."""
    org_id = globex_member["org_id"]

    # The owner creates a throwaway user for this test to target.
    _, email = invite(globex_owner, org_id, "MEMBER")
    target = find_member(globex_owner, org_id, email)
    assert target is not None, "Test setup failed: invited user not found in members list"

    resp = change_role(globex_member, org_id, target["user_id"], "ADMIN")
    assert resp.status_code in BLOCKED, (
        f"BUG-03: MEMBER changed another user's role (HTTP {resp.status_code}, expected 403)"
    )


def test_tc33_admin_can_invite_member(acme_admin):
    """RBAC-05: an ADMIN is allowed to invite a new MEMBER."""
    resp, _ = invite(acme_admin, acme_admin["org_id"], "MEMBER")
    assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.text}"


def test_tc34_owner_can_change_a_members_role(acme_owner):
    """RBAC-06: an OWNER is allowed to change another user's role."""
    org_id = acme_owner["org_id"]

    _, email = invite(acme_owner, org_id, "MEMBER")
    target = find_member(acme_owner, org_id, email)
    assert target is not None, "Test setup failed: invited user not found in members list"

    resp = change_role(acme_owner, org_id, target["user_id"], "ADMIN")
    assert resp.status_code in (200, 204), f"Expected 200/204, got {resp.status_code}: {resp.text}"

    # Verify the change really happened, not just that the API said OK.
    assert find_member(acme_owner, org_id, email)["role"] == "ADMIN"