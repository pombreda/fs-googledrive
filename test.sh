#!/bin/sh
coverage run --source googledrivefs -m py.test \
&& echo \
&& coverage report