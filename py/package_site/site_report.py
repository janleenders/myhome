# Name: site_report.py
# Author: Jan Leenders
# Description: 
#    This is the report part of the website
#    Can generate data on day, month or year level.
#

from flask import Flask, render_template
from datetime import *
import sqlite3
import requests
import json

levels = [ ["Uur", "/report?l=h"], ["Dag", "/report?l=d"], ["Maand", "/report?l=m"], ["Jaar", "/report?l=y"]]

def set_scope(level, period):
   return_val = {'lbl': 'Dag', 'l': 'd', 'p': 0}

   if level == 'y': 
      return_val['lbl'] = 'Jaar'
      return_val['l'] = 'y'
   if level == 'm': 
      return_val['lbl'] = 'Maand'
      return_val['l'] = 'm'
   if level == 'h': 
      return_val['lbl'] = 'Uur'
      return_val['l'] = 'h'

   try:
      p = int(period)
      if p > 0: p = 0      
   except Exception:
      p = 0
   
   return_val['p'] = p
   
   return return_val
   
def show_report(main_menu, menu_idx, app_name, level, period, database_path):
   
   scope = set_scope(level, period)

   try:
      conn
   except Exception:
      conn = sqlite3.connect(database_path)
   
   cur= conn.cursor()
   if level == 'h':
      query_select = "tst_date || printf('%02d',tst_hr) as interval"
      query_group_by = "interval order by interval asc"
      period -= 0
      interval = 25 # always show 24 hours
      date_start = datetime.today() - timedelta(days=-period)
   elif level == 'm':
      query_select = "printf('%02d',tst_y)||printf('%02d',tst_month) as interval"
      query_group_by = "interval order by tst_y asc, tst_month asc"
      period -= 13
      interval = 13 # Show 12 months
      date_start = datetime.today() - timedelta(days=-period*30)
   elif level == 'y':
      query_select = "tst_y"
      query_group_by = "tst_y order by tst_y asc"
      period -= 4
      interval = 5 # show 5 years when available
      date_start = datetime.today() - timedelta(days=-period*365)
   else: # level 'd' is the default
      query_select = "tst_date"
      query_group_by = "tst_date order by tst_date asc"
      period -= 31
      interval = 32 # always show 31 days
      date_start = datetime.today() - timedelta(days=-period)
      
   query = ("select " + query_select + 
                   ", max(consumption_high) + max(consumption_low) as max_cons" +
                   ", max(return_high) + max(return_low) as max_return" + 
                   ", min(consumption_high) + min(consumption_low) as min_cons" +
                   ", min(return_high) + min(return_low) as min_return" + 
                   "  from p1_channel_summary where channel=0 and tst_date >= '" + date_start.strftime("%y%m%d") + 
                   "' group by " + query_group_by + " limit " + str(interval))
   cur.execute(query)
   rows = cur.fetchall()
   chan0_day_labels = [row[0] for row in rows]
   chan0_day_values = [row[1] for row in rows]
   chan0_day_return_values = [row[2] for row in rows]
   chan9_day_production_values = [row[2] for row in rows]
   chan0_day_values_min = [row[3] for row in rows]
   chan0_day_return_values_min = [row[4] for row in rows]
   chan9_day_production_values_min = [row[4] for row in rows]
      
   query = ("select " + query_select + 
            ", max(return_high) + max(return_low) as max_return" + 
            ", min(return_high) + min(return_low) as min_return" + 
            "  from p1_channel_summary where channel=9 and tst_date >= '" + date_start.strftime("%y%m%d") + 
            "' group by " + query_group_by + " limit " + str(interval))
   cur.execute(query)
   rows = cur.fetchall()
   chan9_day_labels = [row[0] for row in rows]
   chan9_day_return_values = [row[1] for row in rows]
   chan9_day_return_values_min = [row[1] for row in rows]
      
   N = len(chan0_day_labels)
   NP = len(chan9_day_labels) #length of production array
   i = 0 # index for consumption array (channel = 0)
   j = 0 # index for production array (channel = 9)      
   while i < N and j < NP:
      if j == 0: 
         chan9_day_production_values_prev = chan9_day_return_values[j]
         chan9_day_production_values_min_prev = chan9_day_return_values_min[j]
      if chan9_day_labels[j] == chan0_day_labels[i]:
         chan9_day_production_values[i] = chan9_day_return_values[j]
         chan9_day_production_values_prev = chan9_day_return_values[j]
         chan9_day_production_values_min[i] = chan9_day_return_values_min[j]
         chan9_day_production_values_min_prev = chan9_day_return_values_min[j]
         i += 1
         j += 1
      elif chan9_day_labels[j] > chan0_day_labels[i]:
         chan9_day_production_values[i] = chan9_day_production_values_prev
         chan9_day_production_values_min[i] = chan9_day_production_values_min_prev
         i += 1

   delta0 = 0
   delta0_return = 0
   delta9_production = 0
   i = 0 # index for consumption array (channel = 0)
   while i < N:
      if i == 0:
         delta0 = chan0_day_values_min[i]
         delta0_return = chan0_day_return_values_min[i]
         delta9_production = chan9_day_production_values_min[i]
         # chan0_day_labels[i] = ""
      else:
         delta0 = delta0 + chan0_day_values[i-1]
         delta0_return = delta0_return + chan0_day_return_values[i-1]
         delta9_production = delta9_production + chan9_day_production_values[i-1]
         chan0_day_return_values[i-1] = - chan0_day_return_values[i-1]
         chan9_day_production_values[i-1] = - chan9_day_production_values[i-1]
      chan0_day_values[i] -= delta0
      chan0_day_return_values[i] -= delta0_return
      chan9_day_production_values[i] -= delta9_production
      i += 1
   if N > 0: 
      chan0_day_return_values[N-1] = - chan0_day_return_values[N-1]
      chan9_day_production_values[N-1] = - chan9_day_production_values[N-1]

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

   now = datetime.now()
   timeString = now.strftime("%y-%m-%d %H:%M")
   
   templateData = {
      'title'     : main_menu[menu_idx][0],
      'app'       : app_name,
      'time'      : timeString,
      'level_name': scope['lbl'],
      'level_parameter' : scope['l'],
      'period'    : scope['p'],
      'periodm'   : scope['p'] - 1,
      'periodp'   : scope['p'] + 1,
      'levels'    : levels,
      'main_menu' : main_menu
      }
   return render_template('report.html', **templateData,
       chan0_day_labels=chan0_day_labels, chan0_day_values=chan0_day_values, chan0_day_return_values=chan0_day_return_values,
       chan9_day_production_values=chan9_day_production_values,
       chan1_day_labels=chan1_day_labels, chan1_day_values=chan1_day_values)
