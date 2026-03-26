import time
import jwt
import requests
import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("GITHUB_APP_ID")
PRIVATE_KEY_PATH = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
INSTALLATION_ID = os.getenv("GITHUB_APP_INSTALLATION_ID")
OWNER = os.getenv("TARGET_OWNER")
REPO = os.getenv("TARGET_REPO")

if not all([APP_ID, PRIVATE_KEY_PATH, INSTALLATION_ID, OWNER, REPO]):
    raise Exception("Missing required environment variables")

# Load private key
with open(PRIVATE_KEY_PATH, "r") as f:
    PRIVATE_KEY = f.read()

# Step 1 — Create JWT
def generate_jwt():
    now = int(time.time())

    payload = {
        "iat": now - 60,        # issued at time
        "exp": now + (10 * 60), # max 10 minutes
        "iss": APP_ID           # app id
    }

    token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
    return token

# Step 2 — Exchange JWT for installation token
def get_installation_token(jwt_token):
    url = f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.post(url, headers=headers)

    if response.status_code != 201:
        raise Exception(f"Failed to get installation token: {response.text}")

    return response.json()["token"]

# Step 3 — Call GitHub API
def main():
    print("Generating JWT...")
    jwt_token = generate_jwt()

    print("Getting installation token...")
    installation_token = get_installation_token(jwt_token)

    headers = {
        "Authorization": f"Bearer {installation_token}",
        "Accept": "application/vnd.github+json"
    }

    print("Listing repositories...")
    repos = requests.get(
        "https://api.github.com/installation/repositories",
        headers=headers
    ).json()

    for repo in repos.get("repositories", []):
        print("-", repo["full_name"])

    print("\nCreating issue...")
    issue_data = {
        "title": "GitHub App Python script test",
        "body": "Created via Python script using GitHub App"
    }

    issue = requests.post(
        f"https://api.github.com/repos/{OWNER}/{REPO}/issues",
        headers=headers,
        json=issue_data
    )

    if issue.status_code != 201:
        raise Exception(issue.text)

    print("Created issue:", issue.json()["html_url"])

if __name__ == "__main__":
    main()