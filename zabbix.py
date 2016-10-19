#!/usr/bin/env python

# Description:
#   Uses Zabbix 2.4 api to :
#  - create maintenance period for host or group of hosts
#  - acknowledge events

import argparse
import json
import requests
import re
import time


# Zabbix api fqdn
api = "https://<<zabbix server>>/api_jsonrpc.php"

# Credential file to connect to Zabbix api. File managed by puppet.
secrets = open('<<file path>>secrets.json').read()
headers = {
  'content-type': "application/json-rpc",
  'cache-control': "no-cache",
  'postman-token': "561fd14a-0622-1d41-4c60-d7582b740e5e"
  }


# Generate a token to connect ot Zabbix api
def get_token(creds):
  try:
    response = requests.request("POST", api, data=creds, headers=headers)
  except requests.exceptions.RequestException as e:
    print e
    sys.exit(1)
  else:
    try:
      return json.loads(response.text)
    except:
      raise Exception ('problem getting a token')


# Return a host id with a host name
def get_host_id(host):
    hostid = re.sub("host:", "", host, count=1)
    method = 'host.get'
    params = {
                  'output': 'extend',
                  'filter': {
                              'host': [hostid]
                            }
                }
    return apicall(method, params, 'hostid')


# Return a group id with a group name
def get_group_id(group):
    groupid = re.sub("group:", "", group, count=1)
    method = 'hostgroup.get'
    params = {
                  'output': 'extend',
                  'filter': {
                              'name': [groupid]
                            }
                }
    return apicall(method, params, 'groupid')


# Generate a POST request to Zabbix server
def apicall(method, params, response, exception=''):

    token = get_token(secrets)

    response_options = ['maintenanceid', 'name', 'hostid', 'groupid']

    data = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'auth': token['result'],
            'id': token['id'],
            }
    try:
        responsecall = requests.request("POST", api, data=json.dumps(data), headers=headers)
        response_formated = json.loads(responsecall.text)
    except requests.exceptions.RequestException as e:
        print 'error:' + e
        sys.exit(1)
    else:
        try:
            if response in response_options:
                return response_formated['result'][0][response]
            elif response == 'eventid':
                return response_formated
            else:
                return response
        except:
            raise Exception(exception)


class Maintenance(object):

    def __init__(self, args):

        self.args = args

    @staticmethod
    def get_maintenance_group_id(group):
        method = 'maintenance.get'
        params = {
                'output': 'extend',
                'selectHosts': 'extend',
                'selecttimeperiods': 'extend',
                'groupids': get_group_id(group),
                }
        exception = 'No maintenance for group: ' + group
        return apicall(method, params, 'maintenanceid', exception)

    @staticmethod
    def get_maintenance_name(host_group):
        if re.search(r'group:', host_group):
            group_type = 'groupids'
            hostid = get_group_id(host_group)
        else:
            group_type = 'hostids'
            hostid = get_host_id(host_group)

        method = 'maintenance.get'
        params = {
                'output': 'extend',
                'selectHosts': 'extend',
                'selecttimeperiods': 'extend',
                group_type: hostid
                }
        response = 'maintenance_name'
        exception = 'No maintenance for host: ' + host_group
        return apicall(method, params, response, exception)

    @staticmethod
    def get_maintenance_host_id(host):
        method = 'maintenance.get'
        params = {
            'output': 'extend',
            'selectHosts': 'extend',
            'selecttimeperiods': 'extend',
            'hostids': get_host_id(host),
            }
        exception = 'No maintenance for host: ' + host
        return apicall(method, params, 'maintenanceid', exception)

    def del_maintenance(self):
        if self.args.group:
            mid = self.get_maintenance_group_id(self.args.group)
            hostgroup = self.args.group
        elif self.args.host:
            mid = self.get_maintenance_host_id(self.args.host)
            hostgroup = self.args.host
        else:
            raise Exception('please provide a host name or a group name')
        method = 'maintenance.delete'
        params = [mid]
        response = 'maintenance for ' + hostgroup + ' was deleted successfully'
        return apicall(method, params, response, '')

    def start_maintenance_host(self):
        if self.args.host:
            hostid = get_host_id(self.args.host)
        else:
            raise Exception('please provide an host name')
        if self.args.hours:
            howlong = int(self.args.hours)
        else:
            raise Exception('please provide a maintenance duration in hours')
        if self.args.username:
            username = self.args.username
        else:
            username = ''

        now = int(time.time())
        until = int(time.time()) + howlong*3600
        method = 'maintenance.create'
        params = {
                'name': 'pause_' + self.args.host,
                'active_since': now,
                'active_till': until,
                'hostids': [hostid],
                'description': 'created by: ' + username,
                'timeperiods': [
                    {
                    'timeperiod_type': 0,
                    'period': howlong*3600,
                    }
                ],
            }
        response = 'Zabbix monitoring was paused for ' + str(howlong) + ' hour(s) on ' + str(self.args.host)
        return apicall(method, params, response)

    def start_maintenance_group(self):
        if self.args.group:
            groupid = get_group_id(self.args.group)
        else:
            raise Exception('please provide a group name')
        if self.args.hours:
            howlong = int(self.args.hours)
        else:
            raise Exception('please provide a maintenance duration in hours')
        if self.args.username:
            username = self.args.username
        else:
            username = ''

        now = int(time.time())
        until = int(time.time()) + howlong*3600

        method = 'maintenance.create'
        params = {
                'name': 'pause_' + self.args.group,
                'active_since': now,
                'active_till': until,
                'groupids': [groupid],
                'description': 'created by: ' + username,
                'timeperiods': [
                    {
                    'timeperiod_type': 0,
                    'period': howlong*3600,
                    }
                ],
            }
        response = 'Zabbix monitoring was paused for ' + str(howlong) + ' hour(s) on ' + str(self.args.group)
        return apicall(method, params, response)


