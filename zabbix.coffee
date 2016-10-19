# Description:
#   Uses Zabbix api to :
#  - create maintenance period for host or group of hosts
#  - acknowledge events
#
# Commands:
#   marley pause me group pao - create a maintenance period of 1 hour for host group PAO
#   marley pause me host paoad1 for 6 hours -  create a maintenance period of 6 hours for paoad1 host
#   marley unpause me group pao - delete maintenance for group pao
#   marley unpause me host paoad1 - delete maintenance for host paoad1
#   marley zaback 9376146 pb resolved - Acknowledge eventid 9376146 and add comment: "pb resolved"

cp = require 'child_process'

module.exports = (robot) ->
  robot.respond /pause\sme\s(group)\s(\w{3,4})\s(for)\s(\d)\s(\w+)/i, (msg) ->
   pause_group = msg.match[2]
   howlong = if msg.match[4] then msg.match[4] else 1
   cp.execFile "bin/zabbix.py", ['--pause', '--group', pause_group, '--hours', howlong, '--username', msg.message.user.name], (error, stdout, stderr)->
     msg.send stdout

  robot.respond /pause\sme\s(group)\s(\w{3,4})$/i, (msg) ->
   pause_group = msg.match[2]
   cp.execFile "bin/zabbix.py", ['--pause', '--group', pause_group, '--hours', 1, '--username', msg.message.user.name], (error, stdout, stderr)->
     msg.send stdout

  robot.respond /pause\sme\s(host)\s(\w+)$/i, (msg) ->
   pause_host = msg.match[2]
   cp.execFile "bin/zabbix.py", ['--pause', '--host', pause_host, '--hours', 1, '--username', msg.message.user.name], (error, stdout, stderr)->
     msg.send stdout

  robot.respond /unpause\sme\sgroup\s(\w+)/i, (msg) ->
   unpause_group = msg.match[1]
   cp.execFile "bin/zabbix.py", ['--unpause', '--group', unpause_group], (error, stdout, stderr)->
     msg.send stdout

  robot.respond /unpause\sme\shost\s(\w+)/i, (msg) ->
   unpause_host = msg.match[1]
   cp.execFile "bin/zabbix.py", ['--unpause', '--host', unpause_host], (error, stdout, stderr)->
     msg.send stdout

  robot.respond /pause\sme\shost\s(\w+)\s(for)\s(\d)\s(\w+)/i, (msg) ->
   group = msg.match[1]
   howlong = msg.match[3]
   cp.execFile "bin/zabbix.py", ['--pause', '--host', group, '--hours', howlong, '--username', msg.message.user.name], (error, stdout, stderr)->
     msg.send stdout

  robot.respond /zaback\sme\s(\d+)\s(.*)/i, (msg) ->
   ackevent = msg.match[1]
   ackcomment = msg.match[2]
   cp.execFile "bin/zabbix.py", ['--ack', ackevent, '--m', ackcomment], (error, stdout, stderr)->
     msg.send stdout
