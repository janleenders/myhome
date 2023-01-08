# Name: solar.py
# Author: Jan Leenders
# Description: 
#    Defines the function(s) to get the solar data (only for supported systems). Currently:
#        enphase
#        fronius
#

import requests
import json

session = requests.Session() # setup a session on behalf of requests to solar system

def get_datapoint(solar_system, solar_request_path ):
   return_value= {'actual': 0.0, 'total': 0.0}

   try:
      if solar_system == 'enphase':
         watt_production_data = session.get(solar_request_path  + '/api/v1/production').text
         return_value['actual'] = json.loads(watt_production_data)["wattsNow"]
         return_value['total']  = float(json.loads(watt_production_data)["wattHoursLifetime"]) / 1000 # should be in kWh
      if solar_system == 'fronius':
         watt_production_data = session.get(solar_request_path  + 
                    '/solar_api/v1/GetInverterRealtimeData.cgi?Scope=System&DataCollection=CommonInverterData').text
         return_value['actual'] = json.loads(watt_production_data)["Body"]["Data"]["PAC"]["Values"]["1"]
         return_value['total']  = float(json.loads(watt_production_data)["Body"]["Data"]["TOTAL_ENERGY"]["Values"]["1"]) / 1000 # should be in kWh

   except Exception:
      pass

   return return_value
