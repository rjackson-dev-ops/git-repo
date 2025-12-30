# Commands to Work with Git

## Install GIT in windows

## Geit Github ID for Org

```
 gh api orgs/stelligent
{
  "login": "stelligent",
  "id": 1551090,
```


### Get Users

```
.\get-users.ps1

```

### Removing Users

```
$env:GITHUB_TOKEN = "github_pat_11......"

remove-github-users.py stelligent
```

### Add users to Stelligent

```

$env:GITHUB_TOKEN = "github_pat_11......"
python add_users_to_org.py
```