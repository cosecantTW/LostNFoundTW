import json
import urllib.request
from html.parser import HTMLParser
alldatas = []
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super(MyHTMLParser,self).__init__()
        self.istd = False
        self.datas = []
    def handle_starttag(self, tag, attrs):
        if tag == 'td': 
            self.istd = True
    def handle_endtag(self, tag):
        if tag == 'tr':            
            if len(self.datas) == 4 and self.datas[0] != '':
                alldatas.append(dict({'lostdate':self.datas[0],'objname':self.datas[1],'lostplace':'北捷-'+self.datas[2],'serial':'TRTC-'+self.datas[3]}))            
            self.datas = []
    def handle_data(self, data):
        if self.istd:
            self.datas.append(data)
            self.istd = False        
itemlist = ['手套', '手提袋', '手錶', '文件袋', '水壺', '皮夾', '印章', '名片夾', '存摺', '安全帽', '行動電話', '衣物', '車票', '車票夾', '金融卡', '信用卡', '背包', '首飾', '書', '書包', '紙袋', '記事本', '現金', '眼鏡', '票據', '傘', '圍巾', '帽子', '絲巾', '塑膠袋', '照片', '照相機', '腰帶', '鉛筆盒', '電話卡', '電話本', '零錢包', '領帶', '鞋子', '證件', '鑰匙','其他']       
for itemname in itemlist:
    req = urllib.request.Request("http://web.trtc.com.tw/c/lf2009.asp?item="+urllib.request.quote(itemname.encode('utf-8')))  
    req.add_header('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.3 Safari/537.36')
    response = urllib.request.urlopen(req)
    docStr = response.read().decode('utf8') 
    parser = MyHTMLParser()
    parser.feed(docStr)
    parser.close()  
print(json.dumps(alldatas))
