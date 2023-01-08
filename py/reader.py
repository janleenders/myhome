# Name: P1_reader (P1R)
# Author: Jan Leenders
# Version: 1.0 (28-12-2022)
# Description: 
#    periodically reads data from the P1 smart meter port (the Netherlands) and also from the solar unit (envoy in this case)
#    based on http://domoticx.com/p1-poort-slimme-meter-telegram-uitlezen-met-python/
# Details:
#    logging is contained in the ../log directory
#    the database is contained in the ../db directory . It concerns an SQLite3 database.
#    Data concepts:
#    - each datastream is a 'channel'.
#          channel 0: usage (and return) electricity
#          channel 1-4: Gas, water, other (connected to the smart meter). In this code channel 1 concerns gas. 
#          channel 9: production of electricity (solar system). Is not part of the P1 port data; results from a json request towards the solar system.
#
#    Table structure:
#       CREATE TABLE p1_channel_summary 
#              (channel int, tst text, tst_date text, tst_y int, tst_month int, tst_day int, tst_hr int, tst_m int, tst_s int, 
#               consumption_high real, consumption_low real, return_high real, return_low real, 
#               consumption_high_delta real, consumption_low_delta real, return_high_delta real, return_low_delta real);
#       CREATE TABLE p1_channel_detail 
#              (channel int, tst text, tst_date text, tst_y int, tst_month int, tst_day int, tst_hr int, tst_m int, tst_s int, 
#               consumption_high real, consumption_low real, return_high real, return_low real, 
#               consumption_actual real, return_actual real);
#
# P1R-backlog items: 
#    None at this moment

import re
import os
import serial   # pip install pyserial
import time
import sqlite3
import logging
import sys
import requests
import json
from package_generic import parameters
from package_reader import solar
from datetime import datetime, timedelta

args = sys.argv[1:] # get the commandline arguments. the first one is the file (location) with the configuration parameters.

# Set your own preferences here, or use the config file.
param_dict = {
                "folder_path": ["/home/pi/myhome/", "str", False],
                "interval_data_details_watt": ["20", "int", False],
                "interval_data_details_m3": ["300","int",False],
                "interval_data_summary": ["3600","int",False],
                "database": ["db/P1R.db","str",False],
                "logging": ["log/","str",False],
                "solar_path": ["http://192.168.2.4","str",False],
                "solar_system": ["enphase","str",False],
		"serial_port_name" : ["/dev/ttyUSB0", "str", False]
             }

if parameters.setParameters(args[0], param_dict):
    parameters.showParameters(param_dict)
    serial_port_name = param_dict["serial_port_name"][0]
    folder_path = param_dict["folder_path"][0]
    interval_data_details_watt  = int(param_dict["interval_data_details_watt"][0]) # Time interval between registration of electricity details in seconds.
    interval_data_details_m3    = int(param_dict["interval_data_details_m3"][0]) # Time interval between registration of m3 (gas or water) details in seconds.
    interval_data_summary       = int(param_dict["interval_data_summary"][0]) # Time interval between registration of summary data in seconds.
    db = folder_path + param_dict["database"][0]
    log_path = folder_path + param_dict["logging"][0]
    solar_request_path = param_dict["solar_path"][0] # to request data from the solar system
    solar_system = param_dict["solar_system"][0] # to request data from the solar system
else:
    print("Error reading parameters from file. Execution aborted")
    quit()

timestr = time.strftime("%Y%m%d")
os.makedirs(log_path, exist_ok=True)

f = log_path + str(timestr) + ".log"

log_format = "%(asctime)s :: %(levelname)s :: %(name)s :: %(filename)s :: %(message)s"
# logging.basicConfig(level='WARNING', format=log_format, datefmt='%d-%b-%y %H:%M:%S')
logging.basicConfig(
    filename=f, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)

# Seriele poort confguratie
ser = serial.Serial()

# DSMR 2.2 > 9600 7E1:
#ser.baudrate = 9600
#ser.bytesize = serial.SEVENBITS
#ser.parity = serial.PARITY_EVEN
#ser.stopbits = serial.STOPBITS_ONE

# DSMR 4.0/4.2 > 115200 8N1:
ser.baudrate = 115200
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE

ser.xonxoff = 0
ser.rtscts = 0
ser.timeout = 12
ser.port = serial_port_name
ser.close()

watt = []
watt_return = []

