#!/bin/sh
set -eu  # "use strict"
set -x  # trace all commands

#BEGIN simple epoch
gcovr --timestamp 1640606727
#END simple epoch

#BEGIN source date epoch
SOURCE_DATE_EPOCH=1640606727 gcovr
#END source date epoch

#BEGIN simple RFC 3339
gcovr --timestamp '2021-12-27 13:05:27'
#END simple RFC 3339

#BEGIN RFC 3339 with UTC timezone
gcovr --timestamp '2021-12-27T13:05:27Z'
gcovr --timestamp '2021-12-27T13:05:27+00:00'
gcovr --timestamp '2021-12-27T13:05:27-00:00'
#END RFC 3339 with UTC timezone

#BEGIN prefixes
gcovr --timestamp @1640606727
gcovr --timestamp epoch:1640606727
gcovr --timestamp 'rfc3339:2021-12-27 13:05:27'
#END prefixes

# The following commands can only be performed if
# A) we are in a git repository, and
# B) git is installed.
# The use of "command -v" is a Posixly-correct way to check for existence of a
# command, unlike the "which", "type", or "hash" commands.
if test -d ../../.git && command -v git >/dev/null; then

#BEGIN git commit
gcovr --timestamp="$(git show --no-patch --format=%cI HEAD)"
#END git commit

for fmt in %at %ct %aI %cI; do
    gcovr --timestamp="$(git show --no-patch --format=$fmt HEAD)"
done

for date in unix iso-strict iso8601-strict iso-strict-local iso8601-strict-local; do
    gcovr --timestamp="$(git show --no-patch --date=$date --format=%cd HEAD)"
done

fi
