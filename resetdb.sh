#!/bin/bash
sudo -u postgres \
    psql -c 'DROP DATABASE hive;'
sudo -u postgres \
    psql -c "create database hive with owner = drone encoding = 'UTF8';"
