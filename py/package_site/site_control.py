#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  site_dashboard.py
#  
#  

from flask import Flask, render_template
import datetime
import sqlite3
import requests
import json

def show_control(main_menu, menu_idx, app_name):
   now = datetime.datetime.now()
   timeString = now.strftime("%y-%m-%d %H:%M")
   templateData = {
      'title'      : main_menu[menu_idx][0],
      'app'        : app_name,
      'time'       : timeString,
      'main_menu'  : main_menu
      }
   return render_template('control.html', **templateData)    
    
