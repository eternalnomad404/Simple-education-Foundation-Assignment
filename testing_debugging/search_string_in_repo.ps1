Get-ChildItem -Recurse -Filter *.py -File |                                      
    Where-Object { $_.Fullname -notmatch '\\(\.venv|.venv_wsl|\.git|__pycache__)\\' } |
    Select-String -SimpleMatch "Search_string"