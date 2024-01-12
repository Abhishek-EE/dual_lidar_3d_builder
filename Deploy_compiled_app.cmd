if EXIST "C:\MyCode\dual_lidar_3d" goto nomkdir
mkdir "C:\MyCode"
mkdir "C:\MyCode\dual_lidar_3d"
mkdir "C:\MyCode\dual_lidar_3d\db\"
:nomkdir
cd "Z:\centralDev\py37\pyQt5\dual_lidar_3d"
rem xcopy /S/Y ".\*.db" "%USERPROFILE%\.qgis2\python\plugins\ida\*.db"
del /F/Q "C:\MyCode\dual_lidar_3d\*.*"
xcopy /S/Y .\dist\*.* "C:\MyCode\dual_lidar_3d\*.*"
xcopy /S/Y .\db\*.db "C:\MyCode\dual_lidar_3d\db\*.db"

ECHO dual_lidar_3d Deployed
exit
:notfound
ECHO dual_lidar_3d Not Deployed.
exit