#!/usr/bin/env python

import omero.scripts as scripts
from wvutils.scripts_manager import ScriptsManager

try:
    from PIL import Image
except ImportError:
    import Image
import requests

#urls
server_url = "http://192.168.205.13"  # url of the analysis server
url_process_list = server_url+"/process/list/"  # url for retriving process list
url_process_details = server_url+"/process/detail/"  # url for process details (inputs and ouputs definitions)
url_process_run = server_url+"/process/run/"  # url for running processes

# webdav url for image uploading
webdav_url = "http://192.168.205.10/owncloud/files/webdav.php/inputs/"

# base url for uploaded images (this will be sent to analysis server)
public_webdav_url = "http://192.168.205.10/owncloud/public.php?service=files&download&t=480d93ee44956ac9e26efc1d3321449e&path=/"


def simple_input(type, identifier, group_num, description, optional):
    """Builds a generic input () string."""
    s = """\
                            scripts.{0}("{1}", #input identifier
                                        optional={4},
                                        grouping="{2}",
                                        description="{3}"),
""".format(type, identifier, group_num, description, optional)
    return s


def build_inputs(inputs_json):
    s = ""
    group_num = 2
    for input in inputs_json:
        if input["type"] == "url_list":
            s += simple_input("String",
                              input["label"],
                              group_num,
                              input["description"],
                              str(not input["required"]))
        elif input["type"] == "string":
            s += simple_input("String",
                              input["label"],
                              group_num,
                              input["description"],
                              str(not input["required"]))
        elif input["type"] == "int":
            s += simple_input("Int",
                              input["label"],
                              group_num,
                              input["description"],
                              str(not input["required"]))
        else:
            raise RuntimeError("Input type <{0}> not recognized".format(input["type"]))
        group_num += 1
    return s


def build_image_upload(json):
    s = ""
    for input in json:
        if input["type"] == "url_list":
            s += """\
                    if annotation.getValue() == scriptParams["{0}"]:
                        omeTiffImage = image.exportOmeTiff()
                        loader.upload(url, omeTiffImage)
                        urls["{1}"] = urls.get("{1}","")+urllib.quote(loaderout+url,":/")+"||"

""".format(input["label"],
           input["name"])
    return s


def build_data(json):
    s = ""
    for input in json:
        if input["type"] == "url_list":
            s += """\
        data["{0}"] = urls.get("{0}", "")[:-2]
""".format(input["name"])
        else:
            s += """\
        data["{0}"] = scriptParams.get("{1}","")
""".format(input["name"], input["label"])
    return s


if __name__ == "__main__":
    client = scripts.client("WebValley Processing",
                            "This code enables for the creation of processing scripts.",
                            scripts.String("Folder Name", grouping="1",
                                           description="Folder Name where analysis scripts will be created"),
                            version="0.1",
                            authors=["WebvalleyTeam 2013"],
                            institutions=["FBK"],
                            contact="webvalley@fbk.eu")

    scriptParams = {}
    for key in client.getInputKeys():
        if client.getInput(key):
            scriptParams[key] = client.getInput(key, unwrap=True)

    availableProcesses = requests.get(url_process_list).json()

    for process in availableProcesses:
        jsonData = requests.get(url_process_details + str(process["id"])).json()

        url_list_needed = False
        for input in jsonData["inputs"]:
            if input["type"] == "url_list":
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
import urllib

try:
    from PIL import Image
except ImportError:
    import Image
import omero.clients
from omero import client_wrapper
from wvutils.davloader import DAVLoader
from time import sleep

loaderout = "{public_webdav_url}"
loaderin  = "{webdav_url}"

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

        if response["success"]:
            polling_url =response["polling_url"]
            running = True
            while running:
                status = requests.get("{server_url}"+polling_url).json()
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
           url_process_run=url_process_run + process["code"] + "/" + str(process["id"]),
           server_url=server_url,
           webdav_url=webdav_url,
           public_webdav_url=public_webdav_url
        )

        sm = ScriptsManager()
        sm.upload("/"+scriptParams["Folder Name"]+"/", process["code"], finalCode)