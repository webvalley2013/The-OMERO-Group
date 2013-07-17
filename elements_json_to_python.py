import requests
import json

data = requests.get("http://192.168.205.13/process/detail/1")
#data.content displays
jsonloaded = data.json()
#This returns a list, whose first element is the desired dictionary.
for x in jsonloaded:
	print x

x #Display the components of the dictionary

jinputsinputs = jsonloaded["inputs"]
jinputscode = jsonloaded["code"]
jinputsdescription = jsonloaded["description"]
jinputsauthor = jsonloaded["author"]
jinputsoutputs = jsonloaded["outputs"]
jinputsdate = jsonloaded["date"]
jinputstype = jsonloaded["type"]
jinputsid = jsonloaded["id"]

print jinputsinputs
print jinputscode
print jinputsdescription
print jinputsauthor
print jinputsoutputs
print jinputsdate
print jinputstype
print jinputsid


"""
inputs
code
description
author
outputs
date
type
id

"""
