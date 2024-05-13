# Тестовое задание 2 DATUM Group
Необходим PostgreSQL/PostGIS и геоинформационная библиотека gdal

Установка
```
conda env create -n <name-env> -f environment.yaml
conda activate <name-env>
```
Создать файл .env 
```
NAME_DB=...
USER_DB=...
PASSWORD_DB=...
HOST_DB=...
PORT_DB=...
GDAL_LIBRARY= ... + .dll
OSGEO4W= ... (Ex: C:\OSGeo4W)
```
Создание таблиц бд
```
python .\manage.py migrate
```
Запуск
```
python .\manage.py runserver
```
