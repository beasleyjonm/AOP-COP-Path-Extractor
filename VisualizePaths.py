import pandas as pd
import networkx as nx
import re
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import io
import base64

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

def VisualizeAnswerRow(df,selected_row):
    cols = df.columns
    node_cols = []
    edge_cols = []
    count_cols = [x for x in cols if " counts" in x]
    for col in cols:
        if col.count('node')==1 and df.at[selected_row,col]!="?":
            if "protein names" not in col:
                node_cols.append(col)
        elif col.count('edge')==1 and df.at[selected_row,col]!="?":
            edge_cols.append(col)
    human_sort(node_cols)
    human_sort(edge_cols)
    print(node_cols)
    print(edge_cols)
    print(count_cols)
    added_nodes = []
    added_edges = []
    for col in node_cols:
        added_nodes.append(df.at[selected_row,col].replace(' ','\n'))
    for col in edge_cols:
        added_edges.append(df.at[selected_row,col].replace('_','\n'))

    G = nx.Graph()
    G.add_nodes_from(added_nodes)
    for i in range(len(added_edges)):
        G.add_edge(added_nodes[i],added_nodes[i+1], type=added_edges[i].replace('biolink:',''))
    edge_labels = nx.get_edge_attributes(G,'type')
    fig = plt.figure(figsize = (5,8))
    #plt.gca().set_facecolor('blue') #Background color of the whole app
    
    pos={}  #To set nodes evenly spaced
    y=0
    for n in added_nodes:
        n_pos={n:[0,y]}
        pos.update(n_pos)
        y+=(-1*len(added_nodes))

    # pos={added_nodes[0]:[0,0]}  #To set node distance based on edge label
    # y=0
    # for n in range(len(added_edges)):
    #     y+=(-1*len(added_edges[n]))
    #     n_pos={added_nodes[n+1]:[0,y]}
    #     pos.update(n_pos)
        
    #nodecharacters=[len(x) for x in G.nodes()]
    nodesize=[300*len(x) for x in G.nodes()]
    #nodesize=400*max(nodecharacters)
    
    nx.draw(G, pos, with_labels=True, node_size=nodesize, font_weight='bold')
    # for p in pos:  # raise text positions
    #     t=list(pos[p])
    #     t[0]=t[0]+0.1
    #     pos[p]=tuple(t)

    nx.draw_networkx_edge_labels(G, pos, font_size=10, edge_labels=edge_labels,
                                rotate=False,
                                horizontalalignment='left', 
                                bbox=dict(alpha=0))
    fig.set_facecolor('#7794B8')
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