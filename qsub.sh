#!/bin/sh

#$ -j y
#$ -N $1
#$ -l sql-s1-user-readonly=1

python $HOME/reports/$1.py
