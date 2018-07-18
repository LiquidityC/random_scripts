#!/bin/sh

# Wraps a command in a guard so that the caller may receive a notification when
# the command completes. eg:
# % guard <slow build command>

PROG=${@:1}
notify-send "Guarding: $PROG"
$PROG
notify-send "Completed: $PROG"
