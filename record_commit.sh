#!/bin/sh

commit=$(git rev-parse HEAD)
[ -n "$(git status --short)" ] && dirty=-dirty
printf "DEPLOYED_COMMIT = '$commit$dirty'"
printf "DEPLOYED_COMMIT = '$commit$dirty'" >triviagame/commit.py
