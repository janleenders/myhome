#
# Name: parameters
# Type: module
# Version: 1.0 (01-01-2023)
# Author: Jan Leenders
# Description: 
#   Can read parameters from an input file and checks for their syntax: int or float
#   needs a parameter dictionary as input:
#   parameters = { {<name>: [<str>,   				#name of the parameter
#                            {'int'|'float'|'str'}, #type of the parameter
#                            {True | False}			#True if updated from file, default value is False
#  						    ]
#                  },
#                   .....
#                  {...,..,...}
#                }

import re

# Reads from an inputfile and updates the parameter values in the parameter dictionary
# returns: True if file could be opened and if it contains one line or more, False otherwise
#
def setParameters(file_name, 		# in:		location and name of the parameter file
                  parameters={}):	# in/out: 	parameter dictionary

   return_value = True
   try:
      f = open(file_name, "r")
   except Exception as e:
      return_value = False
      print("Error opening parameter file: " + str(e))

   nroflines = 0
   while True and return_value:
      fline = f.readline()
      if fline == "": break
      nroflines += 1
      for key in parameters.keys():
         good_result = True
         if re.match(r'\s*' + key + '\s*\=\s*\[.*\]\s*(#.*)?$', fline.strip()):
            parts = fline.strip().split('[')
            new_value_str = (parts[1].split(']'))[0].strip()
            if parameters[key][1] == "int":
               try:
                  new_value = int(new_value_str)
               except:
                  good_result = False
            elif parameters[key][1] == "float":
               try:
                  new_value = float(new_value_str)
               except:
                  good_result = False
            if good_result:
               parameters[key][0] = new_value_str
               parameters[key][2] = good_result	

   return return_value and (nroflines > 0)

# prints (to console) the actual values of the parameters, including whether they are default or updated from the inputfile
# returns: Number of parameters in the dictionary
#
def showParameters(parameters={}):
	nrofparameters = 0
	for key in parameters.keys():
		nrofparameters += 1
		if parameters[key][2]:
			status_value = "updated from input file"
		else: 
			status_value = "Default value"
		print(key + ": " + parameters[key][0] + " # " + status_value)
	return nrofparameters
				