def eventid(args):
    method = 'event.get'
    params = {
        'output': 'extend',
        'select_acknowledges': 'extend',
        'objectids': args.trigger,
        'sortfield': ['clock', 'eventid'],
        'sortorder': 'DESC'
        }
    return apicall(method, params, 'eventid')


def acknowledge(args):
    if args.m:
        message = args.m
    else:
        message = ""
    method = 'event.acknowledge'
    params = {
        'eventids': args.ack,
        'message': message
        }
    response = 'alert ' + str(args.ack) + ' has been acked sucessfully.'
    return apicall(method, params, response)


def argument_check(args):
    pause = Maintenance(args)
    if args.pause:
        if args.host and args.hours:
            print(pause.start_maintenance_host())
        elif args.group and args.hours:
            print(pause.start_maintenance_group())
    elif args.unpause:
        print(pause.del_maintenance())
    elif args.ack:
        print(acknowledge(args))
    elif args.trigger:
        print(eventid(args))
    else:
        raise Exception('please select an host or a group and a time during')


def main():

    app_caption = 'Zabbix api calls'
    arg_caption_pause = 'Create a maintenance period for a host or group'
    arg_caption_unpause = 'Delete a maintenance period for a host or group'
    arg_caption_host = 'Host name'
    arg_caption_group = 'Group name'
    arg_caption_hours = 'how long the maintenance will be for in hours'
    arg_caption_trigger = 'shows trigger events'
    arg_caption_ack = 'Eventid to ack'
    arg_caption_m = 'ack comment'
    arg_caption_username = 'username'

    parser = argparse.ArgumentParser(description=app_caption)
    parser.add_argument('--pause', action='store_true',
                        help=arg_caption_pause)
    parser.add_argument('--unpause', action='store_true',
                        help=arg_caption_unpause)
    parser.add_argument('--host', type=str,
                        help=arg_caption_host)
    parser.add_argument('--group', type=str,
                        help=arg_caption_group)
    parser.add_argument('--hours', type=int,
                        help=arg_caption_hours)
    parser.add_argument('--trigger', type=int,
                        help=arg_caption_trigger)
    parser.add_argument('--ack', type=int,
                        help=arg_caption_ack)
    parser.add_argument('--m', type=str,
                        help=arg_caption_m)
    parser.add_argument('--username', type=str,
                        help=arg_caption_username)


    args = parser.parse_args()
    argument_check(args)

if __name__ == '__main__':
    main()
