#!/usr/bin/env python

from omero.gateway import BlitzGateway            # used for connecting to the server
import omero                        # contains general OMERO content
import omero.util.script_utils as scriptUtil        # used for making the user interface
from omero.rtypes import *                # imports rstring + other data types
import omero.scripts as scripts                # allows for making user interface
from cStringIO import StringIO
from numpy import *                    # for array representations

try:
    from PIL import Image
except ImportError:
    import Image
import omero.clients
from omero import client_wrapper
import requests

if __name__ == "__main__":
    dataTypes = [rstring('Dataset'), rstring('Image')]

    client = scripts.client('Upload Image',
                            """Using this script, you can upload one or more images to a remote sever.""",
                            scripts.String("Data_Type", optional=False, grouping="1",
                                           description="Choose source of images (only Image supported)",
                                           values=dataTypes, default="Image"),
                            scripts.List("IDs", optional=False, grouping="2",
                                         description="List of Image IDs to change annotations for.").ofType(rlong(0)),
                            scripts.String("Control_Tag", optional=False, grouping="3",
                                           description="Tag used for the control drug."),
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

        # go through each image
        for image in images:
            for annotation in image.listAnnotations():
                if isinstance(annotation, omero.gateway.TagAnnotationWrapper):
                    if annotation.getValue() == scriptParams["Control_Tag"]:
                        omeTiffImage = image.exportOmeTiff()
                        payload = {'file': omeTiffImage}
                        r = requests.put("http://192.168.205.10/owncloud/remote.php/webdav/", files=payload)

                    #f = open('/home/gabriele/prova16.tiff').read()
                    #r = requests.delete(url='http://192.168.205.10/owncloud/files/webdav.php/filename', auth=('webvalley','webvalley'))
                    #r = requests.put(url='http://192.168.205.10/owncloud/files/webdav.php/newfolder/filename', data=f, auth=('webvalley','webvalley'))
                    #r = requests.request('DELETE',url='http://192.168.205.10/owncloud/files/webdav.php/newfolder', auth=('webvalley','webvalley'))

    finally:
        client.closeSession()
