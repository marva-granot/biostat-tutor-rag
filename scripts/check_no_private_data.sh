#!/bin/sh
# Fails if course material or data derived from it would be committed or pushed.
#
# Usage:
#   check_no_private_data.sh staged           check the index (used by pre-commit)
#   check_no_private_data.sh push < refs      check unpushed commits (used by pre-push;
#                                             reads git's "<ref> <sha> <ref> <sha>" lines)
#
# The patterns mirror .gitignore on purpose: .gitignore stops accidental `git add`,
# this check also catches `git add -f` and files that were committed earlier.

PRIVATE_RE='(^|/)(data|index)/|(^|/)eval/private/|(^|/)\.env$|\.(pdf|pptx)$'
ZERO=0000000000000000000000000000000000000000

list_files() {
  case "$1" in
    staged)
      git diff --cached --name-only --diff-filter=ACMR
      ;;
    push)
      while read -r _local_ref local_sha _remote_ref remote_sha; do
        [ "$local_sha" = "$ZERO" ] && continue            # branch deletion
        if [ "$remote_sha" = "$ZERO" ]; then
          range="$local_sha --not --remotes"              # new branch: all unpushed commits
        else
          range="$remote_sha..$local_sha"
        fi
        # --name-only over every commit, so a file added then deleted is still caught.
        # shellcheck disable=SC2086
        git log --name-only --pretty=format: $range
      done
      ;;
  esac
}

case "$1" in staged|push) ;; *) echo "usage: $0 staged|push" >&2; exit 2 ;; esac

bad=$(list_files "$1" | sort -u | grep -E "$PRIVATE_RE")

if [ -n "$bad" ]; then
  echo "BLOCKED: course material or derived data would leave this machine:" >&2
  echo "$bad" | sed 's/^/  /' >&2
  echo "Unstage with 'git rm --cached <file>' (or rewrite the commits) and retry." >&2
  exit 1
fi
exit 0
