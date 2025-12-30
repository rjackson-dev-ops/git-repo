param(
    # Your GitHub organization login
    [string]$Org   = 'YOUR_ORG_NAME',

    # Run in "show me only" mode by default; pass -DryRun:$false to actually delete
    [bool]  $DryRun = $true
)

# Hardcoded list of GitHub logins that are allowed to remain
# >>> EDIT THIS LIST <<<
$AllowedLogins = @(
    'alice',
    'bob',
    'carol'
)

Write-Host ("Using organization: {0}" -f $Org) -ForegroundColor Cyan
Write-Host ('Allowed logins: {0}' -f ($AllowedLogins -join ', ')) -ForegroundColor Cyan

# Ensure gh is available
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error 'GitHub CLI (gh) is not installed or not in PATH.'
    exit 1
}

# Ensure we are authenticated
gh auth status > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error 'gh is not authenticated. Run ''gh auth login'' first.'
    exit 1
}

Write-Host 'Fetching organization members...' -ForegroundColor Yellow
$membersJson = gh api "orgs/$Org/members" --paginate
$members = @()
if ($membersJson) {
    $members = $membersJson | ConvertFrom-Json
}

Write-Host 'Fetching outside collaborators...' -ForegroundColor Yellow
$outsideJson = gh api "orgs/$Org/outside_collaborators" --paginate
$outside = @()
if ($outsideJson) {
    $outside = $outsideJson | ConvertFrom-Json
}

# Build candidate removal list
$toRemove = @()

# Org members not in allowed list
$toRemove += $members |
    Where-Object { $AllowedLogins -notcontains $_.login } |
    ForEach-Object {
        [PSCustomObject]@{
            login = $_.login
            type  = 'OrgMember'
        }
    }

# Outside collaborators not in allowed list
$toRemove += $outside |
    Where-Object { $AllowedLogins -notcontains $_.login } |
    ForEach-Object {
        [PSCustomObject]@{
            login = $_.login
            type  = 'OutsideCollaborator'
        }
    }

# Dedupe by login/type
$toRemove = $toRemove | Sort-Object login, type -Unique

if (-not $toRemove) {
    Write-Host 'No users found that are outside the allowed list. Nothing to do.' -ForegroundColor Green
    exit 0
}

Write-Host ''
Write-Host 'Users that will be removed (not in allowed list):' -ForegroundColor Yellow
$toRemove | Format-Table login, type

if ($DryRun) {
    Write-Host ''
    Write-Host 'Dry run mode is ON. No changes have been made.' -ForegroundColor Cyan
    Write-Host 'Re-run with -DryRun:$false to actually remove these users.' -ForegroundColor Cyan
    exit 0
}

Write-Host ''
Write-Host 'Dry run is OFF. Proceeding to remove users...' -ForegroundColor Red

foreach ($u in $toRemove) {
    if ($u.type -eq 'OrgMember') {
        Write-Host ("Removing org member '{0}' from '{1}'..." -f $u.login, $Org) -ForegroundColor Red
        gh api -X DELETE "orgs/$Org/members/$($u.login)"
    }
    elseif ($u.type -eq 'OutsideCollaborator') {
        Write-Host ("Removing outside collaborator '{0}' from '{1}'..." -f $u.login, $Org) -ForegroundColor Red
        gh api -X DELETE "orgs/$Org/outside_collaborators/$($u.login)"
    }
    else {
        Write-Warning ("Unknown type '{0}' for '{1}' – skipping." -f $u.type, $u.login)
    }
}

Write-Host 'Done.' -ForegroundColor Green
