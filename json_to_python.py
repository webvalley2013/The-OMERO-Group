import requests
import json

data = requests.get("http://192.168.205.10/pl.json")
#data.content displays
jsonloaded = data.json()
#json.dumps(jsonloaded)
#This returns a list, whosefirst element is the desired dictionary.
print jsonloaded 


