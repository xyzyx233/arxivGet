import urllib.request
from lxml import etree
import pandas as pd
import datetime
import os
import socks
import socket
import wget

import threading
import time
import urllib3
import urllib3.contrib.pyopenssl
import certifi
import random

socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1080)
socket.socket = socks.socksocket

lock = threading.Lock()
count = 0

def requestFileSize(http, url):
    r = http.request('HEAD', url)
    return r.headers["Content-Length"]


def test_urllib3(http, url):
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36"
    }

    response = http.request('GET', url, None, header)
    data = response.data.decode('utf-8')  # 注意, 返回的是字节数据.需要转码.
    print(data)  # 打印网页的内容


class MulThreadDownload(threading.Thread):
    def __init__(self, http, url, startpos, endpos, fo):
        super(MulThreadDownload, self).__init__()
        self.url = url
        self.startpos = startpos
        self.endpos = endpos
        self.fo = fo
        self.http = http

    def downloadBlock(self, start, end):
        headers = {"Range": "bytes=%d-%d" % (start, end)}
        res = self.http.request('GET', self.url, headers=headers, preload_content=False)

        lock.acquire()
        self.fo.seek(start)
        global count
        count = (count + len(res.data))
        print("download total %d" % count)
        self.fo.write(res.data)
        self.fo.flush()
        lock.release()

    def download(self):
        print("start thread:%s at %s" % (self.getName(), time.process_time()))

        bufSize = 102400
        pos = self.startpos + bufSize
        while pos < self.endpos:
            time.sleep(random.random())  # 延迟 0-1s,避免被服务器识别恶意访问
            self.downloadBlock(self.startpos, pos)
            self.startpos = pos + 1
            pos = self.startpos + bufSize

        self.downloadBlock(self.startpos, self.endpos)
        print("stop thread:%s at %s" % (self.getName(), time.process_time()))

    def run(self):
        self.download()


def createFile(filename, size):
    with open(filename, 'wb') as f:
        f.seek(size - 1)
        f.write(b'\x00')


# @click.command(help="""多线程下载单个静态文件,注意,目前不支持数据流文件.如果下载不了,请减少线程个数. \n
#     MultiThreadDownloadFile.py pathUrl pathOutput""")
# @click.option('--threads_num', default=2, help="线程个数")
# @click.option('--url_proxy', default="", help="HTTP代理")
# @click.argument('path_url', type=click.Path())
# @click.argument('path_output', type=click.Path())
# @click.pass_context
# def runDownload(ctx, threads_num, url_proxy, path_url, path_output):
#     print(" threadNum: %d\n urlProxy: %s\n pathUrl: %s\n PathOutput %s\n"
#           % (threads_num, url_proxy, path_url, path_output))
#
#     http = None
#     if len(url_proxy) == 0:
#         http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
#     else:
#         http = urllib3.ProxyManager(url_proxy, cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
#
#     print(path_url)
#     print(http)
#     fileSize = int(requestFileSize(http, path_url))
#     print(fileSize)
#     step = fileSize // threads_num
#     mtd_list = []
#
#     createFile(path_output, fileSize)
#
#     startTime = time.time()
#     # rb+ ，二进制打开，可任意位置读写
#     with open(path_output, 'rb+') as  f:
#
#         loopCount = 1
#         start = 0
#         while loopCount < threads_num:
#             end = loopCount * step - 1
#             t = MulThreadDownload(http, path_url, start, end, f)
#             t.start()
#             mtd_list.append(t)
#             start = end + 1
#             loopCount = loopCount + 1
#
#         t = MulThreadDownload(http, path_url, start, fileSize - 1, f)
#         t.start()
#         mtd_list.append(t)
#
#         for i in mtd_list:
#             i.join()
#
#     endTime = time.time()
#     print("Download Time: %fs" % (endTime - startTime))
def runDownload( threads_num, path_url, path_output):
    print(" threadNum: %d\n pathUrl: %s\n PathOutput %s\n"
          % (threads_num, path_url, path_output))

    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    fileSize = int(requestFileSize(http, path_url))
    print(fileSize)
    step = fileSize // threads_num
    mtd_list = []

    createFile(path_output, fileSize)

    startTime = time.time()
    # rb+ ，二进制打开，可任意位置读写
    with open(path_output, 'rb+') as  f:

        loopCount = 1
        start = 0
        while loopCount < threads_num:
            end = loopCount * step - 1
            t = MulThreadDownload(http, path_url, start, end, f)
            t.start()
            mtd_list.append(t)
            start = end + 1
            loopCount = loopCount + 1

        t = MulThreadDownload(http, path_url, start, fileSize - 1, f)
        t.start()
        mtd_list.append(t)

        for i in mtd_list:
            i.join()

    endTime = time.time()
    print("Download Time: %fs" % (endTime - startTime))
def norme(str):
    return str.replace(":","-")
# text = open('out.html').read().encode('utf-8')
response = urllib.request.urlopen('https://arxiv.org/list/cs.AI/recent')
text=response.read().decode('gb2312')
s=etree.HTML(text.encode('utf-8'))
download_list=s.xpath('//dl/dt//a[@title="Download PDF"]/@href')
titles=s.xpath('//dl/dd/div/div[@class="list-title mathjax"]/text()')
primary_subject=s.xpath('//dl/dd/div/div[@class="list-subjects"]/span[@class="primary-subject"]/text()')
subject=s.xpath('//dl/dd/div/div[@class="list-subjects"]/text()')
count=len(download_list)
print(count)

title_list=[]
subjects=[]

for i in range(count):
    title_list.append(str.strip(titles[2*i+1]))
for i in range(count):
    subjects.append(primary_subject[i]+subject[3*i+2].strip())
for i in range(count):
    download_list[i]="https://arxiv.org/"+download_list[i]
data={'title':title_list,'subject':subjects,'download link':download_list}
data_df = pd.DataFrame(data)
today=datetime.datetime.today().strftime('%Y%m%d')
is_path=os.path.exists(today)
if not is_path:
    os.mkdir(today)
data_df.to_csv(today+'/1arxiv.csv')
# urllib3.contrib.pyopenssl.inject_into_urllib3()
# random.seed()
for i in range(count):
    urllib.request.urlretrieve(download_list[i]+'.pdf',today+'/'+norme(title_list[i])+'.pdf')
    # wget.download(download_list[i]+'.pdf',today+'/'+title_list[i]+'.pdf')
    # runDownload(4,download_list[i]+'.pdf',today+'/'+title_list[i]+'.pdf')
    print('download '+title_list[i]+' end')
