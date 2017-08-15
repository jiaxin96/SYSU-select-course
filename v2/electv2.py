#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: e:\code\脚本\教务系统抢课脚本\electv2.py
# Project: e:\code\脚本\教务系统抢课脚本
# Created Date: Wednesday, July 26th 2017, 4:42:28 pm
# Author: JX
# -----
# Last Modified: Tue Aug 15 2017
# Modified By: JX
# 说明
# 改进版本使用填入配置文件的方法可以换课和抢课
# -----
# Copyright (c) 2017 SYSU-SDCS-RJX
# 
# 学习使用
# github地址:https://github.com/jiaxin96
###
import urllib.request
from lxml import etree

from urllib.request import urlopen
import urllib.parse
from bs4 import BeautifulSoup
import requests
import re
import time
import json
import codecs


class xuanke:
    headers={
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'zh-CN,zh;q=0.8',
        'Connection':'keep-alive',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
    }
    s=requests.session()
    baseurl="https://cas.sysu.edu.cn"
    def __init__(self):
        try:
            f = codecs.open("../config.json", "r", "utf-8")
            jo = json.loads(f.read())
            f.close()
            self.todo = jo["todo"]
            self.type = jo["type"]
            self.want = jo["want"]
            self.dislike = jo["dislike"]
            self.netid = jo["netid"]
            self.passwd = jo["passwd"]
            self.dislike_jxbhNUm = [] 
            self.like_jxbhNUm = [] 
        except:
            print("没有找到config.json文件")
            exit(0)
        
    def login(self):
        loginurl='http://uems.sysu.edu.cn/elect/casLogin'
        html = requests.get(url=loginurl,headers=xuanke.headers)
        bs = BeautifulSoup(html.text, 'lxml')
        fm_value=bs.find("form",{"id":"fm1"})["action"]
        lt_value=bs.find("input",{"name":"lt"})["value"]
        ex_value=bs.find("input",{"name":"execution"})["value"]
        postdata={
            'username':self.netid,
            'password':self.passwd,
            'lt':lt_value,
            'execution':ex_value,
            '_eventId':'submit',
            'submit':'登录'
        }
        r=xuanke.s.post(xuanke.baseurl+fm_value,data=postdata, headers=xuanke.headers)
        title = etree.HTML(r.text).xpath("/html/head/title/text()")[0]

        if (title and title == "教务选课"):
            print("登录成功!")
            return r
        else:
            print("登录失败!\n请检查config.json文件")
            exit(0)
            

        
    def getType(self, courses_link):
            base_coursrs_url = r"http://uems.sysu.edu.cn/elect/s/"    
            # 专必
            zbUrl = "".join((base_coursrs_url, str(courses_link[0])))
            # 专选
            zxUrl = "".join((base_coursrs_url, str(courses_link[1])))
            # 公必
            gbUrl = "".join((base_coursrs_url, str(courses_link[2])))
            # 公选
            gxUrl = "".join((base_coursrs_url, str(courses_link[3])))
            if self.type == 'zb':
                return zbUrl
            elif self.type == 'zx':
                return zxUrl
            elif self.type == 'gx':
                return gxUrl
            elif self.type == 'gb':
                return gbUrl

    def course_handler(self,html):
        htmlTree = etree.HTML(html.text)
        courses_link = htmlTree.xpath(r"/html/body/div[@id='content']/div[1]/div[@class='displayblock'][1]/div[@class='grid-container']/table[@class='grid']/tbody/tr/td[@class='c'][2]/a/@href")

        typeurl = xuanke.getType(self,courses_link)

        electHtml=xuanke.s.get(typeurl, headers=xuanke.headers)
        
        gxtree = etree.HTML(electHtml.text)
        
        # //*[@id="courses"]/tbody/tr[1]/td[2]/a
        want_list = gxtree.xpath("/html/body/div[@id='content']/div[@class='grid-container'][2]/table[@id='courses']/tbody")[0]
        want_names = want_list.xpath("//tr/td[2]/a")
        # print(want_names[0].text)


        # //*[@id="elected"]/tbody/tr[1]/td[3]/a
        dislike_list = gxtree.xpath('//*[@id="elected"]/tbody')[0]
        dilike_names = gxtree.xpath('//*[@id="elected"]/tbody/tr/td[3]/a')
        # print(dilike_names[0].text)
        
        sid = electHtml.url.split('&')[-1].split("=")[-1]
        xkjdszid = gxtree.xpath('//input[@name="xkjdszid"]/@value')[0]
        
        hasDone = False

        for nametag in want_names:
            name = nametag.text
            for coursename in self.want:
                if (name.find(str(coursename)) != -1):
                    self.like_jxbhNUm.append(nametag.xpath('../../td[1]/a/@jxbh')[0])
        for nametag in dilike_names:
            name = nametag.text
            for coursename in self.dislike:
                if (name.find(str(coursename)) != -1):
                    self.dislike_jxbhNUm.append(nametag.xpath('../../td[1]/a/@jxbh')[0])
        xuanke.postDataToSelect(self,xkjdszid,sid)


    def postDataToSelect(self,xkjdszid,sid):
        print("提交数据")
        
        unelect_postUrl = "http://uems.sysu.edu.cn/elect/s/unelect"
        
        elect_postUrl = "http://uems.sysu.edu.cn/elect/s/elect"
        elect_postData = {
            "jxbh":"",
            "xkjdszid":xkjdszid,
            "sid":sid
        }
        postHeaders = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Connection':'keep-alive',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
            'Host':'uems.sysu.edu.cn',
            'Origin':'http://uems.sysu.edu.cn',
            'Referer':'http://uems.sysu.edu.cn/elect/s/courses?xkjdszid='+str(xkjdszid)+'&fromSearch=false&sid='+str(sid),
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'X-Requested-With':'XMLHttpRequest'
        }
        i = 0
        while(True):
            tjxb = []
            for jxbh in self.dislike_jxbhNUm:
                elect_postData["jxbh"] = jxbh
                tjxb.append(jxbh);
                f = xuanke.s.post(url=unelect_postUrl, headers=postHeaders, data=elect_postData)
                jo = json.loads(f.text)
                if (jo['err']['code'] == 0):
                    print("退课成功")
                    del self.dislike_jxbhNUm[self.dislike_jxbhNUm.index(jxbh)]


            for jxbh in self.like_jxbhNUm:
                elect_postData["jxbh"] = jxbh
                f = xuanke.s.post(url=elect_postUrl, headers=postHeaders, data=elect_postData)
                jo = json.loads(f.text)
                if (jo['err']['code'] == 0):
                    del self.like_jxbhNUm[self.like_jxbhNUm.index(jxbh)]
            
            if (self.todo == 3):
                for jxbh in tjxb:
                    elect_postData["jxbh"] = jxbh
                tjxb.append(jxbh);
                f = xuanke.s.post(url=elect_postUrl, headers=postHeaders, data=elect_postData)
                jo = json.loads(f.text)
                if (jo['err']['code'] == 0):
                    print("换课失败")
                    self.dislike_jxbhNUm.append(jxbh)
                    del tjxb[tjxb.index(jxbh)]

            time.sleep(1)
            if (i % 6 == 0):
                print("第%d次" % i)
            i = i + 1
            
            if (self.like_jxbhNUm.count == 0 and self.todo != 2):
                break;
                print("选课完成")
            if (self.like_jxbhNUm.count == 0 and self.todo == 1):
                break;
                print("选课完成")

            if (self.dislike_jxbhNUm.count == 0 and self.todo == 2):
                break
                print("退课成功")
            if (self.like_jxbhNUm.count == 0 and self.todo == 2):
                break
                print("换课成功")

            if (self.dislike_jxbhNUm.count == 0 and self.like_jxbhNUm.count == 0):
                break
                print("成功")

            

        


def main():    
    xuanke1 = xuanke()
    xuanke1.course_handler(xuanke1.login())
    
if __name__ == '__main__':
    main()
