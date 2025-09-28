@echo off
start "" "%~dp0/../Python39/python" -i -c "import sys;sys.path.append(\"%~dp0/../Scripts\");import PrismCore;pcore=PrismCore.create(prismArgs=[\"noUI\", \"loadProject\"])"