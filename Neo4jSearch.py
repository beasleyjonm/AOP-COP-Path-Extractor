#from socket import timeout
import pandas as pd
import py2neo
import neo4j
#from neo4j import unit_of_work
from matplotlib.pyplot import cm
#import re
from distinctipy import distinctipy

def GenerateNodeColors(list_to_color):

    # number of colours to generate
    N = len(list_to_color)

    # generate N visually distinct colours
    colors = distinctipy.get_colors(N)

    color_map = dict()
    i=0
    for item in list_to_color:
        color_map.update({item:colors[i]})
        i+=1
    
    return color_map

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

#@unit_of_work(timeout=1.0)
def run_query(tx,q):
    result = tx.run(q)
    return result

# KGNamesIDProps specififies the keys to properties specific to KGs. The order of terms should be: node names, node primary identifiers, node alternate identifiers, predicate.
# The order of keys should be: node names, node primary identifiers, node alternate identifiers, predicate.
# If nodes have no equivalent identifiers in a KG, make primary and equivalent id keys the same.
KGNameIDProps = {
            "ROBOKOP":["name","id","equivalent_identifiers","predicate"],
            "SCENT-KOP":["name","id","id","predicate"],
            "HetioNet":["name","identifier","identifier","predicate"],
            "ComptoxAI":["commonName","uri","uri","predicate"]
        }
