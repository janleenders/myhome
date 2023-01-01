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
    
def show_dashboard(main_menu, menu_idx, app_name, database_path):

   try:
      conn
   except Exception:
      conn = sqlite3.connect(database_path)

   cur= conn.cursor()
   cur.execute("select printf('%02d', tst_hr) ||':'|| printf('%02d', tst_m) ||':'|| printf('%02d', tst_s) as time , consumption_actual, return_actual  from p1_channel_detail where channel=0 order by tst desc limit 200")
   rows = cur.fetchall()
   chan0_labels = [row[0] for row in rows]
   chan0_values = [row[1] for row in rows]
   chan0_return_values = [row[2] for row in rows]

   i = 0
   N = len(chan0_labels)
   while i < N / 2 :
      c0 = chan0_labels[i]
      c1 = chan0_values[i]
      c2 = chan0_return_values[i]
      chan0_labels[i] = chan0_labels[N-1-i]
      chan0_values[i] = chan0_values[N-1-i]
      chan0_return_values[i] = chan0_return_values[N-1-i]
      chan0_labels[N-1-i] = c0
      chan0_values[N-1-i] = c1
      chan0_return_values[N-1-i] = c2
      i += 1

   cur= conn.cursor()
   cur.execute("select printf('%02d', tst_hr) ||':'|| printf('%02d', tst_m) ||':'|| printf('%02d', tst_s) as time , return_actual  from p1_channel_detail where channel=9 order by tst desc limit 200")
   rows = cur.fetchall()
   chan9_labels = [row[0] for row in rows]
   chan9_values = [row[1] for row in rows]

   i = 0
   N = len(chan9_labels)
   while i < N / 2 :
      c0 = chan9_labels[i]
      c1 = chan9_values[i]
      chan9_labels[i] = chan9_labels[N-1-i]
      chan9_values[i] = chan9_values[N-1-i]
      chan9_labels[N-1-i] = c0
      chan9_values[N-1-i] = c1
      i += 1

   cur= conn.cursor()
   cur.execute("select printf('%02d', tst_hr) ||':'|| printf('%02d', tst_m) ||':'|| printf('%02d', tst_s) as time , consumption_high_delta + consumption_low_delta as delta, - return_high_delta - return_low_delta as return_delta from p1_channel_summary where channel=0 order by tst desc limit 96")
   rows = cur.fetchall()
   chan0_day_labels = [row[0] for row in rows]
   chan0_day_values = [row[1] for row in rows]
   chan0_day_return_values = [row[2] for row in rows]

   i = 0
   N = len(chan0_day_labels)
   while i < N / 2 :
      c0 = chan0_day_labels[i]
      c1 = chan0_day_values[i]
      c2 = chan0_day_return_values[i]
      chan0_day_labels[i] = chan0_day_labels[N-1-i]
      chan0_day_values[i] = chan0_day_values[N-1-i]
      chan0_day_return_values[i] = chan0_day_return_values[N-1-i]
      chan0_day_labels[N-1-i] = c0
      chan0_day_values[N-1-i] = c1
      chan0_day_return_values[N-1-i] = c2
      i += 1

   cur= conn.cursor()
   cur.execute("select printf('%02d', tst_hr) ||':'|| printf('%02d', tst_m) ||':'|| printf('%02d', tst_s) as time , consumption_high_delta + consumption_low_delta as delta from p1_channel_summary where channel=1 order by tst desc limit 48")
   rows = cur.fetchall()
   chan1_day_labels = [row[0] for row in rows]
   chan1_day_values = [row[1] for row in rows]

   i = 0
   N = len(chan1_day_labels)
   while i < N / 2 :
      c0 = chan1_day_labels[i]
      c1 = chan1_day_values[i]
      chan1_day_labels[i] = chan1_day_labels[N-1-i]
      chan1_day_values[i] = chan1_day_values[N-1-i]
      chan1_day_labels[N-1-i] = c0
      chan1_day_values[N-1-i] = c1
      i += 1

   consuming_actual = -1.0
   m3_1_consumption = -1.0

   cur= conn.cursor()
   cur.execute("select consumption_actual, return_actual from p1_channel_detail where channel=0 order by tst desc limit 1")
   rows = cur.fetchall()
   for row in rows: 
      receiving_actual = int(row[0])
      returning_actual = int(row[1])

   cur.execute("select consumption_high from p1_channel_detail where channel=1 order by tst desc limit 1")
   rows = cur.fetchall()
   for row in rows: 
      m3_1_consumption= row[0]
   now = datetime.datetime.now()

   cur= conn.cursor()
   cur.execute("select return_actual from p1_channel_detail where channel=9 order by tst desc limit 1")
   rows = cur.fetchall()
   for row in rows: 
      producing_actual = int(row[0])
   consuming_actual = producing_actual + receiving_actual - returning_actual 
   cur.execute("select consumption_high from p1_channel_detail where channel=1 order by tst desc limit 1")
   rows = cur.fetchall()
   for row in rows: 
      m3_1_consumption= row[0]
   now = datetime.datetime.now()




   timeString = now.strftime("%y-%m-%d %H:%M")
   templateData = {
      'title' : main_menu[menu_idx][0],
      'app': app_name,
      'time': timeString,
      'consuming_actual': consuming_actual,
      'receiving_actual': receiving_actual,
      'returning_actual': returning_actual,
      'm3_1_consumption': m3_1_consumption,
      'producing_actual': producing_actual,
      'main_menu'       : main_menu
      }
   return render_template('index.html', **templateData,
       chan0_labels=chan0_labels, chan0_values=chan0_values, chan0_return_values=chan0_return_values, chan9_values=chan9_values, 
       chan0_day_labels=chan0_day_labels, chan0_day_values=chan0_day_values, chan0_day_return_values=chan0_day_return_values,
       chan1_day_labels=chan1_day_labels, chan1_day_values=chan1_day_values)
