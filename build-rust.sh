#!/bin/bash
toolforge jobs run build \
    --command "bash -c 'source ~/.profile && cd ~/src/database-reports/ && cargo build --release'" \
    --image python3.11 --mem 2G --cpu 2
echo "Build has been queued"
