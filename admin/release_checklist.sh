#!/usr/bin/env bash
set -eu

# This is an automated release checklist. Call it to ensure that all known
# mentions of the gcovr version have been updated to a target version.

print_err() {
    echo "$@" >&2
}

verify_tags=yes
verify_docs_next_version=yes
target_version=
usage="usage: $0 [OPTIONS] TARGET_REVISION

Options:
  --no-verify-tags
  --no-verify-docs-next-version
"

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --no-verify-tags)
            verify_tags=no
            shift
            ;;
        --no-verify-docs-next-version)
            verify_docs_next_version=no
            shift
            ;;
        -*)
            print_err "unknown argument $1"
            print_err "$usage"
            exit 1
            ;;
        *)
            target_version="$1"
            shift
            break
            ;;
    esac
done

if [[ -z "$target_version" || "$#" -ne 0 ]]; then
    print_err "$usage"
    exit 1
fi

ok=yes

maybe_error() {
    local is_err="$1"
    shift
    if [[ "$is_err" = yes ]]; then
        ok=no
        print_err "ERROR:" "$@"
    else
        # ok stays unchanged
        print_err "WARNING:" "$@"
    fi
}

error() {
    maybe_error yes "$@"
}

if ! [[ -d .git ]]; then
    error "Please run this script from the repository root"
    exit 1
fi

grep -qF "__version__ = \"$target_version\"" gcovr/version.py \
    || error "gcovr/version.py: Please update with this version"

grep -qE "^$(echo "$target_version" | sed -e "s/+main//") \\(.+\\)\$" CHANGELOG.rst \
    || error "CHANGELOG.rst: Please update with this version"

grep -qF "version=\"gcovr $target_version\"" doc/examples/example_cobertura.xml \
    || error "examples: Please regenerate: " \
            "cd doc/examples; ./example_cobertura.sh > example_cobertura.xml"

grep -qF "GCOVR (Version $target_version)" doc/examples/example_html.html \
    || error "examples: Please regenerate: " \
            "cd doc/examples; ./example_html.sh > example_html.html"
grep -qF "GCOVR (Version $target_version)" doc/examples/example_html.details.html \
    || error "examples: Please regenerate: " \
            "cd doc/examples; ./example_html.sh > example_html.details.html"

grep -qF "$(basename $0) \$EXTRA_CHECKLIST_ARGS $target_version" .github/workflows/deploy.yml \
    || error ".github/workflows/deploy.yml: Please update the $0 version"

occurrences="$(
  grep -E '\.\. (versionadded|versionchanged|versionremoved|deprecated):: NEXT' \
       -A 1 doc/source/*.rst doc/source/*/*.rst *.rst || exit 0)"
test -z "$occurrences" || {
    maybe_error $verify_docs_next_version \
                "doc/source/*.rst: please update notes with next version"
    # shellcheck disable=SC2001
    echo "$occurrences" | sed 's/^/INFO: /' >&2
}

if git tag | grep -qE "^$target_version\$"; then
    # grandfathering of non-annotated 3.4 tag
    [[ "$target_version" = 3.4 ]] \
        || [[ "$(git cat-file -t "$target_version")" = tag ]] \
        || maybe_error $verify_tags \
                       "Please use annotated tags (git tag -a) for releases"
fi

if [[ "$ok" = yes ]]; then
    echo "SUCCESS: release may proceed"
else
    echo "FAILURE: please fix the above problems"
    exit 1
fi
