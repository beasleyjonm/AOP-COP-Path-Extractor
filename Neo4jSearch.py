#from socket import timeout
import pandas as pd
import py2neo
import neo4j
from neo4j import unit_of_work
from matplotlib.pyplot import cm



def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct 
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return cm.get_cmap(name, n)

def processInputText(text):
    l1 = []
    for line in text.split('\n'):
        a = line
        if a != "":
            l1.append(a.strip())
    return l1

@unit_of_work(timeout=1.0)
def run_query(tx,q):
    result = tx.run(q)
    return result

KGNameIDProps = {
            "ROBOKOP":["name","id"],
            "SCENT-KOP":["name","id"],
            "HetioNet":["name","identifier"],
            "ComptoxAI":["commonName","xrefDTXSID"]
        }
#Version 2
#Uses WHERE IN [] to search for star/end nodes in a list and hopefully improve performance.
#Measured and it IS faster than Version 1.
def Graphsearch(graph_db,start_nodes,end_nodes,nodes,edges,limit_results,contains_starts=False,contains_ends=False,start_end_matching=False):
    if graph_db == "ROBOKOP":
        link = "neo4j://robokopkg.renci.org"
    elif graph_db == "HetioNet":
        link = "bolt://neo4j.het.io"
    elif graph_db == "SCENT-KOP":
        link = "bolt://scentkop.apps.renci.org"
    elif graph_db == "ComptoxAI":
        link = "bolt://neo4j.comptox.ai:7687"
    try:
        #G = py2neo.Graph(link)
        G = neo4j.GraphDatabase.driver(link)
    except:
        result=['No Results: Connection Broken']
        return (result)
    limit = str(limit_results)
    robokop_output = {}
    results = {}
    o=0
    frames=[]
    KGNameIDProps = {
            "ROBOKOP":["name","id"],
            "SCENT-KOP":["name","id"],
            "HetioNet":["name","identifier"],
            "ComptoxAI":["commonName","xrefDTXSID"]
        }
    for p in nodes:
        query = f"MATCH "
        k = len(nodes[p])
        robokop_output = {}
        
        for i in range(k):
            if i==0:
                robokop_output.update({f"node{i}:{nodes[p][i]}":[]})
                if graph_db == "ROBOKOP" or "ComptoxAI":
                    robokop_output.update({f"esnd_n{i}_r{i}":[]})
                robokop_output.update({f"edge{i}":[]})
                query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"
            elif i>0 and i<(k-1):
                robokop_output.update({f"node{i}:{nodes[p][i]}":[]})
                if graph_db == "ROBOKOP" or "ComptoxAI":
                    robokop_output.update({f"esnd_n{i}_r{i-1}":[]})
                    robokop_output.update({f"esnd_n{i}_r{i}":[]})
                robokop_output.update({f"edge{i}":[]})
                query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"
            else:
                robokop_output.update({f"node{i}:{nodes[p][i]}":[]})
                if graph_db == "ROBOKOP" or "ComptoxAI":
                    robokop_output.update({f"esnd_n{i}_r{i-1}":[]})
                query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''}) "
                
        if start_end_matching == False:
            que = query 
            if "wildcard" in start_nodes and "wildcard" in end_nodes:
                continue
            elif "wildcard" in start_nodes:
                que = que + f"WHERE n{k-1}.{KGNameIDProps[graph_db][0]} IN {str(end_nodes)} "
            elif "wildcard" in end_nodes:
                que = que + f"WHERE n{0}.{KGNameIDProps[graph_db][0]} IN {str(start_nodes)} "
            else:
                que = que + f"WHERE n{0}.{KGNameIDProps[graph_db][0]} {'CONTAINS' if contains_starts==True else 'IN'} {str(start_nodes)} AND (n{k-1}.{KGNameIDProps[graph_db][0]}) {'CONTAINS' if contains_ends==True else 'IN'} {str(end_nodes)} "
            q = que
                            
        elif start_end_matching == True:
            for start, end in zip(start_nodes, end_nodes):
                que = query
                if "wildcard" in start and "wildcard" in end:
                    que = que
                elif "wildcard" in start:
                    que = que + f"WHERE n{k-1}.{KGNameIDProps[graph_db][0]} = \"{end}\" "
                elif "wildcard" in end:
                    que = que + f"WHERE n{0}.{KGNameIDProps[graph_db][0]} = \"{start}\" "
                else:
                    que = que + f"WHERE n{0}.{KGNameIDProps[graph_db][0]} {'CONTAINS' if contains_starts==True else '='} \"{start}\" AND (n{k-1}.{KGNameIDProps[graph_db][0]}) {'CONTAINS' if contains_ends==True else '='} \"{end}\" "
                q = que
                
        if graph_db == "ROBOKOP" or "ComptoxAI":
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
                    q = q + f"n{z}.{KGNameIDProps[graph_db][0]}, esnd_n{z}_r{z}, TYPE(r{z}), "
                elif z>0 and z<(k-1):
                    q = q + f"n{z}.{KGNameIDProps[graph_db][0]}, esnd_n{z}_r{z-1}, esnd_n{z}_r{z}, TYPE(r{z}), "
                else: 
                    q = q + f"n{z}.{KGNameIDProps[graph_db][0]}, esnd_n{z}_r{z-1} LIMIT {limit}"

            #q = q + f"* LIMIT {limit}" #Working on returning ALL results.

        else:
            q = q + f"RETURN "
            for z in range(k):
                if z==0:
                    q = q + f"n{z}.{KGNameIDProps[graph_db][0]}, TYPE(r{z}), "
                elif z>0 and z<(k-1):
                    q = q + f"n{z}.{KGNameIDProps[graph_db][0]}, TYPE(r{z}), "
                else: 
                    q = q + f"n{z}.{KGNameIDProps[graph_db][0]} LIMIT {limit}"

            # q = q + f"RETURN * LIMIT {limit}" #Working on returning ALL results.
            

        print(q+"\n")
        # timeout = 1   # [seconds]

        # timeout_start = time.time()
        # t=0

        # while time.time() < timeout_start + timeout:
        #     time.sleep(0.1)
        #     session = G.session()#.data()
        #     matches = run_query(session,q)
        #     t+=1
        #     if t > 0:
        #         break

        session = G.session()#.data()
        matches = run_query(session,q)
        print(type(matches))
        # keys = list(matches[0].keys())
        # print(matches[0].keys())
        # l=0
        # for m in matches:
        #     for i in robokop_output:
        #         key=keys[l]
        #         print(key)
        #         print(list(m.keys()))
        #         robokop_output[i].append(m[l])
        #         l+=1
        #     for j in robokop_output:
        #         m[l].split(", ")
        #         robokop_output[j].append(m[l][0])
        #         l += 1
        # print("Done")
        # return "Nothing to see here!"

        for m in matches:
            l = 0
            for j in robokop_output:
                #print(m[l])
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
    elif graph_db == "ComptoxAI":
        link = "bolt://neo4j.comptox.ai:7687"
    rk_nodes=[]
    rk_edges=[]
    try:
        G = py2neo.Graph(link)
    except:
        rk_nodes=['No Available Nodes: Connection Broken']
        rk_edges=['No Available Edges: Connection Broken']
        return (rk_nodes, rk_edges)
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
    # cmap = get_cmap(len(rk_nodes))
    # print(cmap)

    return (rk_nodes, rk_edges)

