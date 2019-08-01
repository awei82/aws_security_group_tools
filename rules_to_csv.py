import boto3
import pandas as pd

from sg_graph import security_group_graph

# TODO: Implement argument parsing to pass in AWS profiles + output naming


def get_tag_value(resource_json, key):
    if not resource_json.get('Tags'):
        return ''

    tags = resource_json['Tags']
    value = [tag['Value'] for tag in tags if tag['Key'] == key]
    if len(value) == 0:
        return ''
    else:
        return value[0]


session = boto3.session.Session()
ec2_client = session.client('ec2')
#ec2 = session.resource('ec2')

security_groups_json = ec2_client.describe_security_groups()
security_groups_json = security_groups_json['SecurityGroups']


security_groups = {x['GroupId']: {'GroupName': x['GroupName'],
                                  'Description': x['Description'],
                                  'Name': get_tag_value(x, 'Name'),
                                  'owner': get_tag_value(x, 'owner'),
                                  'team': get_tag_value(x, 'team'),
                                  'role': get_tag_value(x, 'role'),
                                  }
                            for x in security_groups_json}

graph = security_group_graph(security_groups_json)


#### Create table of security group rules
rule_records = []
for sg, rules in graph.items():
    for rule in rules:
        rule_records.append([sg, security_groups[sg], rule.source, rule.description, rule.port, rule.protocol])
records_dict = dict(zip(range(len(rule_records)), rule_records))

df = pd.DataFrame.from_dict(records_dict, orient='index', columns=['GroupId','GroupName','Source','Description','Port','Protocol'])
df.to_csv('inbound_rules.csv')


#### Create table of security groups + # of interfaces attached to each
ni_json = ec2_client.describe_network_interfaces()
active_security_groups = a = [[x['GroupId'] for x in y['Groups']] for y in ni_json['NetworkInterfaces']]
active_security_groups = [x for sublist in active_security_groups for x in sublist]
active_security_groups = set(active_security_groups)

sg_records = []
for group_id, group_data in security_groups.items():
    n_attached = len([x for x in ni_json['NetworkInterfaces'] if group_id in [y['GroupId'] for y in x['Groups']]])
    sg_records.append([group_id,
                    group_data['GroupName'],
                    group_data['Description'],
                    n_attached,
                    group_data['Name'],
                    group_data['owner'],
                    group_data['team'],
                    group_data['role']
                   ])

records_dict = dict(zip(range(len(sg_records)), sg_records))
df = pd.DataFrame.from_dict(records_dict, orient='index', columns=['GroupId',
                                                                   'GroupName',
                                                                   'Description',
                                                                   'Interfaces_attached',
                                                                   'Name',
                                                                   'owner',
                                                                   'team',
                                                                   'role'])
df.to_csv('active_security_groups.csv')
