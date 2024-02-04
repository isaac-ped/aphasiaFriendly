#!/usr/bin/env bash
# Helper script to run summarization on all inputs
mkdir -p finetuning
set -eu
for X in inputs/*.txt; do
    if ! [ -s "$X" ] ; then
        echo "File $X is empty. Skipping"
        continue
    fi
    echo "###### Running on $X"
    BASENAME="$(basename "$X")"
    NAME="${BASENAME%.*}"
    ./af summarize -f yaml -f pptx "$X" "$@" -v;
    cp "output/$NAME/summary.yaml" "finetuning/$NAME.yaml"
done
