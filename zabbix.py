#!/usr/bin/env python

# Description:
#   Uses Zabbix api to :
#  - create maintenance period for host or group of hosts (site code only for now e.g sfo sfo2 iad)
#  - acknowledge events

import argparse
import json
import re
import requests
import time


# Zabbix api fqdn
api = "<<zabbix server fdqdn>>/api_jsonrpc.php"

# Credential file to connect to Zabbix api. File managed by puppet.
secrets = open('secrets.json').read()
headers = {
  'content-type': "application/json-rpc",
  'cache-control': "no-cache",
  }


# Generate a token to connect ot Zabbix api
def get_token(creds):
  try:
    response = requests.request("POST", api, data=creds, headers=headers)
  except:
    raise Exception ('problem getting a token')
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

    response_options = ['maintenanceid', 'name', 'hostid', 'groupid', 'name']

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
            print Exception(exception)


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

    def get_maintenance_name(self):
        if self.args.group:
            group_type = 'groupids'
            hostid = get_group_id(self.args.group)
        elif self.args.host:
            group_type = 'hostids'
            hostid = get_host_id(self.args.host)
        else:
            Exception('Please provide either a group or a host name')

        method = 'maintenance.get'
        params = {
                'output': 'extend',
                'selecttimeperiods': 'extend',
                group_type: hostid
                }
        response = 'name'
        exception = 'No maintenance'
        if hostid:
            return apicall(method, params, response, exception)
        else:
            raise Exception('Enter a valid host or group name')

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
        if self.args.group and re.search(r'pause_', self.get_maintenance_name()):
            mid = self.get_maintenance_group_id(self.args.group)
            hostgroup = self.args.group
        elif self.args.host and re.search(r'pause_', self.get_maintenance_name()):
            mid = self.get_maintenance_host_id(self.args.host)
            hostgroup = self.args.host
        else:
            raise Exception('No maintenance found to delete')
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
        if hostid is None:
          return 'please provide a valid host name'
        else:
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
        if groupid is None:
          return 'please provide a valid group name'
        else:
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
        message = 'no comment added'
    if args.username:
        username = args.username
    else:
        username = 'no username available'
    method = 'event.acknowledge'
    params = {
        'eventids': args.ack,
        'message': username + ': ' + message
        }
    response = 'alert ' + str(args.ack) + ' has been acked sucessfully.'
    return apicall(method, params, response)


def arguments_to_functions(args):
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
    elif args.maintenancename:
        print(pause.get_maintenance_name())
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
    arg_caption_maintenancename = 'return the maintenance name'

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
    parser.add_argument('--maintenancename', action='store_true',
                        help=arg_caption_maintenancename)


    args = parser.parse_args()
    arguments_to_functions(args)

if __name__ == '__main__':
    main()
