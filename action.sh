#!/bin/bash

if [[$3 = true]]; then
    awyes --verbose --path $1 $2
else
    awyes --path $1 $2
fi