#Version 2
#Uses WHERE IN [] to search for star/end nodes in a list and hopefully improve performance.
#Measured and it IS faster than Version 1.
def Graphsearch(graph_db,start_nodes,end_nodes,nodes,options,edges,get_metadata,timeout_ms,limit_results,contains_starts=False,contains_ends=False,start_end_matching=False):
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
    #neo4j_query = "MATCH "
    #display_where_options = "WHERE "
    #p_num = 0
    robokop_output = {}

    frames=[]
    
    #start_nodes = "["+",".join(f'"{x}"' for x in start_nodes)+"]"
    #end_nodes = "["+",".join(f'"{x}"' for x in end_nodes)+"]"
    print(options)

    for p in nodes:
        query = f"MATCH "
        #display_query = ""
        k = len(nodes[p])
        robokop_output = {}
        where_options = "WHERE "
        for i in range(k):
            if i==0:
                robokop_output.update({f"node{i}: {nodes[p][i]}":[]})
                if get_metadata == True:
                    robokop_output.update({f"n{i}:MetaData":[]})
                if graph_db == "ROBOKOP" or graph_db == "ComptoxAI":
                    robokop_output.update({f"esnd_n{i}_r{i}":[]})
                robokop_output.update({f"edge{i}":[]})
                if get_metadata == True:
                    if graph_db == "ROBOKOP":
                        robokop_output.update({f"e{i}:MetaData":[]})
                query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"
        #        display_query = display_query + f"(n{i}_{p_num}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}_{p_num}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"

            elif i>0 and i<(k-1):
                robokop_output.update({f"node{i}: {nodes[p][i]}":[]})
                if get_metadata == True:
                    robokop_output.update({f"n{i}:MetaData":[]})
                if graph_db == "ROBOKOP" or graph_db == "ComptoxAI":
                    robokop_output.update({f"esnd_n{i}_r{i-1}":[]})
                    robokop_output.update({f"esnd_n{i}_r{i}":[]})
                robokop_output.update({f"edge{i}":[]})
                if get_metadata == True:
                    if graph_db == "ROBOKOP":
                        robokop_output.update({f"e{i}:MetaData":[]})
                query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"
        #        display_query = display_query + f"(n{i}_{p_num}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}_{p_num}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"

                if options[p][i-1] != "wildcard":
                    if ":" in options[p][i-1]:
                        where_options = where_options + f"any(x IN {str(processInputText(options[p][i-1]))} WHERE x IN n{i}.{KGNameIDProps[graph_db][0]} OR x IN n{i}.{KGNameIDProps[graph_db][2]}) AND "
        #                display_where_options = display_where_options + f"any(x IN {str(processInputText(options[p][i-1]))} WHERE x IN n{i}_{p_num}.{KGNameIDProps[graph_db][0]} OR x IN n{i}_{p_num}.{KGNameIDProps[graph_db][2]}) AND "
                    else:
                        where_options = where_options + f"n{i}.{KGNameIDProps[graph_db][0]} IN {str(processInputText(options[p][i-1]))} AND "
        #                display_where_options = display_where_options + f"n{i}_{p_num}.{KGNameIDProps[graph_db][0]} IN {str(processInputText(options[p][i-1]))} AND "
            else:
                robokop_output.update({f"node{i}: {nodes[p][i]}":[]})
                if get_metadata == True:
                    robokop_output.update({f"n{i:}MetaData":[]})
                if graph_db == "ROBOKOP" or graph_db == "ComptoxAI":
                    robokop_output.update({f"esnd_n{i}_r{i-1}":[]})
                query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''}) "
         #       display_query = display_query + f"(n{i}_{p_num}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})"
        if len(where_options)>6:
            query = query + where_options

        if start_end_matching == False:
            que = query 
            if "wildcard" in start_nodes and "wildcard" in end_nodes:
                continue
            elif "wildcard" in start_nodes:
                if ":" in str(end_nodes):
                    que = que + f"{'WHERE' if len(where_options)<=6 else ''} any(x IN {str(end_nodes)} WHERE x IN n{k-1}.{KGNameIDProps[graph_db][0]} OR x IN n{k-1}.{KGNameIDProps[graph_db][2]}) "
            #        display_where_options = display_where_options + f"any(x IN {str(end_nodes)} WHERE x IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} OR x IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]}) "
                else:
                    que = que + f"{'WHERE' if len(where_options)<=6 else ''} n{k-1}.{KGNameIDProps[graph_db][0]} IN {str(end_nodes)} "
            #        display_where_options = display_where_options + f"n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} IN {str(end_nodes)} "
                    

            elif "wildcard" in end_nodes:
                if ":" in str(start_nodes):
                    que = que + f"{'WHERE' if len(where_options)<=6 else ''} any(x IN {str(start_nodes)} WHERE x IN n{0}.{KGNameIDProps[graph_db][0]} OR x IN n{0}.{KGNameIDProps[graph_db][2]}) "
            #        display_query = display_query + f"any(x IN {str(start_nodes)} WHERE x IN n{0}_{p_num}.{KGNameIDProps[graph_db][0]} OR x IN n{0}_{p_num}.{KGNameIDProps[graph_db][2]}) "
                que = que + f"{'WHERE' if len(where_options)<=6 else ''} n{0}.{KGNameIDProps[graph_db][0]} IN {str(start_nodes)} "
            #    display_where_options = display_where_options + f"n{0}_{p_num}.{KGNameIDProps[graph_db][0]} IN {str(start_nodes)} "
                

            else:
                if ":" in str(start_nodes)+str(end_nodes):
                    que = que + f"{'WHERE' if len(where_options)<=6 else ''} any(x IN {str(start_nodes)} WHERE x IN n{0}.{KGNameIDProps[graph_db][0]} OR x IN n{0}.{KGNameIDProps[graph_db][2]}) AND any(x IN {str(end_nodes)} WHERE x IN n{k-1}.{KGNameIDProps[graph_db][0]} OR x IN n{k-1}.{KGNameIDProps[graph_db][2]}) "
            #        display_where_options = display_where_options + f"any(x IN {str(start_nodes)} WHERE x IN n{0}_{p_num}.{KGNameIDProps[graph_db][0]} OR x IN n{0}_{p_num}.{KGNameIDProps[graph_db][2]}) AND any(x IN {str(end_nodes)} WHERE x IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} OR x IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]}) "
                    
                else:
                    que = que + f"{'WHERE' if len(where_options)<=6 else ''} n{0}.{KGNameIDProps[graph_db][0]} IN {str(start_nodes)} AND n{k-1}.{KGNameIDProps[graph_db][0]} IN {str(end_nodes)} "
            #        display_where_options = display_where_options + f"n{0}_{p_num}.{KGNameIDProps[graph_db][0]} IN {str(start_nodes)} AND n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} IN {str(end_nodes)} "
                    
            q = que
            #if p_num < len(nodes)-1:
            #    display_where_options = display_where_options + "AND "
                                 
        elif start_end_matching == True:
            for start, end in zip(start_nodes, end_nodes):
                que = query
                if "wildcard" in start and "wildcard" in end:
                    que = que
                elif "wildcard" in start:
                    que = que + f"{'WHERE' if len(where_options)<=6 else ''} n{k-1}.{KGNameIDProps[graph_db][0]} = \"{end}\" "
                elif "wildcard" in end:
                    que = que + f"{'WHERE' if len(where_options)<=6 else ''} n{0}.{KGNameIDProps[graph_db][0]} = \"{start}\" "
                else:
                    que = que + f"{'WHERE' if len(where_options)<=6 else ''} n{0}.{KGNameIDProps[graph_db][0]} {'CONTAINS' if contains_starts==True else '='} \"{start}\" AND (n{k-1}.{KGNameIDProps[graph_db][0]}) {'CONTAINS' if contains_ends==True else '='} \"{end}\" "
                q = que
                
        if graph_db == "ROBOKOP" or graph_db == "ComptoxAI":
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
            
            if get_metadata == True:
                for z in range(k):
                    if z==0:
                        q = q + f"properties(n{z}) as n{z}, esnd_n{z}_r{z}, {'properties(r'+str(z)+') as r'+str(z) if graph_db == 'ROBOKOP' else 'TYPE(r'+str(z)+') as r'+str(z)}, "
                    elif z>0 and z<(k-1):
                        q = q + f"properties(n{z}) as n{z}, esnd_n{z}_r{z-1}, esnd_n{z}_r{z}, {'properties(r'+str(z)+') as r'+str(z) if graph_db == 'ROBOKOP' else 'TYPE(r'+str(z)+') as r'+str(z)}, "
                    else: 
                        q = q + f"properties(n{z}) as n{z}, esnd_n{z}_r{z-1} LIMIT {limit}"
            else:
                for z in range(k):
                    if z==0:
                        q = q + f"n{z}.{KGNameIDProps[graph_db][0]} as n{z}, esnd_n{z}_r{z}, TYPE(r{z}) as r{z}, "
                    elif z>0 and z<(k-1):
                        q = q + f"n{z}.{KGNameIDProps[graph_db][0]} as n{z}, esnd_n{z}_r{z-1}, esnd_n{z}_r{z}, TYPE(r{z}) as r{z}, "
                    else: 
                        q = q + f"n{z}.{KGNameIDProps[graph_db][0]} as n{z}, esnd_n{z}_r{z-1} LIMIT {limit}"

        else:
            q = q + f"RETURN "
            for z in range(k):
                if z==0:
                    q = q + f"n{z}.{KGNameIDProps[graph_db][0]}, TYPE(r{z}), "
                elif z>0 and z<(k-1):
                    q = q + f"n{z}.{KGNameIDProps[graph_db][0]}, TYPE(r{z}), "
                else: 
                    q = q + f"n{z}.{KGNameIDProps[graph_db][0]} LIMIT {limit}"
        print(q+"\n")
        
        if get_metadata == True:
            if graph_db == "ROBOKOP" or graph_db == "ComptoxAI":
                q = f"CALL apoc.cypher.runTimeboxed(\"{q}\",null,{timeout_ms}) YIELD value RETURN "
                for z in range(k):
                    if z==0:
                        q = q + f"value.n{z}.{KGNameIDProps[graph_db][0]}, value.n{z}, value.esnd_n{z}_r{z},{ 'value.r'+str(z)+'.predicate,' if graph_db == 'ROBOKOP' else ''} value.r{z}, "
                    elif z>0 and z<(k-1):
                        q = q + f"value.n{z}.{KGNameIDProps[graph_db][0]}, value.n{z}, value.esnd_n{z}_r{z-1}, value.esnd_n{z}_r{z},{ 'value.r'+str(z)+'.predicate,' if graph_db == 'ROBOKOP' else ''} value.r{z}, "
                    else: 
                        q = q + f"value.n{z}.{KGNameIDProps[graph_db][0]}, value.n{z}, value.esnd_n{z}_r{z-1}"
            print(q+"\n")

        else:
            if graph_db == "ROBOKOP" or graph_db == "ComptoxAI":
                q = f"CALL apoc.cypher.runTimeboxed(\"{q}\",null,{timeout_ms}) YIELD value RETURN "
                for z in range(k):
                    if z==0:
                        q = q + f"value.n{z}, value.esnd_n{z}_r{z}, value.r{z}, "
                    elif z>0 and z<(k-1):
                        q = q + f"value.n{z}, value.esnd_n{z}_r{z-1}, value.esnd_n{z}_r{z}, value.r{z}, "
                    else: 
                        q = q + f"value.n{z}, value.esnd_n{z}_r{z-1}"
            print(q+"\n")

        #print(display_query)
        #neo4j_query = f"{neo4j_query}{display_query}{' ' if p_num == (len(nodes)-1) else ', '}"
        #p_num += 1
        session = G.session()#.data()
        matches = run_query(session,q)
        print(type(matches))
        
        for m in matches:
            l = 0
            for j in robokop_output:
                #print(type(m[l]))
                if 'MetaData' in j:
                    robokop_output[j].append(str(m[l]).replace("{","").replace("}","").replace("'","") if isinstance(m[l], dict) else m[l])
                else:
                    robokop_output[j].append(str(m[l]).replace('biolink:','').replace('_',' ') if isinstance(m[l], str) else m[l])

                l += 1

        robokop_output.update({"path":p})
        frames.append(pd.DataFrame(data=robokop_output))
    #neo4j_query = neo4j_query + display_where_options + f"RETURN * LIMIT {100}"
    #print(neo4j_query)
    result = pd.concat(frames, ignore_index=True, sort=False)
    result.fillna("?",inplace=True)
    path_column = result.pop('path')
    result.insert(0, 'path', path_column)

    return result

