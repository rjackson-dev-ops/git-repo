#!/usr/bin/env python3
"""
List all GitHub org members and outside collaborators, one at a time,
prompting the user to optionally delete them from the organization.

Requirements:
- Python 3
- 'requests' library: pip install requests
- Environment variable GITHUB_TOKEN set to a PAT with org admin permissions
  (e.g., fine-grained token with appropriate org access, or classic with admin:org)
"""

import os
import sys
import requests
from collections import OrderedDict

GITHUB_API = "https://api.github.com"

# >>> EDIT THIS LIST <<<
# Logins you do NOT want to list or delete (they will be skipped entirely)
EXCLUDED_LOGINS = {
    "amarentis",
    "dwhitehead95",
    "goldForce",
    "matthewcmorgan",
    "mbarbour-ns",
    "nbaker-stelligent",
    "rjackson-dev-ops",
    "stelligent-joao",
    "stelligent-releasebot",
    "stelligent-topograph-crawlerbot",
    "zacherytcox-stelligent",
}


def get_token() -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("ERROR: Please set the GITHUB_TOKEN environment variable.")
        print("The token should have appropriate org admin permissions.")
        sys.exit(1)
    return token


def get_paginated(token: str, path: str):
    """
    Generic helper to fetch all pages for a given GitHub API path.
    Yields JSON items from each page.
    """
    url = f"{GITHUB_API}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    params = {"per_page": 100}

    while url:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            print(f"ERROR: GitHub API request failed: {resp.status_code}")
            print(resp.text)
            sys.exit(1)

        data = resp.json()
        if isinstance(data, list):
            for item in data:
                yield item
        else:
            yield data

        links = resp.links
        if "next" in links:
            url = links["next"]["url"]
            params = None  # already encoded
        else:
            url = None


def fetch_org_users_and_collaborators(token: str, org: str):
    # Org members
    members = [
        {"login": user["login"], "type": "OrgMember"}
        for user in get_paginated(token, f"/orgs/{org}/members")
    ]

    # Outside collaborators
    outside = [
        {"login": user["login"], "type": "OutsideCollaborator"}
        for user in get_paginated(token, f"/orgs/{org}/outside_collaborators")
    ]

    # Combine & dedupe by (login, type) while preserving order
    combined = OrderedDict()
    for entry in members + outside:
        key = (entry["login"], entry["type"])
        if key not in combined:
            combined[key] = entry

    users = list(combined.values())

    # Apply exclude filter
    users = [u for u in users if u["login"] not in EXCLUDED_LOGINS]

    return users


def remove_user_from_org(token: str, org: str, login: str, user_type: str):
    """
    Remove a user from the organization, either as a member or as an outside collaborator.
    """
    if user_type == "OrgMember":
        path = f"/orgs/{org}/members/{login}"
    elif user_type == "OutsideCollaborator":
        path = f"/orgs/{org}/outside_collaborators/{login}"
    else:
        print(f"Unknown user type '{user_type}' for {login}, skipping delete.")
        return

    url = f"{GITHUB_API}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    resp = requests.delete(url, headers=headers)

    if resp.status_code in (204, 202):
        print(f"✅ Successfully removed {login} as {user_type}")
    else:
        print(f"❌ Failed to remove {login} ({user_type}). Status: {resp.status_code}")
        try:
            print(resp.json())
        except Exception:
            print(resp.text)


def main():
    if len(sys.argv) < 2:
        print("Usage: python list_and_delete_github_users.py ORG_NAME")
        sys.exit(1)

    org = sys.argv[1]
    token = get_token()

    print(f"Fetching users for org: {org} ...")
    users = fetch_org_users_and_collaborators(token, org)

    if not users:
        print("No users or collaborators found (after applying exclude list).")
        return

    print(f"Excluded logins: {', '.join(sorted(EXCLUDED_LOGINS)) or 'none'}")
    total = len(users)
    print(f"Found {total} users (members + outside collaborators, after excluding above).\n")

    for idx, user in enumerate(users, start=1):
        login = user["login"]
        utype = user["type"]
        print(f"{idx}/{total}: {login}  ({utype})")

        answer = input("Delete this user from the org? [y/N/q]: ").strip().lower()

        if answer == "q":
            print(f"Stopping early at user {login}")
            break
        elif answer == "y":
            remove_user_from_org(token, org, login, utype)
        else:
            print(f"Skipping {login}")

        print()  # blank line between entries

    print("Done.")


if __name__ == "__main__":
    main()
