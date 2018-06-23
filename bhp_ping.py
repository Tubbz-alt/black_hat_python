from burp import IBurpExtender
from burp import IContextMenuFactory

from javax.swing import JMenuItem
from java.util import List, ArrayList
from java.net import URL

import socket
import urllib
import json
import re
import base64
# this does not work as is you need to play around with the end point/auth key
bing_api_key = "5373d384389e418397bce87ddab24acd"



class BurpExtender(IBurpExtender, IContextMenuFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self.context = None
        
        #setup our extensions
        callbacks.setExtensionName("BHP Bing")
        callbacks.registerContextMenuFactory(self)
        return
    
    def createMenuItems(self, context_menu):
        self.context = context_menu
        menu_list = ArrayList()
        menu_list.add(JMenuItem("Send to Bing", actionPerformed=self.bing_menu))
        return menu_list
        
    def bing_menu(self, event):
        #grab the setails of what the user clicked
        http_traffic = self.context.getSelectedMessages()
        
        print "%d requests highlighted"%len(http_traffic)
        
        for traffic in http_traffic:
            http_service = traffic.getHttpService()
            host = http_service.getHost()
            
            print "User selected host: %s"%host
            
            self.bing_search(host)
        return 
    
    
    def bing_search(self, host):
        
        #check if we have IP or hostname
        is_ip  = re.match("[0-9]+(?:\.[0-9]+){3}", host)
        
        if is_ip:
            ip_address = host
            domain = False
        else:
            ip_address = socket.gethostbyname(host)
            domain = True
            
        bing_query_string = "'ip:%s'"%ip_address
        self.bing_query(bing_query_string)
        
        if domain:
            bing_query_string = "'domain:%s'"%host
            self.bing_query(bing_query_string)
    
    def bing_query(self, bing_query_string):
        
        print "Perofrming Bing Search: %s"%bing_query_string
        
        #encode
        quoted_query = urllib.quote(bing_query_string)
        
        http_request = "GET https://api.cognitive.microsoft.com/bing/v7.0/entities?$format=json&$top=20&Query=%s HTTP/1.1\r\n"%quoted_query
        http_request += "Host: api.cognitive.microsoft.com\r\n"
        http_request += "Connection: close \r\n"
        http_request += "Authorization: Basic %s \r\n"%base64.b64encode(":%s"%bing_api_key)
        http_request += "User-Agent: Blackhat Python \r\n\r\n"
        
        json_body = self._callbacks.makeHttpRequest("api.cognitive.microsoft.com", 443, True, http_request).toString()
        json_body = json_body.split("\r\n\r\n", 1)[1]
        
        try:
            r = json.loads(json_body)
            
            if len(r["d"]["results"]):
                for site in r["d"]["results"]:
                    print "*" * 100
                    print site['Title']
                    print site['Url']
                    print site['Description']
                    print "*" * 100
                    
                    j_url = URL(site['Url'])
                    
            if not self._callbacks.isInScope(j_url):
                print "Adding to Burp scope"
                self._callbacks.includeInScope(j_url)
        except:
            print "No results from Bing"
            pass
        
        return 
        
        
        
        
        
        
        
            
            


