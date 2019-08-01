import boto3
import pydot

from sg_graph import security_group_graph

# TODO: Implement argument parsing to pass in AWS profiles + output naming


session = boto3.session.Session()
ec2_client = session.client('ec2')

#### get all security group JSON data
security_groups_json = ec2_client.describe_security_groups()
security_groups_json = security_groups_json['SecurityGroups']

security_groups = {x['GroupId']: x['GroupName'] for x in security_groups_json}


#### get list of active security groups
ni_json = ec2_client.describe_network_interfaces()
ni_security_groups = a = [[x['GroupId'] for x in y['Groups']] for y in ni_json['NetworkInterfaces']]
ni_security_groups = [x for sublist in ni_security_groups for x in sublist]
ni_security_groups = set(ni_security_groups)

#### filter security_groups_json to only include active groups
active_groups_json = [x for x in security_groups_json if x['GroupId'] in ni_security_groups]


graph = security_group_graph(active_groups_json)


def convert_to_printable(graph):
    printable_graph = {}
    for group_id, rules in graph.items():
        printable_graph[f'{group_id}\n{security_groups[group_id]}'] = rules

    for node, links in printable_graph.items():
        new_links = []
        for link in links:
            if link.source[0] == 's':   # security group
                new_link = f'{link.source}\n{security_groups[link.source]}'
            else:                       # ip
                new_link = f'{link.source}\n{link.description if link.description else ""}'
            new_links.append(new_link)
            printable_graph[node] = new_links

    return printable_graph

printable_graph = convert_to_printable(graph)


#### Create pydot graph
nodes = []
for group in printable_graph.keys():
    nodes.append(group)
print(f'{len(nodes)} active security groups found.')

edges = []
for node , links in printable_graph.items():
    node_edges = [(node, link) for link in links]
    edges += node_edges
edges = set(edges)
print(f'{len(edges)} edges found.')

pydot_nodes = [pydot.Node(x) for x in nodes]
pydot_edges = [pydot.Edge(x[0],x[1], dir='back') for x in edges]

G = pydot.Dot(graph_type='digraph', rankdir='LR')

for n in pydot_nodes:
    G.add_node(n)
for e in pydot_edges:
    G.add_edge(e)

G.write_png('graph.png')
print('graph saved to graph.png')


