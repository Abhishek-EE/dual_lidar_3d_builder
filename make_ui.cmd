REM compile resource and ui files
for /f %%X in (uilist.txt) do pyuic5 -o %%X.py %%X.ui

rem cd ..

rem Done