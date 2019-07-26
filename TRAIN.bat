@echo off
echo Next, begin learning the model. Learning outcomes will be applied automatically.
pause
cd app
..\python\python.exe train.py ..\dataset
pause