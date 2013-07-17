from omero.gateway import BlitzGateway
import os

class ScriptsManager(object):
    def __init__(self, user="root", pwd="omero", host="localhost"):
        self.conn = BlitzGateway(user, pwd, host=host)
        result = self.conn.connect()
        if not result:
            raise RuntimeError("Cannot connect to <{0}>".format(host)+
                               " with user <{0}>.".format(user))
        self.svc = self.conn.getScriptService()

    def list(self):
         return self.svc.getScripts()

    def delete(self, id):
        try:
            self.svc.deleteScript(id)
        except Exception, e:
            raise RuntimeError("Failed to delete script: "+
                               "{0} ({1})".format(id, e))            

    def upload(self, folder_name, script_name, script):
        import omero
        path = os.path.join(folder_name,
                            script_name+".py")
        try:
            id = self.svc.uploadOfficialScript(path,
                                               script)
        except omero.SecurityViolation, sv:
            raise RuntimeError("SecurityViolation: {0}".format(
                    sv.message))
        except Exception, aue:
            if "editScript" in aue.message:
                self.delete(self.get_id_from_path(folder_name,
                                                  script_name))
                id = self.svc.uploadOfficialScript(path,
                                                   script)
            else:
                raise RuntimeError("ApiUsageException: {0}".format(
                        aue.message))

    def get_id_from_path(self, folder_path, file_path):
        for script in self.list():
            path = script.getPath().getValue()
            name = script.getName().getValue()
            if path == "/"+folder_path+"/" and \
               name == file_path+".py":
                return script.getId().getValue()
        return "-1"
                
if __name__=="__main__":
    sm = ScriptsManager()
    #print sm.get_id_from_path("my_scripts","2_json_new_list")
    #sm.delete(975)
    sm.upload("pollo_test", "empty2",
"""#!/usr/bin/env python

import omero.scripts as scripts

if __name__ == "__main__":
    client = scripts.client('Empty script')
""")
