import sys
import json
import urllib.request
import logging
import os
import http.cookiejar
import re
import time
from datetime import date,timedelta
from html.parser import HTMLParser
from firebase import firebase
from elasticsearch import Elasticsearch
logging.basicConfig(filename="logs/lf_npa_"+str(int(time.time()))+".log", level=logging.INFO)
logger = logging.getLogger( 'NPA' )
es = Elasticsearch([{"host": "localhost", "port": 9277}])
fb = firebase.FirebaseApplication('https://incandescent-heat-2597.firebaseio.com', None)
firebase_secret = os.environ['FIREBASE_SECRET']
firebase_username = 'admin'
fb.authentication = firebase.FirebaseAuthentication(firebase_secret, firebase_username, admin=True)
alldatas = []
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super(MyHTMLParser,self).__init__()
        self.istd = False
        self.istable = False
        self.ispageinfo = False
        self.datas = []
        self.tddata = ''
        self.pagecount = 0
    def handle_starttag(self, tag, attrs):
        if tag == 'td' and self.istable: 
            self.istd = True
            self.tddata = ''
        if tag == 'table': 
            for name, value in attrs:
                if name == 'id' and value == 'OP01A01Q_01Data':
                    self.istable = True
        if tag == 'span':
            for name, value in attrs:
                if name == 'class' and value == 'pagebanner':
                    self.ispageinfo = True            
    def handle_endtag(self, tag):
        if tag == 'table':
            self.istable = False  
        if tag == 'td' and self.istd:
            self.datas.append(self.tddata)
            self.istd = False  
        if tag == 'tr':             
            if len(self.datas) == 6:
                #print(str(len(self.datas))+' '+self.datas[1])  
                m = re.search('獲：(.+)，請', self.datas[5])
                if m:
                    self.datas[5] = m.group(1);
                m = re.search('(\d+)(.+)', self.datas[3])
                if m:
                    self.datas[3] = str(int(m.group(1))+1911) + m.group(2) + ':00'
                alldatas.append(dict({'keeper':self.datas[2],'lostdate':self.datas[3],'objname':self.datas[5],'lostplace':self.datas[4],'serial':'NPA-'+self.datas[1],'fromsite':'NPA'}))            
            self.datas = []
    def handle_data(self, data):
        if self.istd:            
            self.tddata = data               
        if self.ispageinfo:
            m = re.search('共(\d+)頁', data)
            if m:
                self.pagecount = int(m.group(1))
            self.ispageinfo = False        
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.3 Safari/537.36')]
today = date.today()
for diff in range(1,91):
    alldatas = []
    d = today - timedelta(days=diff)
    dstr = str(d.year - 1911) + d.strftime("%m%d")
    postdata = 'method=doQuery&action=&currentPage=&unit1Cd=&unit2Cd=&unit3Cd=&puDateBeg='+ dstr +'&puDateEnd='+ dstr +'&objNm=&objPuPlace='
    req = urllib.request.Request("http://eli.npa.gov.tw/NPA97-217Client/oP01A01Q_01Action.do",postdata.encode('MS950'))  
#req.add_header('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.3 Safari/537.36')
#response = urllib.request.urlopen(req)
    response = opener.open(req)
#print(cj._cookies) 
    try:
        docStr = response.read().decode('MS950')
    except:
        logger.info('d ' + dstr + ' p 1 err\n')
        docStr = response.read().decode('MS950','ignore')
#print(docStr)
    parser = MyHTMLParser()
    parser.feed(docStr)
    pagecount = parser.pagecount
    parser.close()  
    print(dstr + ': ' + str(pagecount))
    for page in range(2,pagecount+1):
        pageurl = "http://eli.npa.gov.tw/NPA97-217Client/oP01A01Q_01Action.do?d-3657963-p="+ str(page) +"&method=doQuery"
        req = urllib.request.Request(pageurl)  
        response = opener.open(req)
    #response = urllib.request.urlopen(req)
        try:
            docStr = response.read().decode('MS950') 
        except:
            logger.info('d ' + dstr + ' p '+str(page)+' err\n')
            docStr = response.read().decode('MS950','ignore')
        parser = MyHTMLParser()
        parser.feed(docStr)
        parser.close()  
    c = 0;
    for data in alldatas:
        try:
            es.index(index="lfdata", doc_type="data", id=data['serial'], body=data)
            result = fb.put('/lfdata/NPA/', data['serial'], data)
            c+=1
            logger.info(str(c) + ' ' + data['serial'] + ' OK\n')
        except:
            logger.info(str(c) + ' ' + data['serial'] + ' ERROR\n')

#print(len(alldatas))
#print(json.dumps(alldatas, ensure_ascii=False))
