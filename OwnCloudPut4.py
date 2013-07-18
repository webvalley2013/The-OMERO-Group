#!/usr/bin/env python

from omero.gateway import BlitzGateway            # used for connecting to the server
import omero                        # contains general OMERO content
import omero.util.script_utils as scriptUtil        # used for making the user interface
from omero.rtypes import *                # imports rstring + other data types
import omero.scripts as scripts                # allows for making user interface
from numpy import *                    # for array representations
import os
import random
import string

try:
    from PIL import Image
except ImportError:
    import Image
import omero.clients
from omero import client_wrapper
from wvutils.davloader import DAVLoader

loaderout = "http://192.168.205.10/owncloud/public.php?service=files&download&t=480d93ee44956ac9e26efc1d3321449e&path=/"
loaderin  = "http://192.168.205.10/owncloud/files/webdav.php/inputs/"

if __name__ == "__main__":

    dataTypes = [rstring('Dataset'), rstring('Image')]

    client = scripts.client('Upload Image',
                            """Using this script, you can upload one or more images to a remote sever.""",
                            scripts.String("Data_Type", optional=False, grouping="1",
                                           description="Choose source of images (only Image supported)",
                                           values=dataTypes, default="Image"),
                            scripts.List("IDs", optional=False, grouping="2",
                                         description="List of Image IDs to change annotations for.").ofType(rlong(0)),
                            scripts.String("Control_Tag1", optional=False, grouping="3",
                                           description="Tag used for the control food."),
                            scripts.String("Control_Tag2", optional=False, grouping="3",
                                           description="Tag used for the control tissue."),
                            scripts.String("Control_Tag3", optional=False, grouping="3",
                                           description="Tag used for the control drug."),
                            scripts.Int("IntInput", optional=False, grouping="3",
                                           description="A beautiful int"),
                            version="0.1",
                            authors=["The OMERO Group", ""],
                            institutions=["WebValley"],
                            contact="webvalley@fbk.eu", )

    try:
        # process the list of args above.
        scriptParams = {}
        for key in client.getInputKeys():
            if client.getInput(key):
                scriptParams[key] = client.getInput(key, unwrap=True)

        # establish connection to omero
        conn = BlitzGateway(client_obj=client)

        #get objects
        objects, logMessage = scriptUtil.getObjects(conn, scriptParams)

        # gather all images
        images = []

        if scriptParams["Data_Type"] == "Dataset":
            for dataSet in objects:
                images.extend(list(dataSet.listChildren()))
            if not images:
                print "No images found in selected dataset."
        else:
            images = objects

        loader = DAVLoader(loaderin, 'process', 'process')
        relativepath = "".join(random.choice(string.ascii_uppercase + string.digits) for x in range(10))
        loader.mkdir(relativepath)

        # go through each image
        urls = {}
        for image in images:
            for annotation in image.listAnnotations():
                if isinstance(annotation, omero.gateway.TagAnnotationWrapper):
                    url = relativepath+"/"+os.path.basename(image.getName())
                    if annotation.getValue() == scriptParams["Control_Tag1"]:
                        omeTiffImage = image.exportOmeTiff()
                        loader.upload(url, omeTiffImage)
                        urls["Control_Tag1"] = urls.get("Control_Tag1","")+"||"+loaderout+url
                    elif annotation.getValue() == scriptParams["Control_Tag2"]:
                        omeTiffImage = image.exportOmeTiff()
                        loader.upload(url, omeTiffImage)
                        urls["Control_Tag2"] = urls.get("Control_Tag2","")+"||"+loaderout+url
                    elif annotation.getValue() == scriptParams["Control_Tag3"]:
                        omeTiffImage = image.exportOmeTiff()
                        loader.upload(url, omeTiffImage)
                        urls["Control_Tag3"] = urls.get("Control_Tag3","")+"||"+loaderout+url

        data = {}

        data["IntInput"] = scriptParams["IntInput"]
        data["Control_Tag1"] = urls["Control_Tag1"]
        data["Control_Tag2"] = urls["Control_Tag2"]
        data["Control_Tag3"] = urls["Control_Tag3"]

        print data

    finally:
        client.closeSession()
