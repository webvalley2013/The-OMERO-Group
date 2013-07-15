#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 components/tools/OmeroPy/scripts/omero/export_scripts/Batch_Image_Export.py 

-----------------------------------------------------------------------------
  Copyright (C) 2006-2011 University of Dundee. All rights reserved.


  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  
  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

------------------------------------------------------------------------------

This script takes a number of images and saves individual image planes in a zip
file for download. 

@author Will Moore
<a href="mailto:will@lifesci.dundee.ac.uk">will@lifesci.dundee.ac.uk</a>
@version 4.3
<small>
(<b>Internal version:</b> $Revision: $Date: $)
</small>
@since 3.0-Beta4.3
"""

import omero.scripts as scripts
from omero.gateway import BlitzGateway
import omero.util.script_utils as script_utils
import omero
from omero.rtypes import *
import os

import glob
import zipfile
from datetime import datetime
import numpy as np

# keep track of log strings. 
logStrings = []

def log(text):
	"""
	Adds the text to a list of logs. Compiled into text file at the end.
	"""
	print text
	logStrings.append(str(text))

def savePlane(conn, image, format, cName, zRange, projectZ, t=0, channel=None, greyscale=True, imgWidth=None, folder_name=None):
	"""
	Renders and saves an image to disk.
    
	@param renderingEngine:     Rendering Engine should already be initialised with the correct pixels etc
	@param imgName:             The name or path to save to disk, with extension. E.g. imgDir/image01_DAPI_T01_Z01.png
	@param zRange:              Tuple of (zIndex,) OR (zStart, zStop) for projection
	@param t:                   T index
	@param channel:             Active channel index. If None, use current rendering settings
	@param greyscale:           If true, all visible channels will be greyscale 
	@param imgWidth:            Resize image to this width if specified.
	"""
    
	originalName = image.getName()
	log("")
	log("savePlane..")
	#log("originalName %s" % originalName)
	#log("format %s" % format)
	log("channel: %s" % cName)
	log("z: %s" % zRange)
	log("t: %s" % t)
	#log("channel %s" % channel)
	#log("greyscale %s" % greyscale)
	#log("imgWidth %s" % imgWidth)
    
	# if channel == None: use current rendering settings
	if channel != None:
		image.setActiveChannels([channel+1])    # use 1-based Channel indices
		if greyscale:
			image.setGreyscaleRenderingModel()
	
	# All Z and T indices in this script are 1-based, but this method uses 0-based.
	plane = image.renderImage(zRange[0]-1, t-1)

	if format == 'TIFF':
		imgName = makeImageName(originalName, cName, zRange, t, "tiff", folder_name)
		log("Saving image: %s" % imgName)
		
		#new dataset
		"""
		dataset = omero.model.DatasetI()
		dataset.setName(rstring(folder_name))
		dataset = conn.getUpdateService().saveAndReturnObject(dataset)
		"""
		pixels = plane.getPrimaryPixels()		
        i = conn.createImageFromNumpySeq(pixels, "numpy image", 1, 1, 1, description=None, dataset=None)
        
def makeImageName(originalName, cName, zRange, t, extension, folder_name):
	""" 
	Produces the name for the saved image.
	E.g. imported/myImage.dv -> myImage_DAPI_z13_t01.png
	"""
	name = os.path.basename(originalName)
	#name = name.rsplit(".",1)[0]  # remove extension
	if len(zRange) == 2:
		z = "%02d-%02d" % (zRange[0], zRange[1])
	else:
		z = "%02d" % zRange[0]
	imgName = "%s_%s_z%s_t%02d.%s" % (name, cName, z, t, extension)
	if folder_name != None:
		imgName = os.path.join(folder_name, imgName)
	# check we don't overwrite existing file
	i = 1
	name = imgName[:-(len(extension)+1)]
	while os.path.exists(imgName):
		imgName = "%s_(%d).%s" % (name, i, extension)
		i += 1
	return imgName
        
def savePlanesForImage(conn, image, sizeC, splitCs, channelNames=None, zRange=None, tRange=None, greyscale=True, imgWidth=None, projectZ=False, format="PNG", folder_name=None):
	"""
	Saves all the required planes for a single image, either as individual planes or projection.
    
	@param renderingEngine:     Rendering Engine, NOT initialised. 
	@param queryService:        OMERO query service
	@param imageId:             Image ID
	@param zRange:              Tuple: (zStart, zStop). If None, use default Zindex
	@param tRange:              Tuple: (tStart, tStop). If None, use default Tindex
	@param greyscale:           If true, all visible channels will be greyscale 
	@param imgWidth:            Resize image to this width if specified.
	@param projectZ:            If true, project over Z range.
	"""
    
	channels = []
	if splitCs:
		for i in range(sizeC):
			channels.append(i)
        

	# set up rendering engine with the pixels
	"""
    renderingEngine.lookupPixels(pixelsId)
    if not renderingEngine.lookupRenderingDef(pixelsId):
        renderingEngine.resetDefaults()
    if not renderingEngine.lookupRenderingDef(pixelsId):
        raise "Failed to lookup Rendering Def"
    renderingEngine.load()
	"""
    
	if tRange == None:
		tIndexes = [image.getDefaultT()+1]      # use 1-based indices throughout script
	else:
		if len(tRange) > 1:
			tIndexes = range(tRange[0], tRange[1])
		else:
			tIndexes = [tRange[0]]
    
	cName = 'merged'
	for c in channels:
		if c is not None:
			gScale = greyscale
			if c < len(channelNames):
				cName = channelNames[c].replace(" ", "_")
			else:
				cName = "c%02d" % c
		for t in tIndexes:
			if len(zRange) > 1:
				for z in range(zRange[0], zRange[1]):
					savePlane(conn, image, format, cName, (z,), projectZ, t, c, gScale, imgWidth, folder_name)
			else:
				savePlane(conn, image, format, cName, zRange, projectZ, t, c, gScale, imgWidth, folder_name)


def batchImageExport(conn, scriptParams):
    
	# for params with default values, we can get the value directly
	splitCs = True
	greyscale = True
	dataType = scriptParams["Data_Type"]
	ids = scriptParams["IDs"]
	folder_name = scriptParams["Folder_Name"]
	format = "TIFF"
	projectZ = False
        
	# check if we have these params
	channelNames = []
	imgWidth = None
    
	# functions used below for each imaage.
	def getZrange(sizeZ, scriptParams):
		zRange = (1, sizeZ+1)
		return zRange
    
	def getTrange(sizeT, scriptParams):
		tRange = (1, sizeT+1)
		return tRange

	# Get the images or datasets
	message = ""
	objects, logMessage = script_utils.getObjects(conn, scriptParams)
	message += logMessage
	if not objects:
		return None, message
    
	# Attach figure to the first image
	parent = objects[0]
    
	if dataType == 'Dataset':
		images = []
		for ds in objects:
			images.extend( list(ds.listChildren()) )
		if not images:
			message += "No image found in dataset(s)"
			return None, message
	else:
		images = objects
        
	log("Processing %s images" % len(images))
    
	# somewhere to put images
	curr_dir = os.getcwd()
	exp_dir = os.path.join(curr_dir, folder_name)
	try:
		os.mkdir(exp_dir)
	except:
		pass
    
	# do the saving to disk
	for img in images:
		log("\n----------- Saving planes from image: '%s' ------------" % img.getName())
		sizeC = img.getSizeC()
		sizeZ = img.getSizeZ()
		sizeT = img.getSizeT()
		zRange = getZrange(sizeZ, scriptParams)
		tRange = getTrange(sizeT, scriptParams)
		log("Using:")
		if zRange is None:      log("  Z-index: Last-viewed")
		elif len(zRange) == 1:  log("  Z-index: %d" % zRange[0])
		else:                   log("  Z-range: %s-%s" % ( zRange[0],zRange[1]-1) )
		if projectZ:            log("  Z-projection: ON")
		if tRange is None:      log("  T-index: Last-viewed")
		elif len(tRange) == 1:  log("  T-index: %d" % tRange[0])
		else:                   log("  T-range: %s-%s" % ( tRange[0],tRange[1]-1) )
		log("  Format: %s" % format)
		if imgWidth is None:    log("  Image Width: no resize")
		else:                   log("  Image Width: %s" % imgWidth)
		log("  Greyscale: %s" % greyscale)
		log("Channel Rendering Settings:")
		for ch in img.getChannels():
			log("  %s: %d-%d" % (ch.getLabel(), ch.getWindowStart(), ch.getWindowEnd()) )
		savePlanesForImage(conn, img, sizeC, splitCs, channelNames, zRange, tRange, greyscale, imgWidth, projectZ=projectZ, format=format, folder_name=folder_name)

		# write log for exported images (not needed for ome-tiff)
		logFile = open(os.path.join(exp_dir, 'Batch_Image_Export.txt'), 'w')
		try:
			for s in logStrings:
				logFile.write(s)
				logFile.write("\n")
		finally:
			logFile.close()

	if len(os.listdir(exp_dir)) == 0:
		return None, "No files exported. See 'info' for more details" 

def runScript():
	"""
	The main entry point of the script, as called by the client via the scripting service, passing the required parameters. 
	"""
       
	dataTypes = [rstring('Dataset'),rstring('Image')]
     
	client = scripts.client('Explode.py', """Explode 3D images into multiple images, split based on channels and number of planes.""",

	scripts.String("Data_Type", optional=False, grouping="1",
        description="The data you want to work with.", values=dataTypes, default="Image"),

	scripts.List("IDs", optional=False, grouping="2",
        description="List of Dataset IDs or Image IDs").ofType(rlong(0)),
        
	scripts.String("Folder_Name", grouping="3",
        description="Name of data set to store images", default='Batch_Image_Export'),

	version = "1.0",
	authors = ["The OMERO Group", ""],
	institutions = ["WebValley 2013"],
	contact = "webvalley@fbk.eu",) 
    
	try:
		startTime = datetime.now()
		session = client.getSession()
		scriptParams = {}

		conn = BlitzGateway(client_obj=client)

		for key in client.getInputKeys():
			if client.getInput(key):
				scriptParams[key] = client.getInput(key, unwrap=True)
		log(scriptParams)

		# call the main script - returns a file annotation wrapper
		fileAnnotation, message = batchImageExport(conn, scriptParams)
        
		stopTime = datetime.now()
		log("Duration: %s" % str(stopTime-startTime))

		# return this fileAnnotation to the client. 
		client.setOutput("Message", rstring(message))
		if fileAnnotation is not None:
			client.setOutput("File_Annotation", robject(fileAnnotation._obj))
                    
	finally:
		client.closeSession()

if __name__ == "__main__":
	runScript()