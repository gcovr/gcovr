subst %GCOVR_TEST_DRIVE_WINDOWS% .. || exit /B 1
subst || exit /B 1
@call :RUN %*
(
    subst %GCOVR_TEST_DRIVE_WINDOWS% /d || exit /B 1
    exit %ERRORLEVEL%
)

:RUN
    :: Brace to replace environment references before changing the directory.
    (
        pushd %GCOVR_TEST_DRIVE_WINDOWS%\simple1-drive-subst || exit /B 1
        %*
    )
    (
        popd
        exit /B %errorlevel%
    )


