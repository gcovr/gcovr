cd project
if NOT exist relevant-library\nul (
    mklink /j relevant-library ..\external-library
)
