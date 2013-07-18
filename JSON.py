#!/usr/bin/env python

#from omero.gateway import BlitzGateway        # used for connecting to the server
#import omero                                # contains general OMERO content
#import omero.util.script_utils as scriptUtil# used for making the user interface
#from omero.rtypes import *                    # imports rstring + other data types
import omero.scripts as scripts                # allows for making user interface
from wvutils.scripts_manager import ScriptsManager

try:
    from PIL import Image
except ImportError:
    import Image
#import omero.clients
#from omero import client_wrapper
import requests

#urls
url_process_details = "http://192.168.205.13/process/detail/"
url_process_list = "http://192.168.205.13/process/list/"
url_process_run = "http://192.168.205.13/process/run/"
server_path = "http://192.168.205.13"

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
    group_num = 2
    for input in inputs_json:
        if input["type"] == "url_list":
            s += simple_input("String",
                              input["label"],
                              group_num,
                              input["description"])
        elif input["type"] == "string":
            s += simple_input("String",
                              input["label"],
                              group_num,
                              input["description"])
        elif input["type"] == "int":
            s += simple_input("Int",
                              input["label"],
                              group_num,
                              input["description"])
        else:
            raise RuntimeError("Input type <{0}> not recognized".format(input["type"]))
        group_num += 1
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
        data["{0}"] = urls.get("{0}", "")
""".format(input["name"])
        else:
            s += """\
        data["{0}"] = scriptParams["{1}"]
""".format(input["name"], input["label"])
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
        jsonData = requests.get(url_process_details+str(process["id"])).json()

        url_list_needed = False
        for input in jsonData["inputs"]:
            if input["type"]=="url_list":
                url_list_needed = True

        if url_list_needed:
            image_input_declaration = """\
                            scripts.String("Data_Type", optional=False, grouping="1",
                                           description="Choose source of images (only Image supported)",
                                           values=dataTypes, default="Image"),
                            scripts.List("IDs", optional=False, grouping="1.1",
                                         description="List of Image IDs to change annotations for.").ofType(rlong(0)),
"""
            image_looping = """\
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
        urls = dict()
        for image in images:
            for annotation in image.listAnnotations():
                if isinstance(annotation, omero.gateway.TagAnnotationWrapper):
                    url = relativepath+"/"+os.path.basename(image.getName())
"""
        else:
            image_input_declaration = ""
            image_looping = ""

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
import requests

try:
    from PIL import Image
except ImportError:
    import Image
import omero.clients
from omero import client_wrapper
from wvutils.davloader import DAVLoader
from time import sleep

loaderout = "http://192.168.205.10/owncloud/public.php?service=files&download&t=480d93ee44956ac9e26efc1d3321449e&path=/"
loaderin  = "http://192.168.205.10/owncloud/files/webdav.php/inputs/"

if __name__ == "__main__":

    dataTypes = [rstring('Dataset'), rstring('Image')]

    client = scripts.client("{script_name}",
                            \"\"\"{description}\"\"\",
{image_input_declaration}
{inputs}
                            version="0.1",
                            authors=["{author}", ""],
                            institutions=["WebValley"],
                            contact="webvalley@fbk.eu", )

    try:
        # process the list of args above.
        scriptParams = dict()
        for key in client.getInputKeys():
            if client.getInput(key):
                scriptParams[key] = client.getInput(key, unwrap=True)

{image_looping}

{image_upload}

        data = dict()

{build_data}

        response = requests.post("{url_process_run}",data=data).json()

        if response["success"] == "true":
            polling_url =response["polling_url"]
            running = True
            while running:
                status = requests.get("{server_path}"+polling_url).json()
                running = not status["finished"]
                sleep(5)
            if status["status"] == "SUCCESS":
                client.setOutput("Message", rstring(str(status["result"])))
            else:
                client.setOutput("Message", rstring("Process failed"))
        else:
            client.setOutput("Message", rstring("Process failed, invalid input parameters"))


    finally:
        client.closeSession()
""".format(image_input_declaration=image_input_declaration,
           image_looping=image_looping,
           script_name=jsonData["code"],
           description=jsonData["description"],
           inputs=build_inputs(jsonData["inputs"]),
           author=jsonData["author"],
           image_upload=build_image_upload(jsonData["inputs"]),
           build_data=build_data(jsonData["inputs"]),
           url_process_run=url_process_run+process["code"]+"/"+str(process["id"]),
           server_path=server_path) #TODO check this

        sm = ScriptsManager()
        sm.upload("/analysis/",process["code"],finalCode)