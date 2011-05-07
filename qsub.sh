#!/bin/sh

#$ -j y
#$ -N $1
#$ -l sqlprocs-s1=1

python $HOME/reports/$1.py
