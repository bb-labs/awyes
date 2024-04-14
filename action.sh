#!/bin/bash

if [ "$3" = true ]; then
    echo "$3 is true"
else
    echo "$3 is not true"
fi

if [ "$4" = true ]; then
    echo "$4 is true"
else
    echo "$4 is not true"
fi

awyes --path $1 $2
