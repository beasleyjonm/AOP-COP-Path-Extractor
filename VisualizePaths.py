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
    for col in cols:
        if col.count('node')==1 and df.at[selected_row,col]!="?" and "protein names" not in col:
            node_cols.append(col)
        elif col.count('edge')==1 and df.at[selected_row,col]!="?":
            edge_cols.append(col)
    human_sort(node_cols)
    human_sort(edge_cols)
    print(node_cols)
    print(edge_cols)
    added_nodes = []
    added_edges = []
    for col in node_cols:
        added_nodes.append(df.at[selected_row,col])
    for col in edge_cols:
        added_edges.append(df.at[selected_row,col])

    G = nx.Graph()
    G.add_nodes_from(added_nodes)
    for i in range(len(added_edges)):
        G.add_edge(added_nodes[i],added_nodes[i+1], type=added_edges[i].replace('biolink:',''))
    edge_labels = nx.get_edge_attributes(G,'type')
    plt.figure(figsize = (2,8))
    pos={}
    y=0
    for n in added_nodes:
        n_pos={n:[0,y]}
        pos.update(n_pos)
        y+=(-2)
    #pos = nx.spectral_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=1000, font_weight='bold')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    # ax = fig.add_subplot(1,1,1) 
    # ax.set_xlabel(f"Principal Component 1; Variance:{expVariance[0]}", fontsize = 15)
    # ax.set_ylabel(f"Principal Component 2; Variance:{expVariance[1]}", fontsize = 15)
    # ax.set_title('2 component PCA', fontsize = 20)
    # targets = [x for x in pcaData['target']]
    # colors = cm.rainbow(np.linspace(0, 1, len(targets)))
    # for target, color in zip(targets,colors):
    #     indicesToKeep = pcaData['target'] == target
    #     ax.scatter(pcaData.loc[indicesToKeep, 'principal component 1']
    #             , pcaData.loc[indicesToKeep, 'principal component 2']
    #             , color = color
    #             , s = 50)
    #     if use_labels==True:
    #         plt.text(pcaData.loc[indicesToKeep, 'principal component 1']
    #                 , pcaData.loc[indicesToKeep, 'principal component 2']
    #                 , target
    #                 , fontsize=10)
    # ax.legend(targets)#, loc='center left', bbox_to_anchor=(1, 0.5))
    # ax.grid()
    
    buf = io.BytesIO() # in-memory files
    
    plt.savefig(buf, format = "png") # save to the above file object
    plt.close()
    data = base64.b64encode(buf.getbuffer()).decode("utf8") # encode to html elements

    return "data:image/png;base64,{}".format(data)