#Function to supply Neo4j display query for all query patterns
def DisplayQuery(graph_db,start_nodes,end_nodes,nodes,options,edges,limit_results,start_end_matching=False):
    
    neo4j_query = "MATCH "
    display_where_options = "WHERE "
    p_num = 0
   
    for p in nodes:
        display_query = ""
        k = len(nodes[p])
        for i in range(k):
            if i==0:
                display_query = display_query + f"(n{i}_{p_num}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}_{p_num}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"

            elif i>0 and i<(k-1):
                display_query = display_query + f"(n{i}_{p_num}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}_{p_num}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"

                if options[p][i-1] != "wildcard":
                    if ":" in options[p][i-1]:
                        display_where_options = display_where_options + f"any(x IN {str(processInputText(options[p][i-1]))} WHERE x IN n{i}_{p_num}.{KGNameIDProps[graph_db][0]} OR x IN n{i}_{p_num}.{KGNameIDProps[graph_db][2]}) AND "
                    else:
                        display_where_options = display_where_options + f"n{i}_{p_num}.{KGNameIDProps[graph_db][0]} IN {str(processInputText(options[p][i-1]))} AND "
            else:
                display_query = display_query + f"(n{i}_{p_num}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})"

        if start_end_matching == False:
            if "wildcard" in start_nodes and "wildcard" in end_nodes:
                continue
            elif "wildcard" in start_nodes:
                if ":" in str(end_nodes):
                    display_where_options = display_where_options + f"any(x IN {str(end_nodes)} WHERE x IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} OR x IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]}) "
                else:
                    display_where_options = display_where_options + f"n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} IN {str(end_nodes)} "
                    
            elif "wildcard" in end_nodes:
                if ":" in str(start_nodes):
                    display_query = display_query + f"any(x IN {str(start_nodes)} WHERE x IN n{0}_{p_num}.{KGNameIDProps[graph_db][0]} OR x IN n{0}_{p_num}.{KGNameIDProps[graph_db][2]}) "
                display_where_options = display_where_options + f"n{0}_{p_num}.{KGNameIDProps[graph_db][0]} IN {str(start_nodes)} "
                
            else:
                if ":" in str(start_nodes)+str(end_nodes):
                    display_where_options = display_where_options + f"any(x IN {str(start_nodes)} WHERE x IN n{0}_{p_num}.{KGNameIDProps[graph_db][0]} OR x IN n{0}_{p_num}.{KGNameIDProps[graph_db][2]}) AND any(x IN {str(end_nodes)} WHERE x IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} OR x IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]}) "     
                else:
                    display_where_options = display_where_options + f"n{0}_{p_num}.{KGNameIDProps[graph_db][0]} IN {str(start_nodes)} AND n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} IN {str(end_nodes)} "
            
            if p_num < len(nodes)-1:
                display_where_options = display_where_options + "AND "
                                           
        print(display_query)
        neo4j_query = f"{neo4j_query}{display_query}{' ' if p_num == (len(nodes)-1) else ', '}"
        p_num += 1

    neo4j_query = neo4j_query + display_where_options + f"RETURN * LIMIT {limit_results}"
    print(neo4j_query)
    
    return neo4j_query

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
    #cmap = GenerateNodeColors(rk_nodes)

    return (rk_nodes, rk_edges)

