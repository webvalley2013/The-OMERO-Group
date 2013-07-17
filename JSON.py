#!/usr/bin/env python

from omero.gateway import BlitzGateway		# used for connecting to the server
import omero								# contains general OMERO content
import omero.util.script_utils as scriptUtil# used for making the user interface
from omero.rtypes import *					# imports rstring + other data types
import omero.scripts as scripts				# allows for making user interface
from cStringIO import StringIO
from numpy import *							# for array representations
try:
    from PIL import Image
except ImportError:
    import Image
import omero.clients
from omero import client_wrapper
import requests

def generateImports():
	#start imports
	importCode = """
	
	from omero.gateway import BlitzGateway		# used for connecting to the server
	import omero								# contains general OMERO content
	import omero.util.script_utils as scriptUtil# used for making the user interface
	from omero.rtypes import *					# imports rstring + other data types
	import omero.scripts as scripts				# allows for making user interface
	from cStringIO import StringIO
	from numpy import *							# for array representations
	try:
    	from PIL import Image
	except ImportError:
    	import Image
	import omero.clients
	from omero import client_wrapper
	
	"""
	
	return importCode

def generateClient(jsonFilePath):
	#download JSON file
	jsonData = requests.get(jsonFilePath).json()

	#add class initialization beginning
	clientGenerationCode = "nif __name__ == (\"__main__\")"
	
	#add data type initialization
	clientGenerationCode += "\n\tdataTypes = [rstring('Dataset'), rstring('Image')]"

	#add name of code
	clientGenerationCode += "\n\n\tclient = scripts.client(\"" + jsonData["code"] + "\","
	
	#add code description
	clientGenerationCode += "\"" + jsonData["description"] + "\","
	
	#default inputs
	clientGenerationCode += "scripts.String(\"Data_Type\", optional = False, grouping = \"1\", description = \"Choose source of images (only Images and Datasets supported)\", values = dataTypes, default = \"Image\"),"
	clientGenerationCode += "scripts.List(\"IDs\", optional = False, grouping = \"1.1\", description = \"List of Image IDs or Dataset IDs to use.\").ofType(rlong(0)),"
	
	#json inputs
	groupingNumber = 1
	
	allInputs = jsonData["inputs"]
	
	for eachInput in allInputs:
		#put everything in separate places...?
		groupingNumber += 1
		
		if (eachInput["type"] == "url_list"): #makes no sense??!
			#add input ID
			clientGenerationCode += " scripts.String(\"" + eachInput["label"] + "\","
			
			#add input optional setting
			clientGenerationCode += " optional = False" + ","
			
			#add input grouping
			clientGenerationCode += " grouping = \"%d\"" % groupingNumber + ","
			
			#add input description
			clientGenerationCode += " description = \"" + eachInput["description"] + "\")"
			
			#add something needed for a list?
			clientGenerationCode += ","
			
	#add version?
	clientGenerationCode += " version = \"0.1\"" + ","
	
	#add authors
	clientGenerationCode += " authors = [\"" + jsonData["author"] + "\"]" + ","
	
	#add institutions
	clientGenerationCode += " institutions = [\"WebValley 2013\"]" + ","
	
	#add contact
	clientGenerationCode += " contact = \"webvalley@fbk.eu\"" + ","
	
	#finish
	clientGenerationCode += ")"
	
	return clientGenerationCode
	
def additionalMainInitialization():
	mainInitialization = """
	
	try:
		# process the list of args above.
		scriptParams = {}
		for key in client.getInputKeys():
			if client.getInput(key):
				scriptParams[key] = client.getInput(key, unwrap=True)
		
		# establish connection to omero
		conn = BlitzGateway(client_obj=client)
        
        		#get objects
		objects, logMessage = script_utils.getObjects(conn, scriptParams)
        
		# gather all images
		images = []

		if (scriptParams["Data_Type"] == "Dataset"):
			for dataSet in objects:
				images.extend(list(dataSet.listChildren()))
			if not images:
				print "No images found in selected dataset."
		else:
			images = objects 
			
		datasetObj = omero.model.DatasetI()
		datasetObj.setName(rstring(scriptParams["Storing_Dataset"]))
		datasetObj = conn.getUpdateService().saveAndReturnObject(datasetObj)
			
		savePlanes(images, conn, datasetObj, scriptParams)
		           
	finally:
		client.closeSession()
	"""	
	return mainInitialization
			
def retrieveSelectionIndex(selectionIndexPath):
	jsonData = requests.get(selectionIndexPath).json()

	for process in jsonData:
		print process
			
if __name__ == "__main__":
	availableProcesses = retrieveSelectionIndex("http://192.168.205.13/process/list")
	
	client = scripts.client('WebValley Processing', """This code enables for the creation of processing scripts.""",
				scripts.String("
	
	finalCode = generateImports()
	finalCode += generateClient("http://192.168.205.13/process/detail/1")
	finalCode += additionalMainInitialization()
	print finalCode
