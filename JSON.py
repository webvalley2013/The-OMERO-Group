#!/usr/bin/env python

from omero.gateway import BlitzGateway        # used for connecting to the server
import omero                                # contains general OMERO content
import omero.util.script_utils as scriptUtil# used for making the user interface
from omero.rtypes import *                    # imports rstring + other data types
import omero.scripts as scripts                # allows for making user interface

try:
    from PIL import Image
except ImportError:
    import Image
import omero.clients
from omero import client_wrapper
import requests

#urls
url_process_details = "http://192.168.205.13/process/detail/"
url_process_list = "http://192.168.205.13/process/list/"
url_process_run = "http://192.168.205.13/process/run/test_int/"

def simple_input(type, identifier, group_num, description):
    """Builds a generic input () string."""
    s = """\
    scripts.{0}("{1}", #input identifier
                optional=False,
                grouping="{2}",
                description="{3}"),
""".format(type, identifier, group_num, description)
    return s

def build_inputs(inputs_json):
    s = ""
    for input in inputs_json:
        if input["type"] == "url_list":
            s += simple_input("String",
                              input["label"],
                              input["index"],
                              input["description"])
        elif input["type"] == "string":
            s += simple_input("String",
                              input["label"],
                              input["index"],
                              input["description"])
        elif input["type"] == "int":
            s += simple_input("Int",
                              input["label"],
                              input["index"],
                              input["description"])
        else:
            raise RuntimeError("Input type <{0}> not recognized".format(input["type"]))
    return s

def build_image_upload(json):
    s = ""
    for input in json:
        if input["type"]=="url_list":
            s += """\
                    if annotation.getValue() == scriptParams["{0}"]:
                        omeTiffImage = image.exportOmeTiff()
                        loader.upload(url, omeTiffImage)
                        urls["{1}"] = urls.get("{1}","")+"||"+loaderout+url

""".format(input["label"],
           input["name"])
    return s

def build_data(json):
    s = ""
    for input in json:
        if input["type"]=="url_list":
            s += """\
                data["{0}"] = urls["{0}"]
""".format(input["name"])
        else:
            s += """\
                data["{0}"] = stringParams["{0}"]
""".format(input["name"])
    return s

if __name__ == "__main__":
    client = scripts.client("WebValley Processing",
                            "This code enables for the creation of processing scripts.",
                            version="0.1",
                            authors=["The OMERO Group", ""],
                            institutions=["WebValley"],
                            contact="webvalley@fbk.eu", )

    availableProcesses = requests.get(url_process_list).json()

    for process in availableProcesses:
        jsonData = requests.get(url_process_details+process["index"]).json()

        finalCode = """\
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

    client = scripts.client({script_name},
                            \"\"\"{description}\"\"\",
                            scripts.String("Data_Type", optional=False, grouping="1",
                                           description="Choose source of images (only Image supported)",
                                           values=dataTypes, default="Image"),
                            scripts.List("IDs", optional=False, grouping="2",
                                         description="List of Image IDs to change annotations for.").ofType(rlong(0)),
{inputs}
                            version="0.1",
                            authors=["{author}", ""],
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
{image_upload}

        data = {}

{build_data}

        print data

        polling_url = requests.post("{url_process_run}",data=str(data)).content

        running = True
        #TODO loop until you make it ;-)

    finally:
        client.closeSession()
""".format(script_name=jsonData["code"],
           description=jsonData["description"],
           inputs=build_inputs(jsonData["inputs"]),
           author=jsonData["author"],
           image_upload=build_image_upload(jsonData["inputs"]),
           build_data=build_data(jsonData["inputs"]),
           url_process_run=url_process_run+str(process["id"])) #TODO check this

        with open("/tmp/"+process["index"], "w") as f:
            f.write(finalCode)
