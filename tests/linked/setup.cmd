if exist subdir\nul (
    rmdir /S /Q subdir || exit 1
)
mkdir subdir || exit 1
cd subdir || exit 1
mklink /j B ..\..\nested\subdir\B || exit 1
mkdir m || exit 1
cd m || exit 1
mklink /j n ..\..\..\nested\subdir\A || exit 1
cd .. || exit 1
mklink /j A m\n || exit 1
mklink /j loop . || exit 1
