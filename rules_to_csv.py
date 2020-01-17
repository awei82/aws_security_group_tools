import boto3
import pandas as pd
import argparse

from sg_graphing.sg_graph import security_group_graph


def parse_args():
    # TODO: Implement argument parsing for output naming
    parser = argparse.ArgumentParser(description='Script for printing AWS security group rules to csv')
    parser.add_argument('-p', '--profile_name', type=str, help='AWS profile to use.')
    parser.add_argument('-v', '--vpc_id', type=str, help='filter by vpc_id', default=None)
    return parser.parse_args()

def get_tag_value(resource_json, key):
    if not resource_json.get('Tags'):
        return ''

    tags = resource_json['Tags']
    value = [tag['Value'] for tag in tags if tag['Key'] == key]
    if len(value) == 0:
        return ''
    else:
        return value[0]

def main():
    args = parse_args()
    PROFILE_NAME = args.profile_name
    VPC_ID = args.vpc_id

    # set up AWS session + EC2 client
    session = boto3.session.Session(profile_name=PROFILE_NAME)
    ec2_client = session.client('ec2')
    # ec2 = session.resource('ec2')

    vpc_filter = {'Name': 'vpc-id', 'Values': [VPC_ID]}

    # create security group graph
    filters = []
    if VPC_ID:
        filters.append(vpc_filter)

    security_groups_json = ec2_client.describe_security_groups(Filters=filters)
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
            rule_records.append([sg, security_groups[sg]['GroupName'], rule.source, rule.description, rule.port, rule.protocol])
    records_dict = dict(zip(range(len(rule_records)), rule_records))

    df = pd.DataFrame.from_dict(records_dict, orient='index',
                                columns=['GroupId', 'GroupName', 'Source', 'Description', 'Port', 'Protocol'])
    print(f'{len(df)} security group rules found')
    print('saving rules to inbound_rules.csv')
    df.to_csv('inbound_rules.csv')


    #### Create table of security groups + # of interfaces attached to each
    ni_json = ec2_client.describe_network_interfaces()
    # active_security_groups = [[x['GroupId'] for x in y['Groups']] for y in ni_json['NetworkInterfaces']]
    # active_security_groups = [x for sublist in active_security_groups for x in sublist]
    # active_security_groups = set(active_security_groups)

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
    print(f'{len(df)} security groups found')
    print('saving security group data to security_groups.csv')
    df.to_csv('security_groups.csv')


if __name__ == "__main__":
    main()