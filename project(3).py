import urllib
import re
import threading
import time
import urllib.request
import urllib.error
import csv

class search:
    # 初始化方法，定义一些变量
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 ((Windows NT 10.0; Win64; x64))'
        # 初始化headers
        self.headers = {'User-Agent': self.user_agent}
        # 存放程序是否继续运行的变量
        self.enable = False

    # 传入某一页的索引获得页面代码
    def connectfirststep(self, cname):
        try:
            url = 'http://www.fedspending.org/fpds/fpds.php?company_name=' + cname + '&x=13&y=12&reptype=r&database=fpds&fiscal_year=2015&detail=0&mustrn=y&datype=T&sortby=r'
            # 构建请求的request
            request = urllib.request.Request(url, headers=self.headers)
            # 利用urlopen获取页面代码
            response = urllib.request.urlopen(request)
            # 将页面转化为UTF-8编码
            pageCode = response.read().decode('utf-8')
            return pageCode

        except urllib.error.URLError as e:
            if hasattr(e, "reason"):
                print("连接失败,错误原因", e.reason)
                return None

    def connectsecondstep(self,cname,dictionary):
        url=self.getallcompany(cname,dictionary)
        if self.enable == False:
            return None
        try:
            request = urllib.request.Request(url, headers=self.headers)
            # 利用urlopen获取页面代码
            response = urllib.request.urlopen(request)
            # 将页面转化为UTF-8编码
            pageCode = response.read().decode('utf-8')
            return pageCode

        except urllib.error.URLError as e:
            if hasattr(e, "reason"):
                print("连接失败,错误原因", e.reason)
                return None

    # 传入某一页代码，返回本页不带图片的段子列表
    def getallcompany(self, cname,dictionary):
        pageCode = self.connectfirststep(cname)
        print (pageCode)
        if not pageCode:
            print("页面加载失败....")
            return None
        pattern = re.compile('Total parent companies for fiscal year 2015: <strong>(.*?)</strong>',
                             re.S)
        items = re.findall(pattern, pageCode)
        #没找到结束
        if len(items)==0:
            self.enable = False
            print("no company")
            dictionary['Best Parent Name'] = 'NA'
            return None
        self.enable = True
        print(items[0])
        itemstr=items[0]
        itemstr = itemstr.replace(",", "")
        company_num=int(itemstr)
        pstring='You can click on the column headers below to re-sort the.*?for this search'
        i=company_num
        if i>20:
            dictionary['Best Parent Name'] = 'Too many'
            self.enable = False
            print("too many")
            return None
        self.enable = True
        while i>0:
            i=i-1
            pstring=pstring+'.*?href="(.*?)">(.*?)</a>.*?right>\$(.*?)</font>'
        pattern = re.compile(pstring, re.S)
        items = re.findall(pattern, pageCode)
        #print(items)
        #print(pageCode)
        nlist=[]
        i = company_num
        #链接，名字，金额
        while i > 0:
            j=company_num-i
            i=i-1
            b=items[0][j*3 + 2]
            b=b.replace(",","")
            b=b.replace("*", "0")
            b=b.replace(" ", "")
            a=int(b)
            nlist.append(a)
        #print(nlist)
        max_value = max(nlist)
        max_index = nlist.index(max_value)
        dictionary['Best Parent Name']=items[0][max_index*3+1]
        num=nlist[max_index]
        if num==0:
            self.enable = False
            return None
        self.enable = True
        compstring=items[0][max_index*3]
        secondurl='http://www.fedspending.org/fpds/'+ compstring
        #print(secondurl)
        return secondurl

    def getthetable(self, cname,dictionary):
        pageCode = self.connectsecondstep(cname,dictionary)
        if self.enable == False:
            return None
        if not pageCode:
            print("页面加载失败....")
            return None
        #print(pageCode)
        pstring = '<h3>Trend</h3>'
        i = 0
        while i < 16:
            i = i + 1
            pstring = pstring + '.*?right>\$(.*?)</td>'
        pattern = re.compile(pstring, re.S)
        items = re.findall(pattern, pageCode)
        #nlist = []
        i = 0
        if len(items)==0:
            self.enable = False
            print("no trend")
            return None
        while i < 16:
            b = items[0][i]
            i = i + 1
            b = b.replace(",", "")
            b = b.replace("*", "0")
            b = b.replace(" ", "")
            a = int(b)
            j=1999+i
            dictionary[j]=a
            #nlist.append(a)
        #print(nlist)


    def start(self):
        print("processing...")
        # 使变量为True，程序可以正常运行
        self.enable = True
        j=0
        numperout=500
        while j<9:
            dictionarys=[]
            with open('companyname.csv', 'r') as csvfile:
                reader = csv.reader(csvfile)
                i = 0
                for row in reader:
                    i = i + 1;
                    if j*numperout+i==1:
                        continue
                    if i<j*numperout+1:
                        continue
                    dictionary={'Name':'','Best Parent Name':'',2000:0,2001:0,2002:0,
                            2003: 0,2004:0,2005:0,2006:0,2007:0,2008:0,
                            2009: 0,2010:0,2011:0,2012:0,2013:0,2014:0,
                            2015:0,}
                    name = row[0]
                    dictionary['Name']=name
                    name = name.replace("  -CL", "")
                    lastblank = name.rfind(" ")
                    name = name[0:lastblank]
                    name = name.replace(" ", "+")
                    name = name.lower()
                    print("the",i-1, "company")
                    self.getthetable(name,dictionary)
                    dictionarys.append(dictionary)
                    if i >= (j+1)*numperout:
                        csvfile.close()
                        break
            jstr=str(j)
            with open('result'+jstr+'.csv', 'w+') as csv_file:
                if len(dictionarys)>=1:
                    headers = [k for k in dictionarys[0]]
                    writer = csv.DictWriter(csv_file, fieldnames=headers)
                    writer.writeheader()
                    for dictionary in dictionarys:
                        writer.writerow(dictionary)
            csvfile.close()
            j=j+1

spider = search()
spider.start()