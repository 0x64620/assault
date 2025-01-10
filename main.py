#!/usr/bin/env python3

# 0x64620/assault -- simple forgejo-to-gitlab migration tool

import os
import subprocess
import requests

forgejoApiUri = "https://git.forgejo.me/api/v1"
forgejoApiToken = "pyoptoiwerjiwjhfihsdjfhdsovijfdbwfioj" # put ur key here
gitlabApiUri = "https://gitlab.example.com/api/v4"
gitlabApiToken = "glpat-hcuisdvnuidvhuibh" # put ur key here
gitlabSshUri = "git@gitlab.example.com"
localBaseDir = "./repositories"

def runCommand(command, cwd=None):
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error while {command}:")
        print(result.stderr)
        return False
    return True

def getUsers():
    headers = {"Authorization": f"token {forgejoApiToken}"}
    response = requests.get(f"{forgejoApiUri}/admin/users", headers=headers)
    if response.status_code != 200:
        print(f"Error retrieving users from FG: {response.status_code} - {response.text}")
        return []
    return response.json()

def getUserRepos(username):
    headers = {"Authorization": f"token {forgejoApiToken}"}
    response = requests.get(f"{forgejoApiUri}/users/{username}/repos", headers=headers)
    if response.status_code != 200:
        print(f"Error retrieving repos for {username}: {response.status_code} - {response.text}")
        return []
    return response.json()

def makeGlRepo(username, repo_name):
    headers = {"PRIVATE-TOKEN": gitlabApiToken}
    data = {"name": repoName}
    response = requests.post(f"{gitlabApiUri}/projects", headers=headers, json=data)
    if response.status_code == 201:
        print(f"Repo {repoName} for {username} moved GitLab.")
        return True
    elif response.status_code == 409:
        print(f"Repo {repoName} exists on GitLab.")
        return True
    else:
        print(f"Error while creating {repoName} on GitLab: {response.status_code} - {response.text}")
        return False

def procUser(username, repos):
    userDir = os.path.join(localBaseDir, username)
    os.makedirs(userDir, exist_ok=True)

    for repo in repos:
        repoName = repo["name"]
        sshUri = repo["ssh_url"]
        print(f"Copying {repo_name} for {username}...")

        repoDir = os.path.join(userDir, repoName)
        if not runCommand(f"git clone --bare {sshUri} {repoDir}"):
            continue

        print(f"Creating {repo_name} on GitLab...")
        if not makeGlRepo(username, repoName):
            continue

        print(f"Uploading {repoName} to GitLab...")
        gitlabRepoUri = f"{gitlabSshUri}:{username}/{repoName}.git"
        if runCommand(f"git remote add gitlab {gitlabRepoUri}", cwd=repoDir):
            runCommand(f"git push --mirror gitlab", cwd=repoDir)

def main():
    users = getUsers()
    if not users:
        print("Users not found.")
        return

    for user in users:
        username = user["login"]
        print(f"Processing {username}...")
        repos = getUserRepos(username)
        if not repos:
            print(f"{username} doesn't have repos.")
            continue
        procUser(username, repos)

if __name__ == "__main__":
    main()
