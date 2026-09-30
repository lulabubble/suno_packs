#!/bin/sh -ex

home_regex=/data/data/com\\.termux/files/home
top_regex=$home_regex/suno_packs

mycode=/sdcard/mycode
track=`pwd | sed "s,^$top_regex/,,"`

cp -r $mycode/$track/* ./

