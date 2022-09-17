#!/bin/bash
time jsub -N build -mem 2G -sync y -j y -stderr -cwd cargo build --release
