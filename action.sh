#!/bin/bash

if [ $3 = true ] && [ $4 = true ]; then
    awyes --verbose --dry --path $1 $2
elif [ $3 = true ]; then
    awyes --verbose --path $1 $2
elif [ $4 = true ]; then
    awyes --dry --path $1 $2
else
    awyes --path $1 $2
fi
