import collections


Security_Group_Rule = collections.namedtuple('Security_Group_Rule', 'source description port protocol')

def security_group_graph(security_group_json, direction='inbound', ip_version='v4', show_ports=False):
    """
    TODO: add support for IP ranges - to and from ports, all ports
    TODO: add IPv6
    TODO: method of showing individual port rules.
    :param security_group_json: list of json objects from describe_security_groups
    :param direction: graph inbound vs outbound rules
    :param ip_version: which ip version to show rules for  [Not implemented yet]
    :param show_ports: show individual ports as separate nodes in grpah [Not implemented yet]
    :return: adjacency list of GroupId to Security_Group_Rule mappings
    """
    graph = {}
    security_groups = {x['GroupId']: x['GroupName'] for x in security_group_json}

    for group_id in security_groups.keys():
        sg = [x for x in security_group_json if x['GroupId'] == group_id][0]
        rules = []

        if direction=='inbound':
            direction_tag = 'IpPermissions'
        elif direction == 'outbound':
            direction_tag = 'IpPermissionsEgress'
        else:
            raise Exception("direction must be either 'inbound' or 'outbound'")

        port_address_mapping = [(x.get('FromPort'), x.get('IpRanges'), x.get('IpProtocol')) for x in sg[direction_tag]]
        for port, addresses, protocol in port_address_mapping:
            for address in addresses:
                rules.append(Security_Group_Rule(address.get('CidrIp'), address.get('Description'), port, protocol))

        port_sg_mapping = [(x.get('FromPort'), x.get('UserIdGroupPairs'), x.get('IpProtocol')) for x in sg[direction_tag]]
        for port, rule_sg_s, protocol in port_sg_mapping:
            for rule_sg in rule_sg_s:
                rules.append(Security_Group_Rule(rule_sg['GroupId'], rule_sg.get('Description'), port, protocol))

        graph[group_id] = rules
        #print(sg, rules)

    return graph
