import pandas as pd
import networkx as nx
import re
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import io
import base64
from Neo4jSearch import GenerateNodeColors
from PubMedSearch import PubMedCoMentionsSimple
import dash_cytoscape as cyto




def tryint(s):
    """
    Return an int if possible, or `s` unchanged.
    """
    try:
        return int(s)
    except ValueError:
        return s

def alphanum_key(s):
    """
    Turn a string into a list of string and number chunks.

    >>> alphanum_key("z23a")
    ["z", 23, "a"]

    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

def human_sort(l):
    """
    Sort a list in the way that humans expect.
    """
    l.sort(key=alphanum_key)

def networx2cytoscape(G):
    cyto.Cytoscape(
        id='cytoscape-two-nodes',
        layout={'name': 'preset'},
        style={'width': '100%', 'height': '400px'},
        elements=[
            {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 75, 'y': 75}},
            {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 200, 'y': 200}},
            {'data': {'source': 'one', 'target': 'two'}}
        ]
    )
    #xy_positions = nx.nx_agraph.graphviz_layout(G)
    cy = nx.readwrite.json_graph.cytoscape_data(G)
    # for n in cy['elements']['nodes']:
    #     for v in n.items():
    #         v['label'] = v.pop('value')
    print(cy)
    #print(xy_positions)
    return 

def CytoscapeVisualize(df, selected_rows):
    cols = df.columns
    node_cols = []
    edge_cols = []
    searched_cols = []
    count_cols = [x for x in cols if " counts" in x]
    print(selected_rows)
    for col in cols: 
        if col.count('node')==1:# and df.at[row,col]!="?":
            if "protein names" not in col:
                searched_cols.append(col)
                node_cols.append(col)
        elif col.count('edge')==1:# and df.at[row,col]!="?":
            searched_cols.append(col)
            edge_cols.append(col)
    human_sort(node_cols)
    human_sort(edge_cols)
    print(searched_cols)
    print(node_cols)
    print(edge_cols)
    print(count_cols)

    node_elements = [
        {'data': {'id':[], 'label':[]},
        'position': {'x':[], 'y':[]},
        'locked': False,
        'grabbable': True,
        'selectable': True,
        'selected': False,
        #'classes': 'blue square'
        }
    ]

    edge_elements = [
        {'data': {'source':[], 'target':[], 'label':[]}}
    ]
    return True

def VisualizeAnswerRow(df,selected_rows,elements,edge_labels=True, pubmed_comentions=True, all_rows=False):
    # if not selected_rows:
    #     return elements
    cols = df.columns
    node_cols = []
    edge_cols = []
    searched_cols = []
    count_cols = [x for x in cols if " counts" in x]
    print(selected_rows)

    for col in cols: 
        if col.count('node')==1:# and df.at[row,col]!="?":
            if "protein names" not in col:
                searched_cols.append(col)
                node_cols.append(col)
        elif col.count('edge')==1:# and df.at[row,col]!="?":
            searched_cols.append(col)
            edge_cols.append(col)
    #human_sort(searched_cols)
    human_sort(node_cols)
    human_sort(edge_cols)
    #df = df[searched_cols].reindex(searched_cols, axis=1)
    print(searched_cols)
    print(node_cols)
    print(edge_cols)
    print(count_cols)
    nodetypecolors = GenerateNodeColors([x[7:].replace('`','').replace('biolink:','') for x in node_cols])
    added_nodes = {}
    node_colors = []
    added_edges = []
    if all_rows == True:
        selected_rows = [x for x in range(len(df))]
    for row in selected_rows:
        for col in node_cols:
            if df.at[row,col] != "?":
                if df.at[row,col].replace(' ','\n') in added_nodes.keys():
                    continue
                else:
                    added_nodes.update({df.at[row,col].replace(' ','\n'):col[7:].replace('`','').replace('biolink:','')})
                    node_colors.append(nodetypecolors[col[7:].replace('`','').replace('biolink:','')])

        for i in range(len(searched_cols)):

            if 'edge' in searched_cols[i]:
                predicate_pos = cols.get_loc(searched_cols[i])
                if df.iat[row,predicate_pos] == "?":
                    continue   
                #n_pos = node_cols.get_loc(df = df.reindex(human_sort(cols), axis=1))
                subject_pos = cols.get_loc(searched_cols[i-1])
                if df.iat[row,subject_pos] == "?":
                    n_pos = node_cols.index(searched_cols[i-1])
                    a = 1
                    while df.iat[row,subject_pos] == "?":
                        if (n_pos+a) <= (len(node_cols)-1) & (n_pos-a) >= 0:
                            if node_cols[n_pos+a][:6] == node_cols[n_pos][:6]:
                                subject_pos = cols.get_loc(node_cols[n_pos+a])
                            elif node_cols[n_pos-a][:6] == node_cols[n_pos][:6]:
                                subject_pos = cols.get_loc(node_cols[n_pos-a])
                            else:
                                a+=1
                                continue
                        elif (n_pos+a) <= (len(node_cols)-1) & (n_pos-a) < 0:
                            if node_cols[n_pos+a][:6] == node_cols[n_pos][:6]:
                                    subject_pos = cols.get_loc(node_cols[n_pos+a])
                            else:
                                a+=1
                                continue
                        elif (n_pos+a) > (len(node_cols)-1) & (n_pos-a) >= 0:
                            if node_cols[n_pos-a][:6] == node_cols[n_pos][:6]:
                                    subject_pos = cols.get_loc(node_cols[n_pos-a])
                            else:
                                a+=1
                                continue
                        else:
                            a+=1

                object_pos = cols.get_loc(searched_cols[i+1])
                if df.iat[row,object_pos] == "?":
                    n_pos = node_cols.index(searched_cols[i+1])
                    a = 1
                    while df.iat[row,object_pos] == "?":
                        if (n_pos+a) <= (len(node_cols)-1) & (n_pos-a) >= 0:
                            if node_cols[n_pos+a][:6] == node_cols[n_pos][:6]:
                                object_pos = cols.get_loc(node_cols[n_pos+a])
                            elif node_cols[n_pos-a][:6] == node_cols[n_pos][:6]:
                                object_pos = cols.get_loc(node_cols[n_pos-a])
                            else:
                                a+=1
                                continue
                        elif (n_pos+a) <= (len(node_cols)-1) & (n_pos-a) < 0:
                            if node_cols[n_pos+a][:6] == node_cols[n_pos][:6]:
                                    object_pos = cols.get_loc(node_cols[n_pos+a])
                            else:
                                a+=1
                                continue
                        elif (n_pos+a) > (len(node_cols)-1) & (n_pos-a) >= 0:
                            if node_cols[n_pos-a][:6] == node_cols[n_pos][:6]:
                                    object_pos = cols.get_loc(node_cols[n_pos-a])
                            else:
                                a+=1
                                continue
                        else:
                            a+=1
                added_edges.append((df.iat[row,subject_pos].replace(' ','\n'),df.iat[row,predicate_pos].replace('_','\n'),df.iat[row,object_pos].replace(' ','\n')))

    n = 0
    node_elements = list()
    edge_elements = list()
    for node in added_nodes.keys():
        element = {
            'data': {'id':f"n{n}", 'label':node},
            'position': {'x':n*5, 'y':0},
            #'locked': False,
            #'grabbable': True,
            #'selectable': True,
            #'selected': False,
            'classes': added_nodes[node]
        }
        if not node_elements:
            node_elements = [element]
        else:
            node_elements = node_elements + [element]
        n+=1
    e = 0
    for edge in added_edges:
        source = [x['data']['id'] for x in node_elements if x['data']['label']==edge[0]][0]
        source_name = [x['data']['label'] for x in node_elements if x['data']['id']==source][0]
        target = [x['data']['id'] for x in node_elements if x['data']['label']==edge[2]][0]
        target_name = [x['data']['label'] for x in node_elements if x['data']['id']==target][0]

        if edge_labels == True:
            label = edge[1]
            if pubmed_comentions == True:
                label = label + f" ({PubMedCoMentionsSimple(source_name,target_name,expand=True)})"
            element = {
                'data': {'source':source, 'target':target, 'label':label}
            }
        else:
            if pubmed_comentions == True:
                label = f"({PubMedCoMentionsSimple(source_name,target_name,expand=True)})"
                element = {
                    'data': {'source':source, 'target':target, 'label':label}
                }
            else:
                element = {
                    'data': {'source':source, 'target':target}
                }
        if not edge_elements:
            edge_elements = [element]
        else:
            edge_elements = edge_elements + [element]
        e+=1
    elements = node_elements + edge_elements
    cyto_elements = []
    [cyto_elements.append(x) for x in elements if x not in cyto_elements]
    stylesheet=[
                    {'selector': 'node',
                        'style': {
                            'label': 'data(label)',
                            'text-wrap':'wrap'
                        }},
                    {'selector': 'edge',
                        'style': {
                            'label': 'data(label)',
                            'curve-style': 'bezier' #segments
                        }}
                ]
    for color in nodetypecolors.keys():
        stylesheet = stylesheet + [{'selector':f".{color}", 'style': {'background-color': tuple(256*x for x in nodetypecolors[color]),'line-color': tuple(256*x for x in nodetypecolors[color])}}]
    #print(cyto_elements)
    
    
    return [cyto_elements,stylesheet]
       
    '''
    elements=[{'data': {'id': x, 'label': x},'position': {'x': 2*len(x), 'y': 2*len(x)}} for x in added_nodes]+[{'data': {'source': e[0], 'target': e[2], 'label': e[1].replace('biolink:','')}} for e in added_edges]
    print(elements)
    #Elements for Cytoscape Figure
    cytoscape_figure = cyto.Cytoscape(
        id='cytoscape-figure',
        layout={'name': 'preset'},
        style={'width': '100%', 'height': '100%'},
        elements=elements
        # [{'data': {'id': 'Metoprolol', 'label': 'Metoprolol'}, 'position': {'x': 20, 'y': 20}}, 
        # {'data': {'id': 'DNM1', 'label': 'DNM1'}, 'position': {'x': 8, 'y': 8}}, 
        # {'data': {'id': 'Alzheimer\ndisease', 'label': 'Alzheimer\ndisease'}, 'position': {'x': 34, 'y': 34}}, 
        # {'data': {'source': 'Metoprolol', 'target': 'DNM1', 'label': 'entity positively regulates entity'}}, 
        # {'data': {'source': 'DNM1', 'target': 'Alzheimer\ndisease', 'label': 'entity negatively regulates entity'}}]
    )
    '''
    '''
    G = nx.Graph()
    G.add_nodes_from(added_nodes)
    for e in added_edges:
        G.add_edge(e[0],e[2], type=e[1].replace('biolink:',''))
    edge_labels = nx.get_edge_attributes(G,'type')
    fig = plt.figure(figsize = (7,7))
    plt.margins(x=0.1,y=0.1)
    #plt.tight_layout()
    #plt.gca().set_facecolor('blue') #Background color of the whole app
    
    # pos={}  #To set nodes evenly spaced
    # x=0
    # for n in added_nodes:
    #     n_pos={n:[x,0]}
    #     pos.update(n_pos)
    #     x+=(-1*len(added_nodes))

    # pos={added_nodes[0]:[0,0]}  #To set node distance based on edge label
    # y=0
    # for n in range(len(added_edges)):
    #     y+=(-1*len(added_edges[n]))
    #     n_pos={added_nodes[n+1]:[0,y]}
    #     pos.update(n_pos)
        
    #nodecharacters=[len(x) for x in G.nodes()]
    nodesize=[300*len(x) for x in G.nodes()]
    #nodesize=400*max(nodecharacters)
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=nodesize, node_color=node_colors, font_weight='bold')
    # for p in pos:  # raise text positions
    #     t=list(pos[p])
    #     t[0]=t[0]+0.1
    #     pos[p]=tuple(t)
    
    nx.draw_networkx_edge_labels(G, pos, font_size=10, edge_labels=edge_labels,
                                #connectionstyle='arc3, rad = 0.1',
                                rotate=False,
                                #horizontalalignment='left', 
                                bbox=dict(alpha=0))
    
    #networx2cytoscape(G)
    #xy_positions = nx.nx_agraph.graphviz_layout()
    fig.set_facecolor('white')
    buf = io.BytesIO() # in-memory files
    plt.savefig(buf, format = "png") # save to the above file object
    plt.close()
    data = base64.b64encode(buf.getbuffer()).decode("utf8") # encode to html elements

    return "data:image/png;base64,{}".format(data)
    '''


def VisualizePubmedCounts(df,selected_rows,elements):
    cols = df.columns
    node_cols = []
    edge_cols = []

    for col in cols:
        if col.count('node')==1 and df.at[selected_row,col]!="?" and "protein names" not in col:
            node_cols.append(col)
        elif col.count('edge')==1 and df.at[selected_row,col]!="?":
            edge_cols.append(col)