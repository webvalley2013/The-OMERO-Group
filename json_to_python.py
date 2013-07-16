###Working Omero code

import omero
from omero.gateway import BlitzGateway
from omero.rtypes import *
import omero.scripts as scripts
import json
import requests

data = requests.get("http://192.168.205.10/pl.json")
jsonloaded = data.json()

def runScript():
  client = scripts.client('1_json_python.py', """With this script, you can convert Json files into Python dictionaries.
	In order to run it, just press the Run Script button at the bottom right corner of this window.""",
	version = "0.1",
	authors = ["The OMERO Group", ""],
	institutions = ["WebValley"],
	contact = "webvalley@fbk.eu",)
	conn = BlitzGateway(client_obj=client)


	print jsonloaded

	client.closeSession()

if __name__ == "__main__":
	runScript()