def checkNodeNameID(graph_db, start_terms, end_terms, start_label, end_label):
    starts = processInputText(start_terms)
    ends = processInputText(end_terms)
    if 'biolink' in start_label:
        startLabel = f"`{start_label}`"
    else:
        startLabel = start_label
    if 'biolink' in end_label:
        endLabel = f"`{end_label}`"
    else:
        endLabel = end_label
    if graph_db == "ROBOKOP":
        link = "bolt://robokopkg.renci.org"
    elif graph_db == "HetioNet":
        link = "bolt://neo4j.het.io"
    elif graph_db == "SCENT-KOP":
        link = "bolt://scentkop.apps.renci.org"
    elif graph_db == "ComptoxAI":
        link = "bolt://neo4j.comptox.ai:7687"
    try:
        G = py2neo.Graph(link)
    except:
        start_message=['No Start Nodes: Connection Broken']
        end_message=['No End Edges: Connection Broken']
        return (start_message,end_message)
    KGNameIDProps = {
            "ROBOKOP":["name","id"],
            "SCENT-KOP":["name","id"],
            "HetioNet":["name","identifier"],
            "ComptoxAI":["commonName","xrefDTXSID"]
        }
    start_message = ""
    end_message = ""
    for term in starts:
        nodes_output = {"search term":[], "node name":[], "node id":[], "node degree":[]}
        if graph_db == "ROBOKOP" or "ComptoxAI":
            query = f"MATCH (n{':'+startLabel if startLabel != 'wildcard' else ''}) WHERE apoc.meta.type(n.{KGNameIDProps[graph_db][0]}) = 'STRING' AND toLower(n.{KGNameIDProps[graph_db][0]}) CONTAINS \"{term.lower()}\" CALL {'{'}WITH n RETURN apoc.node.degree(n) AS degree{'}'} RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}, degree"
        else:
            query = f"MATCH (n{':'+startLabel if startLabel != 'wildcard' else ''}) WHERE toLower(n.{KGNameIDProps[graph_db][0]}) CONTAINS \"{term.lower()}\" RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}"
        matches = G.run(query)
        for m in matches:
            nodes_output["search term"].append(term)
            nodes_output["node name"].append(m[0])
            nodes_output["node id"].append(m[1])
            try:
                nodes_output["node degree"].append(m[2])
            except:
                continue
        b=len(nodes_output['node name'])
        if term in nodes_output["node name"]:
            if graph_db == "ROBOKOP" or "ComptoxAI":
                start_message+=f"'{term}' found! ID: {nodes_output['node id'][0]}, Degree: {nodes_output['node degree'][0]}\n"
            else:
                start_message+=f"'{term}' found! ID: {nodes_output['node id'][0]}\n"
        else:
            if graph_db == "ROBOKOP" or "ComptoxAI":
                start_message+=f"'{term}' not in {graph_db} under '{start_label}' category, try instead {str([str(x)+'('+str(y)+')' for x,y in zip(nodes_output['node name'],nodes_output['node degree'])])}\n"
            else:
                start_message+=f"'{term}' not in {graph_db} under '{start_label}' category, try instead {str([str(x) for x in nodes_output['node name']])}\n"
    for term in ends:
        nodes_output = {"search term":[], "node name":[], "node id":[], "node degree":[]}
        a=len(nodes_output['node name'])
        if graph_db == "ROBOKOP" or "ComptoxAI":
            query = f"MATCH (n{':'+endLabel if endLabel != 'wildcard' else ''}) WHERE apoc.meta.type(n.{KGNameIDProps[graph_db][0]}) = 'STRING' AND toLower(n.{KGNameIDProps[graph_db][0]}) CONTAINS \"{term.lower()}\" CALL {'{'}WITH n RETURN apoc.node.degree(n) AS degree{'}'} RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}, degree"
        else:
            query = f"MATCH (n{':'+endLabel if endLabel != 'wildcard' else ''}) WHERE toLower(n.{KGNameIDProps[graph_db][0]}) CONTAINS \"{term.lower()}\" RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}"
        matches = G.run(query)
        for m in matches:
            nodes_output["search term"].append(term)
            nodes_output["node name"].append(m[0])
            nodes_output["node id"].append(m[1])
            try:
                nodes_output["node degree"].append(m[2])
            except:
                continue
        b=len(nodes_output['node name'])
        if term in nodes_output["node name"]:
            if graph_db == "ROBOKOP":
                end_message+=f"'{term}' found! ID: {nodes_output['node id'][0]}, Degree: {nodes_output['node degree'][0]}\n"
            else:
                end_message+=f"'{term}' found! ID: {nodes_output['node id'][0]}\n"
        else:
            if graph_db == "ROBOKOP":
                end_message+=f"'{term}' not in {graph_db} under '{end_label}' category, try instead {str([str(x)+'('+str(y)+')' for x,y in zip(nodes_output['node name'],nodes_output['node degree'])])}\n"             
            else:
                end_message+=f"'{term}' not in {graph_db} under '{end_label}' category, try instead {str([str(x) for x in nodes_output['node name']])}\n"
        
    return start_message,end_message