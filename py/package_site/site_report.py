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

# function to set the correct filter: period and granularity (Year, Month, Day, hour)
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

# function to get the data from one of the m3 channels. To prevent repetitive code.
def get_m3_data(channel_nr, cur, query):
   cur.execute(query)
   rows = cur.fetchall()
   chan_labels = [row[0] for row in rows]
   chan_values_max = [row[1] for row in rows]
   chan_values_min = [row[2] for row in rows]

   # determine the delta's per chosen period
   N = len(chan_labels)
   delta = 0
   i = 0 # index for consumption array
   if N>0:
      consumption = round(float(chan_values_max[N-1]) - float(chan_values_min[0]),3)
   else:
      consumption = float(0)
   while i < N:
      if i == 0:
         delta = chan_values_min[i]
      else:
         delta += chan_values_max[i-1]
      chan_values_max[i] -= delta
      i += 1
   return [chan_labels, chan_values_max, consumption]
   
def show_report(main_menu, menu_idx, app_name, level, period, database_path):
   
   scope = set_scope(level, period)
   level = scope["l"]
   period = int(scope["p"])

   # initialize dictionary to display consumption
   chan_delta = { "0-used": ["Watt used", "kWh", 0], "0-received": ["Watt received", "kWh",0], 
                  "0-returned": ["Watt returned","kWh",0], "0-produced": ["Watt produced", "kWh",0],
                  "1": ["P1 channel 1", "m3",0], "2": ["P1 channel 2", "m3",0], 
                  "3": ["P1 channel 3","m3",0], "4": ["P1 channel 4", "m3",0]}

   try:
      conn
   except Exception:
      conn = sqlite3.connect(database_path)

   # Define the start and enddate needed to perform the right query.
   date_start = date.today()
   cur= conn.cursor()
   if level == 'h':
      # move forward / backward per day. Show data at hour-level
      query_select = "tst_date || printf('%02d',tst_hr) as interval"
      query_group_by = "interval order by interval asc"
      date_start += timedelta(days=period)
      date_end    = date_start # show 1 day
   elif level == 'm':
      # move forward / backward per year. show data at month-level.
      query_select = "printf('%02d',tst_y)||printf('%02d',tst_month) as interval"
      query_group_by = "interval order by tst_y asc, tst_month asc"
      date_start = date_start.replace(day=1, month=1)
      date_start = date_start.replace(year=(date_start.year + int(period)))
      date_end = date_start.replace(year=(date_start.year + 1)) # show 1 year
      date_end = date_end - timedelta(days=1)

   elif level == 'y':
      # move forward / backward per year. Show max 10 years.
      query_select = "tst_y"
      query_group_by = "tst_y order by tst_y asc"
      date_start = date_start.replace(day=1, month=1)
      date_start = date_start.replace(year=(date_start.year + int(period)))
      date_end   = date_start.replace(year=(date_start.year + 10))
   else: # level 'd' is the default. Move forward / backward per month. 
      query_select = "tst_date"
      query_group_by = "tst_date order by tst_date asc"
      date_start = date_start + timedelta(days=period*28)
      date_start = date_start.replace(day=1)
      date_end   = date_start + timedelta(days=32)
      date_end = date_end.replace(day=1)
      date_end   = date_end - timedelta(days=1)

   # Fetch the electricity data, using two queries: first from the P1 meter (channel 0), second from the solar system (channel 9)            
   query = ("select " + query_select + 
                   ", max(consumption_high) + max(consumption_low) as max_cons" +
                   ", max(return_high) + max(return_low) as max_return" + 
                   ", min(consumption_high) + min(consumption_low) as min_cons" +
                   ", min(return_high) + min(return_low) as min_return" + 
                   "  from p1_channel_summary where channel=0 and tst_date >= '" + date_start.strftime("%y%m%d") + "' " +
                   "   and tst_date <= '" + date_end.strftime("%y%m%d") + "' " + 
                   "  group by " + query_group_by )

   cur.execute(query)
   rows = cur.fetchall()
   chan0_labels = [row[0] for row in rows]
   chan0_values = [row[1] for row in rows]
   chan0_return_values = [row[2] for row in rows]
   chan9_production_values = [row[2] for row in rows] # prepare an array of the same dimension as the channel 0 information. Will be populated later on.
   chan0_values_min = [row[3] for row in rows]
   chan0_return_values_min = [row[4] for row in rows]
   chan9_production_values_min = [row[4] for row in rows] # prepare an array of the same dimension as the channel 0 information. Will be populated later on.

   # Getting the channel 9 data from the database (solar system data).      
   query = ("select " + query_select + 
            ", max(return_high) + max(return_low) as max_return" + 
            ", min(return_high) + min(return_low) as min_return" + 
            "  from p1_channel_summary where channel=9 and tst_date >= '" + date_start.strftime("%y%m%d") + "' " + 
            "   and tst_date <= '" + date_end.strftime("%y%m%d") + "' " + 
            " group by " + query_group_by )
   cur.execute(query)
   rows = cur.fetchall()
   chan9_labels = [row[0] for row in rows]
   chan9_return_values = [row[1] for row in rows]
   chan9_return_values_min = [row[2] for row in rows]
      
   # synchronise solar datapoints with the P1 datapoints, to be able to plot it the right way in a graph
   N = len(chan0_labels)
   M = len(chan9_labels) #length of solar array
   i = 0 # index for consumption array (channel = 0)
   j = 0 # index for production array (channel = 9)      
   while i < N and j < M:
      if j == 0: 
         chan9_production_values_prev = chan9_return_values[j]
         chan9_production_values_min_prev = chan9_return_values_min[j]
      if chan9_labels[j] == chan0_labels[i]:
         chan9_production_values[i] = chan9_return_values[j]
         chan9_production_values_prev = chan9_return_values[j]
         chan9_production_values_min[i] = chan9_return_values_min[j]
         chan9_production_values_min_prev = chan9_return_values_min[j]
         i += 1
         j += 1
      elif chan9_labels[j] > chan0_labels[i]:
         chan9_production_values[i] = chan9_production_values_prev
         chan9_production_values_min[i] = chan9_production_values_min_prev
         i += 1

   
   # determine the delta's per chosen period
   delta = 0
   delta_return = 0
   delta_production = 0
   delta_using = 0
   i = 0 # index for consumption array (channel = 0)
   while i < N:
      if i == 0:
         delta = chan0_values_min[i]
         delta_return = chan0_return_values_min[i]
         delta_production = chan9_production_values_min[i]
      else:
         delta += chan0_values[i-1]
         delta_return += chan0_return_values[i-1]
         delta_production += chan9_production_values[i-1]
         chan0_return_values[i-1] = - chan0_return_values[i-1]
         chan9_production_values[i-1] = - chan9_production_values[i-1]
      chan0_values[i] -= delta
      chan0_return_values[i] -= delta_return
      chan9_production_values[i] -= delta_production
      i += 1
   if N > 0: 
      delta += chan0_values[N-1]
      delta_return += chan0_return_values[N-1]
      delta_production += chan9_production_values[N-1]      
      chan0_return_values[N-1] = - chan0_return_values[N-1]
      chan9_production_values[N-1] = - chan9_production_values[N-1]
      chan_delta["0-received"][2] = round(delta - chan0_values_min[0], 3)
      chan_delta["0-returned"][2] = round(delta_return - chan0_return_values_min[0],3)
      chan_delta["0-produced"][2] = round(delta_production - chan9_production_values_min[0],3)
      chan_delta["0-used"][2]     = round(chan_delta["0-received"][2] + chan_delta["0-produced"][2] - chan_delta["0-returned"][2],3)
         
   # assemble the data concerning channel 1 until 4
   query = ("select " + query_select + 
                   ", max(consumption_high) + max(consumption_low) as max_cons" +
                   ", min(consumption_high) + min(consumption_low) as min_cons" +
                   "  from p1_channel_summary where channel=1 and tst_date >= '" + date_start.strftime("%y%m%d") + "' " +
                   "   and tst_date <= '" + date_end.strftime("%y%m%d") + "' " + 
                   "  group by " + query_group_by)

   chan1_data = get_m3_data(1,cur, query)
   chan_delta["1"][2] = chan1_data[2]

   query = ("select " + query_select + 
                   ", max(consumption_high) + max(consumption_low) as max_cons" +
                   ", min(consumption_high) + min(consumption_low) as min_cons" +
                   "  from p1_channel_summary where channel=2 and tst_date >= '" + date_start.strftime("%y%m%d") + "' " + 
                   "   and tst_date <= '" + date_end.strftime("%y%m%d") + "' " + 
                   "  group by " + query_group_by)

   chan2_data = get_m3_data(2,cur, query)
   chan_delta["2"][2] = chan2_data[2]

   query = ("select " + query_select + 
                   ", max(consumption_high) + max(consumption_low) as max_cons" +
                   ", min(consumption_high) + min(consumption_low) as min_cons" +
                   "  from p1_channel_summary where channel=3 and tst_date >= '" + date_start.strftime("%y%m%d") + "' " + 
                   "   and tst_date <= '" + date_end.strftime("%y%m%d") + "' " + 
                   "  group by " + query_group_by)

   chan3_data = get_m3_data(3,cur, query)
   chan_delta["3"][2] = chan3_data[2]

   query = ("select " + query_select + 
                   ", max(consumption_high) + max(consumption_low) as max_cons" +
                   ", min(consumption_high) + min(consumption_low) as min_cons" +
                   "  from p1_channel_summary where channel=4 and tst_date >= '" + date_start.strftime("%y%m%d") + "' " + 
                   "   and tst_date <= '" + date_end.strftime("%y%m%d") + "' " + 
                   "  group by " + query_group_by)

   chan4_data = get_m3_data(4,cur, query)
   chan_delta["4"][2] = chan4_data[2]


   now = datetime.now()
   timeString = now.strftime("%y-%m-%d %H:%M")

   starttimestamp = date_start.strftime('[%d-%m-%y]')
   endtimestamp = date_end.strftime('[%d-%m-%y]')
   
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
      'starttimestamp' : starttimestamp,
      'endtimestamp' : endtimestamp,
      'main_menu' : main_menu,
      'timeString' : timeString
      }
   return render_template('report.html', **templateData,
       chan0_labels=chan0_labels, chan0_values=chan0_values, chan0_return_values=chan0_return_values,
       chan9_production_values=chan9_production_values,
       chan1_labels=chan1_data[0], chan1_values=chan1_data[1],
       chan2_labels=chan2_data[0], chan2_values=chan2_data[1],
       chan3_labels=chan3_data[0], chan3_values=chan3_data[1],
       chan4_labels=chan4_data[0], chan4_values=chan4_data[1],
       chan_delta=chan_delta
       )
