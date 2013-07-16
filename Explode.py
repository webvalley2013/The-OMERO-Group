#!/usr/bin/env python

import omero.scripts as scripts
from omero.gateway import BlitzGateway
import omero.util.script_utils as script_utils
import omero
from omero.rtypes import *
import os
import numpy as np

def planeGen(z, c, t, pixels):
	currentPlane = pixels.getPlane(z, c, t)
	yield currentPlane
					        
def savePlanes(images, conn, dataset, scriptParams):
	for image in images:
		pixels = image.getPrimaryPixels()
		for t in range(image.getSizeT()):
			for z in range(image.getSizeZ()):
				for c in range(image.getSizeC()):
					i = conn.createImageFromNumpySeq(planeGen(z, c, t, pixels), makeImageName(image, z, c, t, scriptParams), 1, 1, 1, description=getImageDescription(image, z, c, t), dataset=dataset)

def makeImageName(image, z, c, t, scriptParams):
	if "Base_Image_Path" in scriptParams:
		name = scriptParams["Base_Image_Path"]
	else:
		originalName = image.getName()
		name = os.path.basename(originalName)
		
	if scriptParams["Image_Order"] == "T-Z-C":
		imgName = "%s_t%02d_z%s_c%s.tiff" % (name, t, z, c)
	elif scriptParams["Image_Order"] == "T-C-Z":
		imgName = "%s_t%02d_c%s_z%s.tiff" % (name, t, c, z)
	elif scriptParams["Image_Order"] == "Z-T-C":
		imgName = "%s_z%s_t%02d_c%s.tiff" % (name, z, t, c)
	elif scriptParams["Image_Order"] == "Z-C-T":
		imgName = "%s_z%s_c%s_t%02d.tiff" % (name, z, c, t)	
	elif scriptParams["Image_Order"] == "C-Z-T":
		imgName = "%s_c%s_z%s_t%02d.tiff" % (name, c, z, t)	
	elif scriptParams["Image_Order"] == "C-T-Z":
		imgName = "%s_c%s_t%02d_z%s.tiff" % (name, c, t, z)	

	i = 1
	name = imgName[:-(len("tiff")+1)]
	while os.path.exists(imgName):
		imgName = "%s_(%d).%s" % (name, i, "tiff")
		i += 1		
	return imgName
	
def getImageDescription(image, z, c, t):
	originalName = image.getName()
	zString = "Z-Section: %s" % z
	cString = "Channel: %s" % c
	tString = "Timestamp: %s" % t
	
	return originalName + "\n" + tString + "\n" + zString + "\n" + cString

def runScript():
	"""
	The main entry point of the script, as called by the client via the scripting service, passing the required parameters. 
	"""
       
	orders = [rstring('T-Z-C'),rstring('T-C-Z'),rstring('Z-T-C'),rstring('Z-C-T'),rstring('C-Z-T'),rstring('C-T-Z')]
	dataTypes = [rstring('Dataset'),rstring('Image')]
     
	client = scripts.client('Explode.py', """Explode 3D images into multiple images, split based on channels, number of planes, and timestamps.""",

	scripts.String("Data_Type", optional=False, grouping="1", description="The data you want to work with.", values=dataTypes, default="Image"),

	scripts.List("IDs", optional=False, grouping="1.1", description="List of Dataset IDs or Image IDs").ofType(rlong(0)),
        
	scripts.String("Storing_Dataset", optional=False, grouping="2", description="Name of data set to store images", default='Explode'),
        
    scripts.String("Base_Image_Path", grouping="2.1", description="Base name of image."),
	scripts.String("Image_Order", grouping="2.2", description="The order in which explosion information is displayed in the image name.", 
		values=orders, default="T-Z-C"),

	version = "1.0",
	authors = ["The OMERO Group", ""],
	institutions = ["WebValley 2013"],
	contact = "webvalley@fbk.eu",) 
    
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

if __name__ == "__main__":
	runScript()