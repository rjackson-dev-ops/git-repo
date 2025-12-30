#!/usr/bin/env python3
"""
Interactively add users to a GitHub organization by login.

- Prompts for GitHub usernames (logins) one at a time.
- For each login, calls the GitHub REST API to set org membership.
- If the user isn't already a member, GitHub will send an invitation and
  the membership state will be "pending" until they accept.

Requirements:
- Python 3
- 'requests' library: pip install requests
- Environment variable GITHUB_TOKEN set to a PAT with org admin permissions:
  * Fine-grained PAT: "Members" permission (write) for the org
  * Classic PAT: admin:org
"""

import os
import sys
import requests

GITHUB_API = "https://api.github.com"


def get_token() -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("ERROR: Please set the GITHUB_TOKEN environment variable.")
        print("The token must have permission to manage org members.")
        sys.exit(1)
    return token


def add_user_to_org(token: str, org: str, username: str, role: str = "member"):
    """
    Add or update a user's membership in an organization.

    Uses:
      PUT /orgs/{org}/memberships/{username}
    GitHub will:
      - Add them (or update role) if possible
      - Send an invitation if they are not yet a member (state: 'pending')
    """
    url = f"{GITHUB_API}/orgs/{org}/memberships/{username}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"role": role}

    resp = requests.put(url, headers=headers, json=payload)

    if resp.status_code in (200, 201):
        data = resp.json()
        state = data.get("state")
        actual_role = data.get("role")
        print(f"✅ {username}: membership state = {state}, role = {actual_role}")
    elif resp.status_code == 404:
        print(f"❌ {username}: not found or you lack permission (404).")
        try:
            print(resp.json())
        except Exception:
            print(resp.text)
    elif resp.status_code == 403:
        print(f"❌ {username}: forbidden (403) – check token permissions / org ownership.")
        try:
            print(resp.json())
        except Exception:
            print(resp.text)
    else:
        print(f"❌ {username}: unexpected status {resp.status_code}")
        try:
            print(resp.json())
        except Exception:
            print(resp.text)


def main():
    if len(sys.argv) < 2:
        print("Usage: python add_users_to_org.py ORG_NAME")
        sys.exit(1)

    org = sys.argv[1]
    token = get_token()

    print(f"Adding users to org: {org}")
    print("Enter GitHub logins one at a time.")
    print("Press Enter on an empty line or type 'q' to quit.\n")

    while True:
        login = input("GitHub login to add (blank/q to quit): ").strip()
        if not login or login.lower() == "q":
            print("Exiting.")
            break

        # Optional: confirm each time
        confirm = input(f"Add '{login}' to org '{org}' as role 'member'? [y/N]: ").strip().lower()
        if confirm != "y":
            print(f"Skipping {login}.\n")
            continue

        add_user_to_org(token, org, login)
        print()  # blank line between users


if __name__ == "__main__":
    main()