P1_timestamp = None            # Timestamp of the last record from the P1 meter
watt_consumption_high = None
watt_consumption_low = None
watt_return_high = None
watt_return_low = None
watt_production = None # used for the solar system production
prev_watt_consumption_high = None
prev_watt_consumption_low = None
prev_watt_return_high = None
prev_watt_return_low = None
prev_watt_production = None # used for the solar system production
m3_1_consumption = None
m3_2_consumption = None
m3_3_consumption = None
m3_4_consumption = None
prev_m3_1_consumption = None
prev_m3_2_consumption = None
prev_m3_3_consumption = None
prev_m3_4_consumption = None
m3_1_timestamp = None          # Timestamp of the last data concerning channel 1
m3_2_timestamp = None          # Timestamp of the last data concerning channel 2
m3_3_timestamp = None          # Timestamp of the last data concerning channel 1
m3_4_timestamp = None          # Timestamp of the last data concerning channel 2


def expires(secnds):
    future = datetime.now() + timedelta(seconds=int(secnds))
    return int(future.strftime("%s"))

def average(lst):
    if len(lst)>0:
        return round(int(sum(lst) / len(lst)))
    else:
        return 0

summary_timestamp = expires(interval_data_summary)
details_timestamp_watt = expires(interval_data_details_watt)
details_timestamp_m3 = expires(interval_data_details_m3)

logging.warning("Start collecting")

