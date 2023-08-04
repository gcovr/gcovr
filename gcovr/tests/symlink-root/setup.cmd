if exist symlink\nul (
    rmdir /S /Q symlink || exit 1
)
mklink /j symlink .\root
