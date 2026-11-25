#!/bin/sh
# Run with a NEW project name followed by one or more video paths.
set -eu
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 NEW_PROJECT FILE [FILE ...]" >&2
    exit 2
fi
project=$1
shift
cli-anything-davinci doctor
cli-anything-davinci project create "$project"
cli-anything-davinci media import -- "$@"
cli-anything-davinci timeline create Main
cli-anything-davinci timeline append -- "$@"
cli-anything-davinci timeline marker add 0 Opening
cli-anything-davinci project save
