function Show-Tree($path, $prefix = "") {
    Get-ChildItem $path -Force |
        Where-Object { $_.Name -notmatch '^(\.|__)' } |
        ForEach-Object {
            Write-Output "$prefix$($_.Name)"
            if ($_.PSIsContainer) {
                Show-Tree $_.FullName "$prefix  "
            }
        }
}

Show-Tree .