while True:
    ser.open()
    checksum_found = False
    while not checksum_found:
        timestamp = int(time.time())

        try:
            ser_data = ser.readline()  # Read in serial line.
            # Strip spaces and blank lines
            ser_data = ser_data.decode('ascii').strip()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.warning(str(e) + " | " + str(exc_type) +
                            " | " + str(fname) + " | " + str(exc_tb.tb_lineno))
            pass

        try:
            if re.match(r'(?=0-0:1.0.0)', ser_data):  # 0-0:1.0.0 = Contains timestamp from the P1 meter
                P1_timestamp = ser_data[10:-2] 

            if re.match(r'(?=1-0:1.7.0)', ser_data):  # 1-0:1.7.0 = Actual usage in kW
                kw = ser_data[10:-4]
                # vermengvuldig met 1000 voor conversie naar kW en rond het af
                watt.append(int(float(kw) * 1000))

            if re.match(r'(?=1-0:2.7.0)', ser_data):  # 1-0:2.7.0 = Actual return in kW
                kw = ser_data[10:-4] 
                # vermengvuldig met 1000 voor conversie naar kW en rond het af
                watt_return.append(int(float(kw) * 1000))

            if re.match(r'(?=1-0:1.8.1)', ser_data):
                watt_consumption_high = ser_data[10:-5]
                if prev_watt_consumption_high is None: prev_watt_consumption_high = watt_consumption_high

            if re.match(r'(?=1-0:1.8.2)', ser_data):
                watt_consumption_low = ser_data[10:-5]
                if prev_watt_consumption_low is None: prev_watt_consumption_low = watt_consumption_low

            if re.match(r'(?=1-0:2.8.1)', ser_data):
                watt_return_high = ser_data[10:-5]
                if prev_watt_return_high is None: prev_watt_return_high = watt_return_high

            if re.match(r'(?=1-0:2.8.2)', ser_data):
                watt_return_low = ser_data[10:-5]
                if prev_watt_return_low is None: prev_watt_return_low = watt_return_low

            if re.match(r'(?=0-1:24.2.1)', ser_data):  # 0-1:24.2.1 = Last 5 minute value in m3, including decimals 
                m3_1_timestamp = ser_data[11:23]  # Take out the timestamp part (YYMMDDHHMMSS)
                m3_1_consumption = ser_data[26:-4]  
                if prev_m3_1_consumption is None : prev_m3_1_consumption = m3_1_consumption 

            if re.match(r'(?=0-2:24.2.1)', ser_data):  # 0-2:24.2.1 = Last 5 minute value in m3, including decimals 
                m3_2_timestamp = ser_data[11:23]  # Take out the timestamp part (YYMMDDHHMMSS)
                m3_2_consumption = ser_data[26:-4] 
                if prev_m3_2_consumption is None : prev_m3_2_consumption = m3_2_consumption 

            if re.match(r'(?=0-3:24.2.1)', ser_data):  # 0-3:24.2.1 = Last 5 minute value in m3, including decimals 
                m3_3_timestamp = ser_data[11:23]  # Take out the timestamp part (YYMMDDHHMMSS)
                m3_3_consumption = ser_data[26:-4]
                if prev_m3_3_consumption is None : prev_m3_3_consumption = m3_2_consumption 

            if re.match(r'(?=0-4:24.2.1)', ser_data):  # 0-4:24.2.1 = Last 5 minute value in m3, including decimals 
                m3_4_timestamp = ser_data[11:23]  # Take out the timestamp part (YYMMDDHHMMSS)
                m3_4_consumption = ser_data[26:-4]
                if prev_m3_4_consumption is None : prev_m3_4_consumption = m3_2_consumption 

            # Check when the exclamation mark is received (end of data)
            if re.match(r'(?=!)', ser_data, 0):
                checksum_found = True

                try:
                    conn
                except Exception:
                    conn = sqlite3.connect(db)

                try:
                    if timestamp >= details_timestamp_watt:
                        # Get the actual solar system data
                        solar_datapoint = solar.get_datapoint(solar_system, solar_request_path)
                        print(solar_request_path)
                        print(solar_system)
                        print(solar_datapoint)
                        watt_production_actual = int(solar_datapoint['actual'])
                        watt_production_production = float(solar_datapoint['total'])
                        if watt_production_production == float(0.0): # no solar data available at this moment.
                            # Get the last value from the database. Solar system is down of sleeping. 
                            cur= conn.cursor()
                            cur.execute("select return_high + return_low from p1_channel_detail where channel=9 order by tst desc limit 1")
                            rows = cur.fetchall()                            
                            for row in rows: watt_production = float(row[0])
                        if not prev_watt_production:
                            prev_watt_production = watt_production
                        avg_watt = average(watt)
                        avg_watt_return = average(watt_return) 
                        conn.execute("""INSERT INTO p1_channel_detail (channel, tst, tst_date, tst_y, tst_month, tst_day, tst_hr, tst_m, tst_s, 
                                                    consumption_high, consumption_low, return_high, return_low, consumption_actual, return_actual)
                                    VALUES (0,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", [P1_timestamp, P1_timestamp[0:6],
                                                                  int(P1_timestamp[0:2]),int(P1_timestamp[2:4]),int(P1_timestamp[4:6]),
                                                                  int(P1_timestamp[6:8]),int(P1_timestamp[8:10]),int(P1_timestamp[10:12]),
                                                                  float(watt_consumption_high), float(watt_consumption_low), 
                                                                  float(watt_return_high), float(watt_return_low), float(avg_watt), float(avg_watt_return)])
                        conn.commit()
                        conn.execute("""INSERT INTO p1_channel_detail (channel, tst, tst_date, tst_y, tst_month, tst_day, tst_hr, tst_m, tst_s, 
                                                    consumption_high, consumption_low, return_high, return_low, consumption_actual, return_actual)
                                    VALUES (9,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", [P1_timestamp, P1_timestamp[0:6],
                                                                  int(P1_timestamp[0:2]),int(P1_timestamp[2:4]),int(P1_timestamp[4:6]),
                                                                  int(P1_timestamp[6:8]),int(P1_timestamp[8:10]),int(P1_timestamp[10:12]), 0.0, 0.0,
                                                                  float(watt_production), 0.0, 0.0, watt_production_actual])
                        conn.commit()
                        details_timestamp_watt = expires(interval_data_details_watt)
                        watt = []
                        watt_return = []

                    if timestamp >= details_timestamp_m3:
                        # Device connected to channel 1
                        if m3_1_consumption:
                            conn.execute("""INSERT INTO p1_channel_detail (channel, tst, tst_date, tst_y, tst_month, tst_day, tst_hr, tst_m, tst_s, 
                                                        consumption_high, consumption_low, return_high, return_low)
                                        VALUES (1,?,?,?,?,?,?,?,?,?,?,?,?)""", [P1_timestamp, P1_timestamp[0:6],
                                                                      int(P1_timestamp[0:2]),int(P1_timestamp[2:4]),int(P1_timestamp[4:6]),
                                                                      int(P1_timestamp[6:8]),int(P1_timestamp[8:10]),int(P1_timestamp[10:12]),
                                                                      float(m3_1_consumption), 0.0, 0.0, 0.0])
                            conn.commit()

                        # Device connected to channel 2
                        if m3_2_consumption:
                            conn.execute("""INSERT INTO p1_channel_detail (channel, tst, tst_date, tst_y, tst_month, tst_day, tst_hr, tst_m, tst_s, 
                                                        consumption_high, consumption_low, return_high, return_low)
                                        VALUES (2,?,?,?,?,?,?,?,?,?,?,?,?)""", [P1_timestamp, P1_timestamp[0:6],
                                                                      int(P1_timestamp[0:2]),int(P1_timestamp[2:4]),int(P1_timestamp[4:6]),
                                                                      int(P1_timestamp[6:8]),int(P1_timestamp[8:10]),int(P1_timestamp[10:12]),
                                                                      float(m3_2_consumption), 0.0, 0.0, 0.0])
                            conn.commit()

                        # Device connected to channel 3
                        if m3_3_consumption:
                            conn.execute("""INSERT INTO p1_channel_detail (channel, tst, tst_date, tst_y, tst_month, tst_day, tst_hr, tst_m, tst_s, 
                                                        consumption_high, consumption_low, return_high, return_low)
                                        VALUES (3,?,?,?,?,?,?,?,?,?,?,?,?)""", [P1_timestamp, P1_timestamp[0:6],
                                                                      int(P1_timestamp[0:2]),int(P1_timestamp[2:4]),int(P1_timestamp[4:6]),
                                                                      int(P1_timestamp[6:8]),int(P1_timestamp[8:10]),int(P1_timestamp[10:12]),
                                                                      float(m3_3_consumption), 0.0, 0.0, 0.0])
                            conn.commit()

                        # Device connected to channel 4
                        if m3_4_consumption:
                            conn.execute("""INSERT INTO p1_channel_detail (channel, tst, tst_date, tst_y, tst_month, tst_day, tst_hr, tst_m, tst_s, 
                                                        consumption_high, consumption_low, return_high, return_low)
                                        VALUES (4,?,?,?,?,?,?,?,?,?,?,?,?)""", [P1_timestamp, P1_timestamp[0:6],
                                                                      int(P1_timestamp[0:2]),int(P1_timestamp[2:4]),int(P1_timestamp[4:6]),
                                                                      int(P1_timestamp[6:8]),int(P1_timestamp[8:10]),int(P1_timestamp[10:12]),
                                                                      float(m3_4_consumption), 0.0, 0.0, 0.0])
                            conn.commit()


                        details_timestamp_m3 = expires(interval_data_details_m3)

                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    logging.warning(str(e) + " | " + str(exc_type) +
                                    " | " + str(fname) + " | " + str(exc_tb.tb_lineno))
                    pass

                try:
                    if timestamp >= summary_timestamp:
                        watt_consumption_high_delta = float(watt_consumption_high) - float(prev_watt_consumption_high);
                        watt_consumption_low_delta = float(watt_consumption_low) - float(prev_watt_consumption_low);
                        watt_return_high_delta = float(watt_return_high) - float(prev_watt_return_high);
                        watt_return_low_delta = float(watt_return_low) - float(prev_watt_return_low);
                        watt_production_delta = float(watt_production) - float(prev_watt_production);
                        conn.execute("""INSERT INTO p1_channel_summary (channel, tst, tst_date, tst_y, tst_month, tst_day, tst_hr, tst_m, tst_s, 
                                                    consumption_high, consumption_low, return_high, return_low, 
                                                    consumption_high_delta, consumption_low_delta, return_high_delta, return_low_delta)
                                    VALUES (0,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", [P1_timestamp, P1_timestamp[0:6],
                                                                  int(P1_timestamp[0:2]),int(P1_timestamp[2:4]),int(P1_timestamp[4:6]),
                                                                  int(P1_timestamp[6:8]),int(P1_timestamp[8:10]),int(P1_timestamp[10:12]),
                                                                  float(watt_consumption_high), float(watt_consumption_low), 
                                                                  float(watt_return_high), float(watt_return_low), 
                                                                  (watt_consumption_high_delta), (watt_consumption_low_delta),
                                                                  (watt_return_high_delta), (watt_return_low_delta)])
                        conn.commit()
                        conn.execute("""INSERT INTO p1_channel_summary (channel, tst, tst_date, tst_y, tst_month, tst_day, tst_hr, tst_m, tst_s, 
                                                    consumption_high, consumption_low, return_high, return_low, 
                                                    consumption_high_delta, consumption_low_delta, return_high_delta, return_low_delta)
                                    VALUES (9,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", [P1_timestamp, P1_timestamp[0:6],
                                                                  int(P1_timestamp[0:2]),int(P1_timestamp[2:4]),int(P1_timestamp[4:6]),
                                                                  int(P1_timestamp[6:8]),int(P1_timestamp[8:10]),int(P1_timestamp[10:12]),
                                                                  0.0,0.0, 
                                                                  float(watt_production), 0.0, 
                                                                  0.0,0.0,
                                                                  watt_production_delta, 0.0])
                        conn.commit()
                        
                        if m3_1_consumption:
                            m3_1_consumption_delta = float(m3_1_consumption) - float(prev_m3_1_consumption);
                            conn.execute("""INSERT INTO p1_channel_summary (channel, tst, tst_date, tst_y, tst_month, tst_day, tst_hr, tst_m, tst_s, 
                                                        consumption_high, consumption_low, return_high, return_low, 
                                                        consumption_high_delta, consumption_low_delta, return_high_delta, return_low_delta)
                                        VALUES (1,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", [P1_timestamp, P1_timestamp[0:6],
                                                                      int(P1_timestamp[0:2]),int(P1_timestamp[2:4]),int(P1_timestamp[4:6]),
                                                                      int(P1_timestamp[6:8]),int(P1_timestamp[8:10]),int(P1_timestamp[10:12]),
                                                                      float(m3_1_consumption), 0.0, 0.0, 0.0, m3_1_consumption_delta, 0.0, 0.0, 0.0]) 
                            conn.commit()
                            prev_m3_1_consumption = m3_1_consumption

                        if m3_2_consumption:
                            m3_2_consumption_delta = float(m3_2_consumption) - float(prev_m3_2_consumption);
                            conn.execute("""INSERT INTO p1_channel_summary (channel, tst, tst_date, tst_y, tst_month, tst_day, tst_hr, tst_m, tst_s, 
                                                        consumption_high, consumption_low, return_high, return_low, 
                                                        consumption_high_delta, consumption_low_delta, return_high_delta, return_low_delta)
                                        VALUES (2,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", [P1_timestamp, P1_timestamp[0:6],
                                                                      int(P1_timestamp[0:2]),int(P1_timestamp[2:4]),int(P1_timestamp[4:6]),
                                                                      int(P1_timestamp[6:8]),int(P1_timestamp[8:10]),int(P1_timestamp[10:12]),
                                                                      float(m3_2_consumption), 0.0, 0.0, 0.0, m3_2_consumption_delta, 0.0, 0.0, 0.0]) 
                            prev_m3_2_consumption = m3_2_consumption

                        if m3_3_consumption:
                            m3_3_consumption_delta = float(m3_3_consumption) - float(prev_m3_3_consumption);
                            conn.execute("""INSERT INTO p1_channel_summary (channel, tst, tst_date, tst_y, tst_month, tst_day, tst_hr, tst_m, tst_s, 
                                                        consumption_high, consumption_low, return_high, return_low, 
                                                        consumption_high_delta, consumption_low_delta, return_high_delta, return_low_delta)
                                        VALUES (3,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", [P1_timestamp, P1_timestamp[0:6],
                                                                      int(P1_timestamp[0:2]),int(P1_timestamp[2:4]),int(P1_timestamp[4:6]),
                                                                      int(P1_timestamp[6:8]),int(P1_timestamp[8:10]),int(P1_timestamp[10:12]),
                                                                      float(m3_3_consumption), 0.0, 0.0, 0.0, m3_3_consumption_delta, 0.0, 0.0, 0.0]) 
                            prev_m3_3_consumption = m3_3_consumption

                        if m3_4_consumption:
                            m3_4_consumption_delta = float(m3_4_consumption) - float(prev_m3_4_consumption);
                            conn.execute("""INSERT INTO p1_channel_summary (channel, tst, tst_date, tst_y, tst_month, tst_day, tst_hr, tst_m, tst_s, 
                                                        consumption_high, consumption_low, return_high, return_low, 
                                                        consumption_high_delta, consumption_low_delta, return_high_delta, return_low_delta)
                                        VALUES (4,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", [P1_timestamp, P1_timestamp[0:6],
                                                                      int(P1_timestamp[0:2]),int(P1_timestamp[2:4]),int(P1_timestamp[4:6]),
                                                                      int(P1_timestamp[6:8]),int(P1_timestamp[8:10]),int(P1_timestamp[10:12]),
                                                                      float(m3_4_consumption), 0.0, 0.0, 0.0, m3_4_consumption_delta, 0.0, 0.0, 0.0]) 
                            prev_m3_4_consumption = m3_4_consumption

                        summary_timestamp = expires(interval_data_summary)
                        prev_watt_consumption_high = watt_consumption_high
                        prev_watt_consumption_low = watt_consumption_low
                        prev_watt_return_high = watt_return_high
                        prev_watt_return_low = watt_return_low
                        prev_watt_production = watt_production
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    logging.warning(str(e) + " | " + str(exc_type) +
                                    " | " + str(fname) + " | " + str(exc_tb.tb_lineno))
                    pass

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.warning(str(e) + " | " + str(exc_type) +
                            " | " + str(fname) + " | " + str(exc_tb.tb_lineno))
            pass

    ser.close()
conn.close()

