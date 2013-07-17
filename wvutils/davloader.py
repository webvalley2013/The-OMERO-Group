__author__ = 'The webvalley Team (Omero group division)'
from requests import Request, Session
from lxml import etree
from wvutils import xmlutils
import requests


class DAVLoader(object):

    def __init__(self, url, user, password):
        self.__url = url
        self.__user = user
        self.__password = password
        self.__s = Session()

        self.__req = Request('HEAD', url=self.__url).prepare()

        if self.__user is not None:
            self.__req.prepare_auth(auth=(self.__user, self.__password))

        if self.__s.send(self.__req).status_code != 200:
            raise requests.exceptions.HTTPError()

    def __request(self, method, data, path, match_codes):
        r = self.__req
        r.prepare_method(method)
        r.prepare_body(data=data, files=None)
        r.prepare_url(url=self.__url+path, params=None)
        return self.__s.send(r).status_code in match_codes

    def __retrieve(self, method, data, path, match_codes):
        r = self.__req
        r.prepare_method(method)
        r.prepare_body(data=data, files=None)
        r.prepare_url(url=self.__url+path, params=None)
        resp = self.__s.send(r)
        if resp.status_code in match_codes:
            return resp.content
        return False

    def upload(self, path, data):
        return self.__request('PUT', data, path, [201])

    def mkdir(self, path):
        if self.__request('HEAD', None, path, [200]):
            return True
        return self.__request('MKCOL', None, path, [201])

    def delete(self, path):
        return self.__request('DELETE', None, path, [201, 202, 204])

    def download(self, path):
        return self.__retrieve('GET', None, path, [200])

    def list(self, path):
        data = '<?xml version="1.0"?><a:propfind xmlns:a="DAV:"><a:allprop/></a:propfind>'
        xml = self.__retrieve('PROPFIND', data, path, [200, 207])
        parser = etree.XMLParser(remove_blank_text=True)
        tree = xmlutils.clear_xml_comments(xmlutils.clear_xml_namespaces(etree.XML(xml, parser)))
        files = []
        dirs = []
        for response in tree.findall('response'):
            href = response.find('href')
            if href is not None:
                dict = {}
                dict['path'] = href.text
                try:
                    props = response.find('propstat').find('prop')

                    lastmod = props.find('getlastmodified')
                    if lastmod is not None:
                        dict['lastmod'] = lastmod.text

                    contentlength = props.find('getcontentlength')
                    if contentlength is not None:
                        dict['size'] = contentlength.text

                    contenttype = props.find('getcontenttype')
                    if contenttype is not None:
                        dict['type'] = contenttype.text

                    if props.find('resourcetype').find('collection') is not None:
                        dirs.append(dict)
                    else:
                        files.append(dict)

                except AttributeError:
                    pass

        return dirs, files