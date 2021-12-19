#!/bin/sh

commit=$(git rev-parse HEAD)
printf "DEPLOYED_COMMIT = '$commit'"
[ -d "$1" ] && printf "DEPLOYED_COMMIT = '$commit'" >"$1/app/config/commit.py"
