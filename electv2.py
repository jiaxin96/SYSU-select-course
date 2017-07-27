#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: e:\code\脚本\教务系统抢课脚本\electv2.py
# Project: e:\code\脚本\教务系统抢课脚本
# Created Date: Wednesday, July 26th 2017, 4:42:28 pm
# Author: JX
# -----
# Last Modified: Thu Jul 27 2017
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
            f = codecs.open("config.json", "r", "utf-8")
            jo = json.loads(f.read())
            f.close()
            self.todo = jo["todo"]
            self.type = jo["type"]
            self.want = jo["want"]
            self.dislike = jo["dislike"]
            self.netid = jo["netid"]
            self.passwd = jo["passwd"]
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
            print("选课成功!")
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

    def selectCourse(self,html,arguments):
        print("开始选课")
        htmlTree = etree.HTML(html.text)
        courses_link = htmlTree.xpath(r"/html/body/div[@id='content']/div[1]/div[@class='displayblock'][1]/div[@class='grid-container']/table[@class='grid']/tbody/tr/td[@class='c'][2]/a/@href")
        coursename = arguments.get("<courseName>")
        typeurl = xuanke.getType(self,arguments,courses_link)

        electHtml=xuanke.s.get(typeurl, headers=xuanke.headers)
        gxtree = etree.HTML(electHtml.text)
        
        courses_list = gxtree.xpath("/html/body/div[@id='content']/div[@class='grid-container'][2]/table[@id='courses']/tbody")[0]
        names = courses_list.xpath("//tr/td[2]/a")
        
        sid = electHtml.url.split('&')[-1].split("=")[-1]
        xkjdszid = gxtree.xpath('//input[@name="xkjdszid"]/@value')[0]
        
        hasDone = False

        for nametag in names:
            name = nametag.text
            if (name.find(str(coursename)) != -1):
                jxbhNUm = nametag.xpath('../../td[1]/a/@jxbh')[0]
                xuanke.postDataToSelect(self,jxbhNUm,xkjdszid,sid)
                hasDone = True
                break
        if hasDone==False:
            print("已经选上此课 或者 已经没有此课程")
    
    def postDataToSelect(self,jxbh,xkjdszid,sid):
        print("提交数据")
        postUrl = "http://uems.sysu.edu.cn/elect/s/elect"
        postData = {
            "jxbh":jxbh,
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
            f = xuanke.s.post(url=postUrl, headers=postHeaders, data=postData)
            i = i + 1
            jo = json.loads(f.text)
            if (jo['err']['code'] == 0):
                print("选课成功")
                break
            if (i % 10 == 0):
                print("正在进行第%d次尝试！"% i)
            time.sleep(2)

        


def main():    
    xuanke1 = xuanke()
    xuanke1.login()
    
if __name__ == '__main__':
    main()