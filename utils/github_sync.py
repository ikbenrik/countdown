import os
import git
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_FILE_PATH = os.getenv("GITHUB_FILE_PATH")
LOCAL_FILE_PATH = "items.json"

def push_to_github():
    """Pushes the latest items.json to GitHub."""
    repo_path = os.getcwd()  # ✅ Get current working directory
    repo = git.Repo(repo_path)

    try:
        repo.git.add(LOCAL_FILE_PATH)  # ✅ Stage the file
        repo.index.commit("Auto-update items.json")  # ✅ Commit changes
        origin = repo.remote(name="origin")
        origin.push()  # ✅ Push to GitHub

        print("✅ Successfully pushed items.json to GitHub!")
    except Exception as e:
        print(f"❌ Git push failed: {e}")
