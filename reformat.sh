#!/usr/bin/bash

echo $1
sed -e 's/.\{19\}$//g;s/ //g' < $1 | grep -v '^$' > $1.list
