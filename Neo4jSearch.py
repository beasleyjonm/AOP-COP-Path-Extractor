import pandas as pd
import py2neo

def processInputText(text):
    l1 = []
    for line in text.split('\n'):
        a = line
        if a != "":
            l1.append(a.strip())
    return l1

#Version 2
#Uses WHERE IN [] to search for star/end nodes in a list and hopefully improve performance.
#Measured and it IS faster than Version 1.
def Graphsearch(graph_db,start_nodes,end_nodes,nodes,edges,limit_results,contains_starts=False,contains_ends=False,start_end_matching=False):
    if graph_db == "ROBOKOP":
        link = "bolt://robokopkg.renci.org"
    elif graph_db == "HetioNet":
        link = "bolt://neo4j.het.io"
    elif graph_db == "SCENT-KOP":
        link = "bolt://scentkop.apps.renci.org"
    G = py2neo.Graph(link)
    limit = str(limit_results)
    robokop_output = {}
    results = {}
    o=0
    frames=[]

    for p in nodes:
        query = f"MATCH "
        k = len(nodes[p])
        robokop_output = {}
        
        for i in range(k):
            if i==0:
                robokop_output.update({f"node{i}:{nodes[p][i]}":[]})
                if graph_db == "ROBOKOP":
                    robokop_output.update({f"esnd_n{i}_r{i}":[]})
                robokop_output.update({f"edge{i}":[]})
                query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"
            elif i>0 and i<(k-1):
                robokop_output.update({f"node{i}:{nodes[p][i]}":[]})
                if graph_db == "ROBOKOP":
                    robokop_output.update({f"esnd_n{i}_r{i-1}":[]})
                    robokop_output.update({f"esnd_n{i}_r{i}":[]})
                robokop_output.update({f"edge{i}":[]})
                query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"
            else:
                robokop_output.update({f"node{i}:{nodes[p][i]}":[]})
                if graph_db == "ROBOKOP":
                    robokop_output.update({f"esnd_n{i}_r{i-1}":[]})
                query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''}) "
                
        if start_end_matching == False:
            que = query 
            if "wildcard" in start_nodes and "wildcard" in end_nodes:
                continue
            elif "wildcard" in start_nodes:
                que = que + f"WHERE n{k-1}.name IN {str(end_nodes)} "
            elif "wildcard" in end_nodes:
                que = que + f"WHERE n{0}.name IN {str(start_nodes)} "
            else:
                que = que + f"WHERE n{0}.name {'CONTAINS' if contains_starts==True else 'IN'} {str(start_nodes)} AND (n{k-1}.name) {'CONTAINS' if contains_ends==True else 'IN'} {str(end_nodes)} "
            q = que
                            
        elif start_end_matching == True:
            for start, end in zip(start_nodes, end_nodes):
                que = query
                if "wildcard" in start and "wildcard" in end:
                    que = que
                elif "wildcard" in start:
                    que = que + f"WHERE n{k-1}.name = \"{end}\" "
                elif "wildcard" in end:
                    que = que + f"WHERE n{0}.name = \"{start}\" "
                else:
                    que = que + f"WHERE n{0}.name {'CONTAINS' if contains_starts==True else '='} \"{start}\" AND (n{k-1}.name) {'CONTAINS' if contains_ends==True else '='} \"{end}\" "
                q = que
                
        if graph_db == "ROBOKOP":
            for i in range(k):
                firstbracket = "{"
                secondbracket = "}"
                firstmark = f"'`'+"
                secondmark = f"+'`'"
                if i==0:
                    q = q + f"CALL{firstbracket}WITH n{i}, r{i} MATCH(n{i})-[r{i}]-(t) RETURN apoc.node.degree(n{i}, {firstmark if graph_db == 'ROBOKOP' else ''}TYPE(r{i}){secondmark if graph_db == 'ROBOKOP' else ''}) AS esnd_n{i}_r{i}{secondbracket} "
                elif i>0 and i<(k-1):
                    q = q + f"CALL{firstbracket}WITH n{i}, r{i-1} MATCH(n{i})-[r{i-1}]-(t) RETURN apoc.node.degree(n{i}, {firstmark if graph_db == 'ROBOKOP' else ''}TYPE(r{i-1}){secondmark if graph_db == 'ROBOKOP' else ''}) AS esnd_n{i}_r{i-1}{secondbracket} CALL{firstbracket}WITH n{i}, r{i} MATCH(n{i})-[r{i}]-(t) RETURN apoc.node.degree(n{i}, {firstmark if graph_db == 'ROBOKOP' else ''}TYPE(r{i}){secondmark if graph_db == 'ROBOKOP' else ''}) AS esnd_n{i}_r{i}{secondbracket} "
                else:
                    q = q + f"CALL{firstbracket}WITH n{i}, r{i-1} MATCH(n{i})-[r{i-1}]-(t) RETURN apoc.node.degree(n{i}, {firstmark if graph_db == 'ROBOKOP' else ''}TYPE(r{i-1}){secondmark if graph_db == 'ROBOKOP' else ''}) AS esnd_n{i}_r{i-1}{secondbracket} RETURN "
            
            for z in range(k):
                if z==0:
                    q = q + f"n{z}.name, esnd_n{z}_r{z}, TYPE(r{z}), "
                elif z>0 and z<(k-1):
                    q = q + f"n{z}.name, esnd_n{z}_r{z-1}, esnd_n{z}_r{z}, TYPE(r{z}), "
                else: 
                    q = q + f"n{z}.name, esnd_n{z}_r{z-1} LIMIT {limit}"

        else:
            q = q + f"RETURN "
            for z in range(k):
                if z==0:
                    q = q + f"n{z}.name, TYPE(r{z}), "
                elif z>0 and z<(k-1):
                    q = q + f"n{z}.name, TYPE(r{z}), "
                else: 
                    q = q + f"n{z}.name LIMIT {limit}"

        print(q+"\n")

        matches = G.run(q)
        for m in matches:
            l = 0
            for j in robokop_output:
                robokop_output[j].append(m[l])
                l += 1

        robokop_output.update({"path":p})
        frames.append(pd.DataFrame(data=robokop_output))
        
    result = pd.concat(frames, ignore_index=True, sort=False)
    result.fillna("?",inplace=True)
    path_column = result.pop('path')
    result.insert(0, 'path', path_column)

    return result

def getNodeAndEdgeLabels(graph_db):
    if graph_db == "ROBOKOP":
        link = "bolt://robokopkg.renci.org"
    elif graph_db == "HetioNet":
        link = "bolt://neo4j.het.io"
    elif graph_db == "SCENT-KOP":
        link = "bolt://scentkop.apps.renci.org"
    G = py2neo.Graph(link)
    rk_nodes=[]
    rk_edges=[]
    query_1 = f"call db.labels"
    matches_1 = G.run(query_1)
    for m in matches_1:
        rk_nodes.append(m[0])
    query_2 = f"call db.relationshipTypes"
    matches_2 = G.run(query_2)
    for m in matches_2:
        rk_edges.append(m[0])
    rk_nodes.sort()
    rk_edges.sort()
    return (rk_nodes, rk_edges)