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

def generateImports():
    #start imports
    importCode = """
    from omero.gateway import BlitzGateway        # used for connecting to the server
    import omero                                # contains general OMERO content
    import omero.util.script_utils as scriptUtil# used for making the user interface
    from omero.rtypes import *                    # imports rstring + other data types
    import omero.scripts as scripts                # allows for making user interface
    from cStringIO import StringIO
    from numpy import *                            # for array representations
    try:
        from PIL import Image
    except ImportError:
        import Image
    import omero.clients
    from omero import client_wrapper

    """
    return importCode

def image_list_input(identifier, group_num):
    s = """\
    scripts.String("s{0}", #input identifier
                   optional=False,
                   grouping="{1}",
                   description="Choose source of images",
                   values=dataTypes,
                   default="Image"),
    scripts.List("l{0}",
                 optional=False,
                 grouping="{1}.1",
                 description="List of Image IDs or Dataset IDs").ofType(rlong(0)),
""".format(identifier, group_num)
    return s

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
            s += image_list_input(input["label"],
                                  input["index"])
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
{imports}

if __name__ == "__main__":
    dataTypes = [rstring('Dataset'), rstring('Image')]

    client = scripts.client('{script_name}',
                            \"\"\"{script_description}\"\"\",
                            {inputs}
                            version="0.1",
                            authors=["{author}",],
                            institutions=["WebValley"],
                            contact="webvalley@fbk.eu",)

""".format(imports=generateImports(),
           script_name=jsonData["code"],
           script_description=jsonData["description"],
           inputs=build_inputs(jsonData["inputs"]),
           author=jsonData["author"])

        with open("/tmp/"+process["index"], "w") as f:
            f.write(finalCode)