def checkNodeNameID(graph_db, terms, label):
    terms = processInputText(terms)
    #ends = processInputText(end_terms)
    if 'biolink' in label:
        Label = f"`{label}`"
    else:
        Label = label
    # if 'biolink' in end_label:
    #     endLabel = f"`{end_label}`"
    # else:
    #     endLabel = end_label
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
        message=['No Nodes Found: Connection Broken']
        #end_message=['No End Edges: Connection Broken']
        return (message)
   
    message = ""
    '''
    #end_message = ""
    # for term in terms:
    #     nodes_output = {"search term":[], "node name":[], "node id":[], "node degree":[]}
    #     if graph_db == "ROBOKOP" or "ComptoxAI":
    #         query = f"MATCH (n{':'+Label if Label != 'wildcard' else ''}) WHERE apoc.meta.type(n.{KGNameIDProps[graph_db][0]}) = 'STRING' AND toLower(n.{KGNameIDProps[graph_db][0]}) CONTAINS \"{term.lower()}\" CALL {'{'}WITH n RETURN apoc.node.degree(n) AS degree{'}'} RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}, degree"
    #     else:
    #         query = f"MATCH (n{':'+Label if Label != 'wildcard' else ''}) WHERE toLower(n.{KGNameIDProps[graph_db][0]}) CONTAINS \"{term.lower()}\" RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}"
    #     matches = G.run(query)
    #     for m in matches:
    #         nodes_output["search term"].append(term)
    #         nodes_output["node name"].append(m[0])
    #         nodes_output["node id"].append(m[1])
    #         try:
    #             nodes_output["node degree"].append(m[2])
    #         except:
    #             continue
    '''
    nodes_output = {"node name":[], "node id":[], "node eq id":[], "node degree":[]}
    
    searched_list = ",".join(f'"{x.lower()}"' for x in terms)
    
    if graph_db == "ROBOKOP" or graph_db == "ComptoxAI":
        query = f"WITH [{searched_list}] as terms MATCH (n{':'+ Label if Label != 'wildcard' else ''}) WHERE apoc.meta.type(n.{KGNameIDProps[graph_db][0]}) = 'STRING' AND any(term IN terms WHERE toLower(n.{KGNameIDProps[graph_db][0]}) CONTAINS term OR toLower(apoc.text.join(n.{KGNameIDProps[graph_db][2]}, ',')) CONTAINS term) CALL {'{'}WITH n RETURN apoc.node.degree(n) AS degree{'}'} RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}, n.{KGNameIDProps[graph_db][2]}, degree LIMIT 10000"
    else:
        query = f"MATCH (n{':'+Label if Label != 'wildcard' else ''}) WHERE toLower(n.{KGNameIDProps[graph_db][0]}) IN [{searched_list}] OR toLower(apoc.text.join(n.{KGNameIDProps[graph_db][2]}, ',')) IN [{searched_list}] RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}, n.{KGNameIDProps[graph_db][2]} LIMIT 10000"
    
    # for term in starts:
    #     nodes_output = {"search term":[], "node name":[], "node id":[], "node degree":[]}
    #     if graph_db == "ROBOKOP" or "ComptoxAI":
    #         query = f"MATCH (n{':'+startLabel if startLabel != 'wildcard' else ''}) WHERE apoc.meta.type(n.{KGNameIDProps[graph_db][0]}) = 'STRING' AND toLower(n.{KGNameIDProps[graph_db][0]}) CONTAINS \"{term.lower()}\" CALL {'{'}WITH n RETURN apoc.node.degree(n) AS degree{'}'} RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}, degree"
    #     else:
    #         query = f"MATCH (n{':'+startLabel if startLabel != 'wildcard' else ''}) WHERE toLower(n.{KGNameIDProps[graph_db][0]}) CONTAINS \"{term.lower()}\" RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}"
    matches = G.run(query)
    
    for m in matches:
        #nodes_output["search term"].append(term)
        nodes_output["node name"].append(m[0])
        nodes_output["node id"].append(m[1])
        nodes_output["node eq id"].append(m[2])
        try:
            nodes_output["node degree"].append(m[3])
        except:
            continue
    
    for term in terms:
        if term in nodes_output["node name"]:
            index = nodes_output["node name"].index(term)

            if graph_db == "ROBOKOP" or graph_db == "ComptoxAI":
                #message+=f"'{term}' found!\n"
                message+=f"'{term}' found! ID: {nodes_output['node id'][index]}, Degree: {nodes_output['node degree'][index]}\n\n"
            else:
                #message+=f"'{term}' found!\n"
                message+=f"'{term}' found! ID: {nodes_output['node id'][0]}\n\n"

        elif term in nodes_output["node id"]:
            index = nodes_output["node id"].index(term)
            if graph_db == "ROBOKOP" or graph_db == "ComptoxAI":
                #message+=f"'{term}' found!\n"
                message+=f"'{term}' found! Name: {nodes_output['node name'][index]}, Degree: {nodes_output['node degree'][index]}\n\n"
            else:
                #message+=f"'{term}' found!\n"
                message+=f"'{term}' found! Name: {nodes_output['node name'][0]}\n\n"
        
        elif any(term in sublist for sublist in nodes_output["node eq id"]):
            found_list = [sublist for sublist in nodes_output["node eq id"] if term in sublist][0]
            index = nodes_output["node eq id"].index(found_list)
            if graph_db == "ROBOKOP" or graph_db == "ComptoxAI":
                #message+=f"'{term}' found!\n"
                message+=f"'{term}' found! Name: {nodes_output['node name'][index]}, Degree: {nodes_output['node degree'][index]}\n\n"
            else:
                #message+=f"'{term}' found!\n"
                message+=f"'{term}' found! Name: {nodes_output['node name'][0]}\n\n"

        else:
            if graph_db == "ROBOKOP" or graph_db == "ComptoxAI":
                message+=f"'{term}' not found, try instead:\n"
                for w,x,y,z in zip(nodes_output['node name'],nodes_output['node id'],nodes_output['node eq id'],nodes_output['node degree']):
                    if term.lower() in w.lower():
                        message+=f"{str(w)+', Degree: '+str(z)}\n"
                    elif term.lower() in x.lower():
                        message+=f"{str(w)+', '+str(x)+', Degree: '+str(z)}\n"
                    elif any(term.lower() in element.lower() for element in y):
                        message+=f"{str(w)+', '+str([element for element in y if term.lower() in element.lower()])+', Degree: '+str(z)}\n"

                message+=f"\n\n"
                    #message+=f"'{term}' not found, try instead {[str(x)+'('+str(y)+')' for x,y in zip(nodes_output['node name'],nodes_output['node degree']) if term.lower() in x.lower()]}\n\n"
            else:
                message+=f"'{term}' not found, try instead {str([str(x) for x,y in zip(nodes_output['node name'],nodes_output['node id']) if term.lower() in x.lower()])}\n\n"
    
    # for term in ends:
    #     nodes_output = {"search term":[], "node name":[], "node id":[], "node degree":[]}
    #     a=len(nodes_output['node name'])
    #     if graph_db == "ROBOKOP" or "ComptoxAI":
    #         query = f"MATCH (n{':'+endLabel if endLabel != 'wildcard' else ''}) WHERE apoc.meta.type(n.{KGNameIDProps[graph_db][0]}) = 'STRING' AND toLower(n.{KGNameIDProps[graph_db][0]}) CONTAINS \"{term.lower()}\" CALL {'{'}WITH n RETURN apoc.node.degree(n) AS degree{'}'} RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}, degree"
    #     else:
    #         query = f"MATCH (n{':'+endLabel if endLabel != 'wildcard' else ''}) WHERE toLower(n.{KGNameIDProps[graph_db][0]}) CONTAINS \"{term.lower()}\" RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}"
    #     matches = G.run(query)
    #     for m in matches:
    #         nodes_output["search term"].append(term)
    #         nodes_output["node name"].append(m[0])
    #         nodes_output["node id"].append(m[1])
    #         try:
    #             nodes_output["node degree"].append(m[2])
    #         except:
    #             continue
    #     b=len(nodes_output['node name'])
    #     if term in nodes_output["node name"]:
    #         if graph_db == "ROBOKOP":
    #             end_message+=f"'{term}' found! ID: {nodes_output['node id'][0]}, Degree: {nodes_output['node degree'][0]}\n\n"
    #         else:
    #             end_message+=f"'{term}' found! ID: {nodes_output['node id'][0]}\n\n"
    #     else:
    #         if graph_db == "ROBOKOP":
    #             end_message+=f"'{term}' not in {graph_db} under '{end_label}' category, try instead {str([str(x)+'('+str(y)+')' for x,y in zip(nodes_output['node name'],nodes_output['node degree'])])}\n\n"             
    #         else:
    #             end_message+=f"'{term}' not in {graph_db} under '{end_label}' category, try instead {str([str(x) for x in nodes_output['node name']])}\n\n"
        
    return message