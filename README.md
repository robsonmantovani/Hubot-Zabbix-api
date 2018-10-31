# Hubot Zabbix script that let's you:
- create maintenance period for an host or group of hosts
- acknowledge events

 ### Works with 
 
 * Zabbix 2.4

### Configuration

In *zabbix.py*, add your zabbix server's fqdn:

```py
api = "https://<<zabbixserver_fqdn>>/api_jsonrpc.php"
```

Copy `secrets.json.example` to `secrets.json`, add a username and password with api permissions:

```json
{
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {
        "user": "<username>",
        "password": "<password>"
    },
    "id": 1,
    "auth": null
}
```

### Hubot Commands:

* To  create a maintenance period of 1 hour for host group PAO:
`hubot pause me group pao`

* To create a maintenance period of 6 hours for paoad1 host:
`hubot pause me host paoad1 for 6 hours`

* To delete maintenance for group pao:
`hubot unpause me group pao`

* To delete maintenance for host paoad1:
`hubot unpause me host paoad1`

*  Acknowledge eventid 9376146 and add comment: "pb resolved": 
`hubot zaback 9376146 pb resolved`