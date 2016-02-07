#!/bin/bash
#Takes a file and replaces all commas in between double quotes "" with ";"
#Assumes that quotes are balanced in each line
#removes all the double quotes at the end
awk -F'"' -v OFS='' '{for (i=2; i<=NF; i+=2) gsub(",", ";", $i) } 1' $1 > ${1}2
cp ${1}2 $1
rm ${1}2
sed 's/\"//g' $1 > ${1}2
cp ${1}2 $1
rm ${1}2
