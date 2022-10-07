import pandas as pd
import networkx as nx
import re
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import io
import base64
from Neo4jSearch import GenerateNodeColors
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
    

def VisualizeAnswerRow(df,selected_rows):
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
    nodetypecolors = GenerateNodeColors([x[7:].replace('`','').replace('biolink:','') for x in node_cols])
    added_nodes = []
    node_colors = []
    added_edges = []
    for row in selected_rows:
        for col in node_cols:
            if df.at[row,col] != "?":
                if df.at[row,col].replace(' ','\n') in added_nodes:
                    continue
                else:
                    added_nodes.append(df.at[row,col].replace(' ','\n'))
                    node_colors.append(nodetypecolors[col[7:].replace('`','').replace('biolink:','')])

        for i in range(len(searched_cols)):

            if 'edge' in searched_cols[i]:
                predicate_pos = cols.get_loc(searched_cols[i])
                if df.iat[row,predicate_pos] == "?":
                    continue   

                subject_pos = cols.get_loc(searched_cols[i-1])

                object_pos = cols.get_loc(searched_cols[i+1])
                if df.iat[row,object_pos] == "?":
                    a = 1
                    while df.iat[row,object_pos] == "?":
                        object_pos = cols.get_loc(searched_cols[i+1+a])
                        a+=1

                added_edges.append((df.iat[row,subject_pos].replace(' ','\n'),df.iat[row,predicate_pos].replace('_','\n'),df.iat[row,object_pos].replace(' ','\n')))
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
    '''
    nx.draw_networkx_edge_labels(G, pos, font_size=10, edge_labels=edge_labels,
                                #connectionstyle='arc3, rad = 0.1',
                                rotate=False,
                                #horizontalalignment='left', 
                                bbox=dict(alpha=0))
    '''
    #networx2cytoscape(G)
    #xy_positions = nx.nx_agraph.graphviz_layout()
    fig.set_facecolor('white')
    buf = io.BytesIO() # in-memory files
    plt.savefig(buf, format = "png") # save to the above file object
    plt.close()
    data = base64.b64encode(buf.getbuffer()).decode("utf8") # encode to html elements

    return "data:image/png;base64,{}".format(data)

def VisualizePubmedCounts(df,selected_row,count_cols):
    cols = df.columns
    node_cols = []
    edge_cols = []

    for col in cols:
        if col.count('node')==1 and df.at[selected_row,col]!="?" and "protein names" not in col:
            node_cols.append(col)
        elif col.count('edge')==1 and df.at[selected_row,col]!="?":
            edge_cols.append(col)