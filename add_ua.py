#!/usr/bin/env python
# encoding: utf-8

import requests
import re
import collections
import socket
from sys import argv
from os import popen as bash

URL = "http://jump.t.nxin.com/"


# requests = requests.session()

class JumpServer(object):
    def __init__(self, username, password):
        self._cookie = None
        self.username = username
        self.password = password

    def get_cookie(self):
        '''@:return connect jumpserver,return cookie'''
        if not self._cookie:
            url = URL + "login/"
            data = {
                "username": self.username,
                "password": self.password
            }
            res = requests.post(url=url, data=data)
            self._cookie = res.cookies
        return self._cookie

    def add_resource(self, hostname, username, password,
                     ip, port=22, group=None, is_active=1):
        '''@ add host'''
        url = URL + "jasset/asset/add/"
        data = {
            "hostname": hostname,
            "username": username,
            "password": password,
            "ip": ip,
            "port": port,
            "group": group,
            "is_active": is_active
        }
        res = requests.post(url=url, data=data, cookies=self.get_cookie())

        return 'add asset result {0}'.format(res.status_code)

    def get_assetgroups_list(self):
        '''get all groups'''
        url = URL + 'jasset/group/list/'

        rs = requests.get(url, cookies=self.get_cookie())
        # list页面组名后面有个空格，主机数量质量的没有
        return re.compile('<a href="/jasset/asset/list/\?group_id=(\d)">(\w+) </a>').findall(rs.text)

    def get_role_id(self, jperm_name):
        '''get role's id '''
        url = URL + 'jperm/role/list/'
        rs = requests.get(url, cookies=self.get_cookie())

        try:
            ###get role's id by role name
            return re.compile('<a href="/jperm/role/detail/\?id=(.*)">{0}'.format(jperm_name)).findall(rs.text)[0]

        except IndexError:
            assert 'jump server have no asset user {0}, add it if needed'.format(jperm_name)

    def asset_add_user(self, role_name, role_password, role_key=None, role_comment=None):
        '''add role user if need'''
        url = URL + 'jperm/role/add/'
        data = {
            'role_name': role_name,
            'role_password': role_password,
            'role_key': role_key,
            'role_comment': role_comment,
        }

        res = requests.post(url=url, data=data, cookies=self.get_cookie())

        return res.status_code

    def asset_push_user(self, asset_groups=None, assets=None, comment=None, use_publicKey=1, jperm_name='admin'):
        '''push role user to the asset'''
        if asset_groups or assets:
            ###get role's id  to push role user
            url = URL + 'jperm/role/push/?id={0}'.format(self.get_role_id(jperm_name))

            rs = requests.get(url, cookies=self.get_cookie())
            ###get assets id to post
            assets_id = re.compile('<option value=(.*)>{0}'.format(assets)).findall(rs.text)[0].split('"')[1]
            data = {
                'asset_groups': asset_groups,
                'assets': assets_id,
                'comment': comment,
                'use_publicKey': use_publicKey,
            }

            res = requests.post(url=url, data=data, cookies=self.get_cookie())
            return 'push role {0} result {1}'.format(jperm_name,res.status_code)
        else:
            raise 'asset_groups or assets can\'t be all null'


def main():
    js = JumpServer("liuniansheng", "")
    gl = js.get_assetgroups_list()
    group_dict = collections.OrderedDict()
    for g in gl:
        group_dict[g[0]] = g[1]

    ##帮助文档
    def help_usage():
        print 'number for group list:\n'
        for k, v in group_dict.items():
            ###中文名字要转码
            print 'num {0} for group {1}'.format(k, v.encode("utf-8"))

        print '\nusage : argv1 is int number of group, argv2 is str password for root of localhost'
        #

    host = socket.gethostname()
    user = 'root'
    ##获取主机内网ip，云主机模板都是eth0
    ip = bash("ifconfig eth0 | grep  'inet addr'|awk '{print $2}'|awk -F: '{print $2}'").read()
    ##输入错误打印帮助文档
    try:
        print js.add_resource(hostname=host, username=user, password=argv[2], ip=ip, port=22,
                        group=argv[1], is_active=1)
        jperm_name_list = ['admin', 'develop']
        for jperm_name in jperm_name_list:
            print js.asset_push_user(assets=host, jperm_name=jperm_name)
    except IndexError, e:
        print e
        help_usage()


if __name__ == "__main__":
    main()
