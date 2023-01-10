# Name: site_dashboard.py
# Author: Jan Leenders
# Description: 
#    Shows actual and today information concerning the energie usage.
#

from flask import Flask, render_template
from datetime import *
import sqlite3
import requests
import json
    
def show_dashboard(main_menu, menu_idx, app_name, interval_hrs, history_hrs, database_path, solar_system, solar_request_path):

   try:
      conn
   except Exception:
      conn = sqlite3.connect(database_path)

   now = datetime.now()
   timeString = now.strftime("%y-%m-%d %H:%M")
   cur_hr = int(now.strftime("%H"))

   # read data as input for the graphs. Start with electricity
   cur = conn.cursor()
   cur.execute("select printf('%02d', tst_hr) ||':'|| printf('%02d', tst_m) ||':'|| printf('%02d', tst_s) as time , " + 
                     " consumption_actual, return_actual  from p1_channel_detail " + 
                     " where channel=0 and " + 
                     "       tst_hr >= " + str(cur_hr + history_hrs - interval_hrs) +
                     "   and tst_hr <= " + str(cur_hr + history_hrs) + 
                     "   and tst_date = substr(replace(date('now'), '-', ''), 3, 6) order by tst asc ")
   rows                = cur.fetchall()
   chan0_labels        = [row[0] for row in rows]
   chan0_values        = [row[1] for row in rows]
   chan0_return_values = [row[2] for row in rows]
   chan0_production_values = [row[1] for row in rows] # creating the array with same dimension as query result
   chan0_usage_values = [row[1] for row in rows]      # idem

   cur.execute("select printf('%02d', tst_hr) ||':'|| printf('%02d', tst_m) ||':'|| printf('%02d', tst_s) as time , " + 
                     " return_actual  from p1_channel_detail " + 
                     " where channel=9 and "+ 
                     "       tst_hr >= " + str(cur_hr + history_hrs - interval_hrs) +
                     "   and tst_hr <= " + str(cur_hr + history_hrs) + 
                     "   and tst_date = substr(replace(date('now'), '-', ''), 3, 6) order by tst asc")
   rows = cur.fetchall()
   chan9_labels = [row[0] for row in rows]
   chan9_values = [row[1] for row in rows]

   # Match the timestamps of the P1 data (channel 0) and the solar data (channel 9)
   # the solar data will be projected in array chan0_production_values
   i = 0
   j = 0
   N = len(chan0_values)
   M = len(chan9_values)
   while i < N and j < M :
      if chan9_labels[j] == chan0_labels[i]:
         chan0_production_values[i] = chan9_values[j]
         i += 1
         j += 1
      elif chan9_labels[j] > chan0_labels[i]:
         chan0_production_values[i] = int(0)
         i += 1
      else: 
         j += 1

   # calculating actual net usage
   i = 0
   while i < N:
      chan0_return_values[i] = - chan0_return_values[i]
      chan0_usage_values[i] = chan0_values[i] + chan0_production_values[i] + chan0_return_values[i] 
      i += 1
   
   # Get data relating to channel 1 until 4 from the P1 meter.
   cur.execute("select printf('%02d', tst_hr) ||':'|| printf('%02d', tst_m) ||':'|| printf('%02d', tst_s) as time , " + 
                     " consumption_high + consumption_low  from p1_channel_detail " + 
                     " where channel=1 and " + 
                     "       tst_hr >= " + str(cur_hr + history_hrs - interval_hrs) +
                     "   and tst_hr <= " + str(cur_hr + history_hrs) + 
                     "   and tst_date = substr(replace(date('now'), '-', ''), 3, 6) order by tst asc")

   rows                = cur.fetchall()
   chan1_labels        = [row[0] for row in rows]
   chan1_values        = [row[1] for row in rows]

   cur.execute("select printf('%02d', tst_hr) ||':'|| printf('%02d', tst_m) ||':'|| printf('%02d', tst_s) as time , " + 
                     " consumption_high + consumption_low  from p1_channel_detail " + 
                     " where channel=2 and " + 
                     "       tst_hr >= " + str(cur_hr + history_hrs - interval_hrs) +
                     "   and tst_hr <= " + str(cur_hr + history_hrs) + 
                     "   and tst_date = substr(replace(date('now'), '-', ''), 3, 6) order by tst asc")

   rows                = cur.fetchall()
   chan2_labels        = [row[0] for row in rows]
   chan2_values        = [row[1] for row in rows]

   cur.execute("select printf('%02d', tst_hr) ||':'|| printf('%02d', tst_m) ||':'|| printf('%02d', tst_s) as time , " + 
                     " consumption_high + consumption_low  from p1_channel_detail " + 
                     " where channel=3 and " + 
                     "       tst_hr >= " + str(cur_hr + history_hrs - interval_hrs) +
                     "   and tst_hr <= " + str(cur_hr + history_hrs) + 
                     "   and tst_date = substr(replace(date('now'), '-', ''), 3, 6) order by tst asc")

   rows                = cur.fetchall()
   chan3_labels        = [row[0] for row in rows]
   chan3_values        = [row[1] for row in rows]

   cur.execute("select printf('%02d', tst_hr) ||':'|| printf('%02d', tst_m) ||':'|| printf('%02d', tst_s) as time , " + 
                     " consumption_high + consumption_low  from p1_channel_detail " + 
                     " where channel=4 and " + 
                     "       tst_hr >= " + str(cur_hr + history_hrs - interval_hrs) +
                     "   and tst_hr <= " + str(cur_hr + history_hrs) + 
                     "   and tst_date = substr(replace(date('now'), '-', ''), 3, 6) order by tst asc")

   rows                = cur.fetchall()
   chan4_labels        = [row[0] for row in rows]
   chan4_values        = [row[1] for row in rows]

   # calculate the delta's for each of channel 1 to 4.
   i = 0
   N = len(chan1_labels)
   while i < N:
      if i == 0: chan1_value_delta = chan1_values[i]
      chan1_values[i] -= chan1_value_delta
      chan1_value_delta += chan1_values[i]
      i += 1

   i = 0
   N = len(chan2_labels)
   while i < N:
      if i == 0: chan2_value_delta = chan2_values[i]
      chan2_values[i] -= chan_value_delta
      chan2_value_delta += chan2_values[i]
      i += 1

   i = 0
   N = len(chan3_labels)
   while i < N:
      if i == 0: chan3_value_delta = chan3_values[i]
      chan3_values[i] -= chan3_value_delta
      chan3_value_delta += chan3_values[i]
      i += 1

   i = 0
   N = len(chan4_labels)
   while i < N:
      if i == 0: chan4_value_delta = chan4_values[i]
      chan4_values[i] -= chan4_value_delta
      chan4_value_delta += chan4_values[i]
      i += 1
      
   receiving_actual = int(0)
   returning_actual = int(0)
   receiving_today = float(0)
   returning_today = float(0)
   cur.execute("select consumption_actual, return_actual, consumption_high + consumption_low, return_high+ return_low from p1_channel_detail where channel=0 order by tst desc limit 1")
   rows = cur.fetchall()
   for row in rows: 
      receiving_actual = int(row[0])
      returning_actual = int(row[1])
      receiving_today = float(row[2])
      returning_today = float(row[3])

   nrofrows = cur.execute("select consumption_high + consumption_low, return_high + return_low from p1_channel_detail where " + 
               " tst_date < substr(replace(date('now'),'-',''),3,6) " + 
               " and channel=0 order by tst desc limit 1")
   rows = cur.fetchall()
   for row in rows: 
      receiving_today  -= float(row[0])
      returning_today  -= float(row[1])
   receiving_today = round(receiving_today, 3)
   returning_today = round(returning_today, 3)
   
   producing_actual = int(0)
   producing_today = float(0)
   cur.execute("select return_actual, return_high + return_low from p1_channel_detail where channel=9 order by tst desc limit 1")
   rows = cur.fetchall()
   for row in rows: 
      producing_actual = int(row[0])
      producing_today  = float(row[1])

   cur.execute("select return_high + return_low from p1_channel_detail where " + 
               " tst_date < substr(replace(date('now'),'-',''),3,6) " + 
               " and channel=9 order by tst desc limit 1")
   rows = cur.fetchall()
   for row in rows: 
      producing_today  -= float(row[0])
   producing_today = round(producing_today, 3)
      
   consuming_actual = producing_actual + receiving_actual - returning_actual # calculate the actual net usage
   consuming_today = round(producing_today + receiving_today - returning_today,3) # calculate the today net usage

   cur.execute("select channel, max(consumption_high), round(max(consumption_high) - min(consumption_high), 3) from p1_channel_detail " +
               "where channel in (1,2,3,4) and tst_date = substr(replace(date('now'),'-',''),3,6) group by channel order by channel")
   rows = cur.fetchall()
   m3_consumption_value = [row[1] for row in rows]
   m3_consumption_channel = [row[0] for row in rows]
   m3_consumption_today = [row[2] for row in rows]
   
   conn.close()
            

   templateData = {
      'title' : main_menu[menu_idx][0],
      'app': app_name,
      'timeString': timeString,
      'history_hrs'     : history_hrs, 
      'interval_hrs'    : interval_hrs, 
      'consuming_actual': consuming_actual,
      'receiving_actual': receiving_actual,
      'returning_actual': returning_actual,
      'producing_actual': producing_actual,
      'consuming_today' : consuming_today,
      'receiving_today' : receiving_today,
      'returning_today' : returning_today,
      'producing_today' : producing_today,
      'm3_consumption'         : m3_consumption_value,
      'm3_consumption_channel' : m3_consumption_channel,
      'm3_consumption_today'   : m3_consumption_today,
      'main_menu'       : main_menu,
      'solar_system' : solar_system,
      'solar_request_path' : solar_request_path
      }
   return render_template('index.html', **templateData,
       chan0_labels=chan0_labels, chan0_values=chan0_values, chan0_return_values=chan0_return_values, 
       chan9_values=chan0_production_values, chan0_usage_values=chan0_usage_values,
       chan1_labels=chan1_labels, chan1_values=chan1_values,
       chan2_labels=chan2_labels, chan2_values=chan2_values,
       chan3_labels=chan3_labels, chan3_values=chan3_values,
       chan4_labels=chan4_labels, chan4_values=chan4_values
       )
