# 1. Set your org name
$org = "stelligent"

# Collect users in a single list
$users = @()

# Org members
$members = gh api "orgs/$org/members" --paginate | ConvertFrom-Json
$users += $members | ForEach-Object {
    [PSCustomObject]@{
        login = $_.login
        type  = 'OrgMember'
    }
}

# Outside collaborators
$outside = gh api "orgs/$org/outside_collaborators" --paginate | ConvertFrom-Json
$users += $outside | ForEach-Object {
    [PSCustomObject]@{
        login = $_.login
        type  = 'OutsideCollaborator'
    }
}

# One line per individual, sorted by login
$users |
    Sort-Object login -Unique |
    Export-Csv -Path ".\temp-directory\org-users-and-collaborators.csv" -NoTypeInformation -Encoding UTF8
