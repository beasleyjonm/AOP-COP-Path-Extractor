#from socket import timeout
import pandas as pd
import py2neo
import neo4j
from datetime import datetime
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

def processInputText(text,lower=True):
    l1 = []
    for line in text.split('\n'):
        a = line
        if a != "":
            if lower == True:
                l1.append(a.strip().lower())
            else:
                l1.append(a.strip())
    return l1

def listToString(s,separator="\n"):
 
    # initialize an empty string
    str1 = ""
 
    # traverse in the string
    for ele in s:
        if ele == s[-1]:
            str1 += ele
        else:
            str1 += ele+separator
 
    # return string
    return str1

#@unit_of_work(timeout=1.0)
def run_query(tx,q):
    result = tx.run(q)
    return result

# KGNamesIDProps specififies the keys to properties specific to KGs. The order of terms should be: node names, node primary identifiers, node alternate identifiers, predicate.
# The order of keys should be: node names, node primary identifiers, node alternate identifiers, predicate.
# If nodes have no equivalent identifiers in a KG, make primary and equivalent id keys the same.
KGNameIDProps = {
            "ROBOKOP":["name","id","equivalent_identifiers","predicate"],
            "YOBOKOP":["name","id","equivalent_identifiers","predicate"],
            "SCENT-KOP":["name","id","id","predicate"],
            "HetioNet":["name","identifier","identifier","predicate"],
            "ComptoxAI":["commonName","uri","uri","predicate"]
        }

# qualified_predicates=[
#             "biolink:causes_increased_expression",
#             "biolink:causes_decreased_expression",
#             "biolink:causes_increased_secretion",
#             "biolink:causes_decreased_activity",
#             "biolink:causes_increased_activity",
#             "biolink:causes_increased_synthesis",
#             "biolink:causes_increased_mutation_rate",
#             "biolink:causes_decreased_localization",
#             "biolink:causes_increased_localization",
#             "biolink:causes_increased_uptake",
#             "biolink:causes_increased_degradation",
#             "biolink:causes_increased_abundance",
#             "biolink:causes_decreased_degradation",
#             "biolink:causes_decreased_secretion",
#             "biolink:causes_increased_stability",
#             "biolink:causes_increased_transport",
#             "biolink:causes_decreased_synthesis",
#             "biolink:causes_decreased_abundance",
#             "biolink:causes_decreased_stability",
#             "biolink:causes_increased_molecular_modification",
#             "biolink:causes_decreased_uptake",
#             "biolink:causes_decreased_transport",
#             "biolink:causes_increased_splicing",
#             "biolink:causes_decreased_molecular_modification",
#             "biolink:causes_decreased_mutation_rate"
#         ]
#Version 2
#Uses WHERE IN [] to search for star/end nodes in a list and hopefully improve performance.
#Measured and it IS faster than Version 1.
def Graphsearch(graph_db,start_nodes,end_nodes,nodes,options,edges,get_metadata,timeout_ms,limit_results,contains_starts=False,contains_ends=False,start_end_matching=False):
    if graph_db == "ROBOKOP":
        link = "neo4j://robokopkg.renci.org"
    elif graph_db == "YOBOKOP":
        link = "neo4j://yobokop-neo4j.apps.renci.org"
    elif graph_db == "HetioNet":
        link = "bolt://neo4j.het.io"
    elif graph_db == "SCENT-KOP":
        link = "bolt://scentkop.apps.renci.org"
    elif graph_db == "ComptoxAI":
        link = "bolt://neo4j.comptox.ai:7687"
    try:
        if graph_db == "YOBOKOP":
            G = neo4j.GraphDatabase.driver(link, auth=("neo4j", "ncatgamma"))
        else:
            G = neo4j.GraphDatabase.driver(link)
    except:
        result=['No Results: Connection Broken']
        return (result)
    limit = str(limit_results)

    robokop_output = {}

    frames=[]
    qualified_predicates=[
            "biolink:causes_increased_expression",
            "biolink:causes_decreased_expression",
            "biolink:causes_increased_secretion",
            "biolink:causes_decreased_activity",
            "biolink:causes_increased_activity",
            "biolink:causes_increased_synthesis",
            "biolink:causes_increased_mutation_rate",
            "biolink:causes_decreased_localization",
            "biolink:causes_increased_localization",
            "biolink:causes_increased_uptake",
            "biolink:causes_increased_degradation",
            "biolink:causes_increased_abundance",
            "biolink:causes_decreased_degradation",
            "biolink:causes_decreased_secretion",
            "biolink:causes_increased_stability",
            "biolink:causes_increased_transport",
            "biolink:causes_decreased_synthesis",
            "biolink:causes_decreased_abundance",
            "biolink:causes_decreased_stability",
            "biolink:causes_increased_molecular_modification",
            "biolink:causes_decreased_uptake",
            "biolink:causes_decreased_transport",
            "biolink:causes_increased_splicing",
            "biolink:causes_decreased_molecular_modification",
            "biolink:causes_decreased_mutation_rate"
        ]
   
    print(options)

    for p in nodes:
        query = f"MATCH "
        k = len(nodes[p])
        robokop_output = {}
        where_options = "WHERE "
        for i in range(k):
            if i==0:
                robokop_output.update({f"node{i}: {nodes[p][i]}":[]})
                if get_metadata == True:
                    robokop_output.update({f"n{i}:MetaData":[]})
                if graph_db in ["ROBOKOP","YOBOKOP","ComptoxAI"]:
                    robokop_output.update({f"esnd_n{i}_r{i}":[]})
                robokop_output.update({f"edge{i}":[]})
                if get_metadata == True:
                    if graph_db in ['ROBOKOP', 'YOBOKOP']:
                        robokop_output.update({f"e{i}:MetaData":[]})
                if str(edges[p][i].replace("`","")) in qualified_predicates:
                    query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}{':'+'`biolink:affects`'}]-"
                    where_options = where_options + f"r{i}.qualified_predicate = '{edges[p][i].split('_')[0].replace('`','')}' AND r{i}.object_direction = '{edges[p][i].split('_')[1].replace('`','')}' AND r{i}.object_aspect = '{edges[p][i].split('_')[2].replace('`','')}' AND "
                else:
                    query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"
  
            elif i>0 and i<(k-1):
                robokop_output.update({f"node{i}: {nodes[p][i]}":[]})
                if get_metadata == True:
                    robokop_output.update({f"n{i}:MetaData":[]})
                if graph_db in ["ROBOKOP","YOBOKOP","ComptoxAI"]:
                    robokop_output.update({f"esnd_n{i}_r{i-1}":[]})
                    robokop_output.update({f"esnd_n{i}_r{i}":[]})
                robokop_output.update({f"edge{i}":[]})
                if get_metadata == True:
                    if graph_db == "ROBOKOP":
                        robokop_output.update({f"e{i}:MetaData":[]})
                if edges[p][i].replace("`","") in qualified_predicates:
                    query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}{':'+'`biolink:affects`'}]-"
                    where_options = where_options + f"r{i}.qualified_predicate = '{edges[p][i].split('_')[0].replace('`','')}' AND r{i}.object_direction = '{edges[p][i].split('_')[1].replace('`','')}' AND r{i}.object_aspect = '{edges[p][i].split('_')[2].replace('`','')}' AND "
                else:
                    query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"
        
                if options[p][i-1] != "wildcard":
                    options_list = processInputText(options[p][i-1])
                    any_options = [x for x in options_list if x[0:2] != "!="]
                    not_options = [x.replace("!=","") for x in options_list if x[0:2] == "!="]
                    if len(any_options) > 0:
                        if ":" in str(any_options):
                            where_options = where_options + f"any(x IN {str(any_options)} WHERE x IN reduce(list = [], n IN n{i}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{i}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                        else:
                            where_options = where_options + f"toLower(n{i}.{KGNameIDProps[graph_db][0]}) IN {str(any_options)} "
                    
                    if len(not_options) > 0:
                        if len(any_options) > 0:
                            where_options = where_options + "AND "
                        if ":" in str(not_options):
                            where_options = where_options + f"none(x IN {str(not_options)} WHERE x IN reduce(list = [], n IN n{i}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{i}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                        else:
                            where_options = where_options + f"NOT toLower(n{i}.{KGNameIDProps[graph_db][0]}) IN {str(not_options)} "

            else:
                robokop_output.update({f"node{i}: {nodes[p][i]}":[]})
                if get_metadata == True:
                    robokop_output.update({f"n{i:}MetaData":[]})
                if graph_db in ["ROBOKOP","YOBOKOP","ComptoxAI"]:
                    robokop_output.update({f"esnd_n{i}_r{i-1}":[]})
                query = query + f"(n{i}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''}) "
        
        query = query + where_options
        if len(where_options)>6:
            query = query + "AND "

        if start_end_matching == False:
            que = query 
            if "wildcard" in start_nodes and "wildcard" in end_nodes:
                continue

            elif "wildcard" in start_nodes:
                any_ends = [x for x in end_nodes if  x[0:2] != "!="]
                not_ends = [x.replace("!=","") for x in end_nodes if x[0:2] == "!="]
                if len(any_ends) > 0:
                    if ":" in str(any_ends):
                        que = que + f"any(x IN {str(any_ends)} WHERE x IN reduce(list = [], n IN n{k-1}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "               
                    else:
                        que = que + f"toLower(n{k-1}.{KGNameIDProps[graph_db][0]}) IN {str(any_ends)} "

                if len(not_ends) > 0:
                    if len(any_ends) > 0:
                        que = que + "AND "
                    if ":" in str(not_ends):
                        que = que + f"none(x IN {str(not_ends)} WHERE x IN reduce(list = [], n IN n{k-1}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "               
                    else:
                        que = que + f"NOT toLower(n{k-1}.{KGNameIDProps[graph_db][0]}) IN {str(not_ends)} "

            elif "wildcard" in end_nodes:
                any_starts = [x for x in start_nodes if  x[0:2] != "!="]
                not_starts = [x.replace("!=","") for x in start_nodes if x[0:2] == "!="]
                if len(any_starts) > 0:
                    if ":" in str(any_starts):
                        que = que + f"any(x IN {str(any_starts)} WHERE x IN reduce(list = [], n IN n{0}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{0}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                    else:
                        que = que + f"toLower(n{0}.{KGNameIDProps[graph_db][0]}) IN {str(any_starts)} "

                if len(not_starts) > 0:
                    if len(any_starts) > 0:
                        que = que + "AND "
                    if ":" in str(not_starts):
                        que = que + f"none(x IN {str(not_starts)} WHERE x IN reduce(list = [], n IN n{k-1}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "               
                    else:
                        que = que + f"NOT toLower(n{k-1}.{KGNameIDProps[graph_db][0]}) IN {str(not_starts)} "

            else:
                any_ends = [x for x in end_nodes if  x[0:2] != "!="]
                not_ends = [x.replace("!=","") for x in end_nodes if x[0:2] == "!="]
                any_starts = [x for x in start_nodes if  x[0:2] != "!="]
                not_starts = [x.replace("!=","") for x in start_nodes if x[0:2] == "!="]
                if len(any_starts) > 0:
                    if ":" in str(any_starts):
                        que = que + f"any(x IN {str(any_starts)} WHERE x IN reduce(list = [], n IN n{0}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{0}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) " 
                    else:
                        que = que + f"toLower(n{0}.{KGNameIDProps[graph_db][0]}) IN {str(any_starts)} "
                if len(any_ends) > 0:
                    if len(any_starts) > 0:
                        que = que + "AND "
                    if ":" in str(any_ends):
                        que = que + f"any(x IN {str(any_ends)} WHERE x IN reduce(list = [], n IN n{k-1}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                    else:
                        que = que + f"toLower(n{k-1}.{KGNameIDProps[graph_db][0]}) IN {str(any_ends)} "

                if len(not_starts) > 0:
                    if len(any_starts)+len(any_ends) > 0:
                        que = que + "AND "
                    if ":" in str(not_starts):
                        que = que + f"none(x IN {str(not_starts)} WHERE x IN reduce(list = [], n IN n{0}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{0}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) " 
                    else:
                        que = que + f"NOT toLower(n{0}.{KGNameIDProps[graph_db][0]}) IN {str(not_starts)} "
                
                if len(not_ends) > 0:
                    if len(any_starts)+len(any_ends)+len(not_starts) > 0:
                        que = que + "AND "
                    if ":" in str(not_ends):
                        que = que + f"none(x IN {str(not_ends)} WHERE x IN reduce(list = [], n IN n{k-1}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                    else:
                        que = que + f"NOT toLower(n{k-1}.{KGNameIDProps[graph_db][0]}) IN {str(not_ends)} "
                  
            q = que
                                 
        # elif start_end_matching == True:
        #     for start, end in zip(start_nodes, end_nodes):
        #         que = query
        #         if "wildcard" in start and "wildcard" in end:
        #             que = que
        #         elif "wildcard" in start:
        #             que = que + f"{'WHERE' if len(where_options)<=6 else ''} n{k-1}.{KGNameIDProps[graph_db][0]} = \"{end}\" "
        #         elif "wildcard" in end:
        #             que = que + f"{'WHERE' if len(where_options)<=6 else ''} n{0}.{KGNameIDProps[graph_db][0]} = \"{start}\" "
        #         else:
        #             que = que + f"{'WHERE' if len(where_options)<=6 else ''} n{0}.{KGNameIDProps[graph_db][0]} {'CONTAINS' if contains_starts==True else '='} \"{start}\" AND (n{k-1}.{KGNameIDProps[graph_db][0]}) {'CONTAINS' if contains_ends==True else '='} \"{end}\" "
        #         q = que
                
        if graph_db in ["ROBOKOP","YOBOKOP","ComptoxAI"]:
            for i in range(k):
                firstbracket = "{"
                secondbracket = "}"
                firstmark = f"'`'+"
                secondmark = f"+'`'"
                if i==0:
                    q = q + f"CALL{firstbracket}WITH n{i}, r{i} MATCH(n{i})-[r{i}]-(t) RETURN apoc.node.degree(n{i}, {firstmark if graph_db in ['ROBOKOP', 'YOBOKOP'] else ''}TYPE(r{i}){secondmark if graph_db in ['ROBOKOP', 'YOBOKOP'] else ''}) AS esnd_n{i}_r{i}{secondbracket} "
                elif i>0 and i<(k-1):
                    q = q + f"CALL{firstbracket}WITH n{i}, r{i-1} MATCH(n{i})-[r{i-1}]-(t) RETURN apoc.node.degree(n{i}, {firstmark if graph_db in ['ROBOKOP', 'YOBOKOP'] else ''}TYPE(r{i-1}){secondmark if graph_db in ['ROBOKOP', 'YOBOKOP'] else ''}) AS esnd_n{i}_r{i-1}{secondbracket} CALL{firstbracket}WITH n{i}, r{i} MATCH(n{i})-[r{i}]-(t) RETURN apoc.node.degree(n{i}, {firstmark if graph_db in ['ROBOKOP', 'YOBOKOP'] else ''}TYPE(r{i}){secondmark if graph_db in ['ROBOKOP', 'YOBOKOP'] else ''}) AS esnd_n{i}_r{i}{secondbracket} "
                else:
                    q = q + f"CALL{firstbracket}WITH n{i}, r{i-1} MATCH(n{i})-[r{i-1}]-(t) RETURN apoc.node.degree(n{i}, {firstmark if graph_db in ['ROBOKOP', 'YOBOKOP'] else ''}TYPE(r{i-1}){secondmark if graph_db in ['ROBOKOP', 'YOBOKOP'] else ''}) AS esnd_n{i}_r{i-1}{secondbracket} RETURN "
            
            if get_metadata == True:
                for z in range(k):
                    if z==0:
                        q = q + f"properties(n{z}) as n{z}, esnd_n{z}_r{z}, TYPE(r{z}) as r{z}_type, {'properties(r'+str(z)+') as r'+str(z) if graph_db in ['ROBOKOP', 'YOBOKOP'] else ''}, "
                    elif z>0 and z<(k-1):
                        q = q + f"properties(n{z}) as n{z}, esnd_n{z}_r{z-1}, esnd_n{z}_r{z}, TYPE(r{z}) as r{z}_type, {'properties(r'+str(z)+') as r'+str(z) if graph_db in ['ROBOKOP', 'YOBOKOP'] else ''}, "
                    else: 
                        q = q + f"properties(n{z}) as n{z}, esnd_n{z}_r{z-1} LIMIT {limit}"
            else:
                for z in range(k):
                    if z==0:
                        q = q + f"n{z}.{KGNameIDProps[graph_db][0]} as n{z}, esnd_n{z}_r{z}, TYPE(r{z}) as r{z}, apoc.text.join([r{z}.qualified_predicate,r{z}.object_direction,r{z}.object_aspect],' ') as r{z}_qual_pred, "
                    elif z>0 and z<(k-1):
                        q = q + f"n{z}.{KGNameIDProps[graph_db][0]} as n{z}, esnd_n{z}_r{z-1}, esnd_n{z}_r{z}, TYPE(r{z}) as r{z}, apoc.text.join([r{z}.qualified_predicate,r{z}.object_direction,r{z}.object_aspect],' ') as r{z}_qual_pred, "
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
            if graph_db in ["ROBOKOP","YOBOKOP","ComptoxAI"]:
                q = f"CALL apoc.cypher.runTimeboxed(\"{q}\",null,{timeout_ms}) YIELD value RETURN "
                for z in range(k):
                    if z==0:
                        if graph_db in ["ROBOKOP", "YOBOKOP"]:
                            q = q + f"value.n{z}.{KGNameIDProps[graph_db][0]}, value.n{z}, value.esnd_n{z}_r{z}, value.r{z}_type, apoc.text.join([value.r{z}.qualified_predicate,value.r{z}.object_direction,value.r{z}.object_aspect],' '), value.r{z}, "
                        else:
                            q = q + f"value.n{z}.{KGNameIDProps[graph_db][0]}, value.n{z}, value.esnd_n{z}_r{z}, value.r{z}_type, "
                    elif z>0 and z<(k-1):
                        if graph_db in ["ROBOKOP", "YOBOKOP"]:
                            q = q + f"value.n{z}.{KGNameIDProps[graph_db][0]}, value.n{z}, value.esnd_n{z}_r{z-1}, value.esnd_n{z}_r{z}, value.r{z}_type, apoc.text.join([value.r{z}.qualified_predicate,value.r{z}.object_direction,value.r{z}.object_aspect],' '), value.r{z}, "
                        else:
                            q = q + f"value.n{z}.{KGNameIDProps[graph_db][0]}, value.n{z}, value.esnd_n{z}_r{z-1}, value.esnd_n{z}_r{z}, value.r{z}_type, "
                    else: 
                        q = q + f"value.n{z}.{KGNameIDProps[graph_db][0]}, value.n{z}, value.esnd_n{z}_r{z-1}"
            print(q+"\n")

        else:
            if graph_db in ["ROBOKOP","YOBOKOP","ComptoxAI"]:
                q = f"CALL apoc.cypher.runTimeboxed(\"{q}\",null,{timeout_ms}) YIELD value RETURN "
                for z in range(k):
                    if z==0:
                        q = q + f"value.n{z}, value.esnd_n{z}_r{z}, value.r{z}, value.r{z}_qual_pred, "
                    elif z>0 and z<(k-1):
                        q = q + f"value.n{z}, value.esnd_n{z}_r{z-1}, value.esnd_n{z}_r{z}, value.r{z}, value.r{z}_qual_pred, "
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
                    if 'edge' in j:
                        robokop_output[j].append(str(m[l+1]).replace('biolink:','').replace('_',' ') if 'null' not in m[l+1] else str(m[l]).replace('biolink:','').replace('_',' '))
                        l += 1
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
                    options_list = processInputText(options[p][i-1])
                    any_options = [x for x in options_list if x[0:2] != "!="]
                    not_options = [x.replace("!=","") for x in options_list if x[0:2] == "!="]
                    if len(any_options) > 0:
                        if ":" in str(any_options):
                            display_where_options = display_where_options + f"any(x IN {str(any_options)} WHERE x IN reduce(list = [], n IN n{i}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{i}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                        else:
                            display_where_options = display_where_options + f"toLower(n{i}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(any_options)} "
                    
                    if len(not_options) > 0:
                        if len(any_options) > 0:
                            display_where_options = display_where_options + "AND "
                        if ":" in str(not_options):
                            display_where_options = display_where_options + f"none(x IN {str(not_options)} WHERE x IN reduce(list = [], n IN n{i}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{i}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                        else:
                            display_where_options = display_where_options + f"NOT toLower(n{i}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(not_options)} "

            else:
                display_query = display_query + f"(n{i}_{p_num}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})"
        
        if len(display_where_options)>6:
            display_where_options = display_where_options + "AND "

        if start_end_matching == False:
            if "wildcard" in start_nodes and "wildcard" in end_nodes:
                continue
            elif "wildcard" in start_nodes:
                any_ends = [x for x in end_nodes if  x[0:2] != "!="]
                not_ends = [x.replace("!=","") for x in end_nodes if x[0:2] == "!="]
                if len(any_ends) > 0:
                    if ":" in str(any_ends):
                        display_where_options = display_where_options + f"any(x IN {str(any_ends)} WHERE x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "               
                    else:
                        display_where_options = display_where_options + f"toLower(n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(any_ends)} "

                if len(not_ends) > 0:
                    if len(any_ends) > 0:
                        display_where_options = display_where_options + "AND "
                    if ":" in str(not_ends):
                        display_where_options = display_where_options + f"none(x IN {str(not_ends)} WHERE x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "               
                    else:
                        display_where_options = display_where_options + f"NOT toLower(n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(not_ends)} "

            elif "wildcard" in end_nodes:
                any_starts = [x for x in start_nodes if  x[0:2] != "!="]
                not_starts = [x.replace("!=","") for x in start_nodes if x[0:2] == "!="]
                if len(any_starts) > 0:
                    if ":" in str(any_starts):
                        display_where_options = display_where_options + f"any(x IN {str(any_starts)} WHERE x IN reduce(list = [], n IN n{0}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{0}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                    else:
                        display_where_options = display_where_options + f"toLower(n{0}.{KGNameIDProps[graph_db][0]}) IN {str(any_starts)} "

                if len(not_starts) > 0:
                    if len(any_starts) > 0:
                        display_where_options = display_where_options + "AND "
                    if ":" in str(not_starts):
                        display_where_options = display_where_options + f"none(x IN {str(not_starts)} WHERE x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "               
                    else:
                        display_where_options = display_where_options + f"NOT toLower(n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(not_starts)} "

            else:
                any_ends = [x for x in end_nodes if  x[0:2] != "!="]
                not_ends = [x.replace("!=","") for x in end_nodes if x[0:2] == "!="]
                any_starts = [x for x in start_nodes if  x[0:2] != "!="]
                not_starts = [x.replace("!=","") for x in start_nodes if x[0:2] == "!="]
                if len(any_starts) > 0:
                    if ":" in str(any_starts):
                        display_where_options = display_where_options + f"any(x IN {str(any_starts)} WHERE x IN reduce(list = [], n IN n{0}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{0}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) " 
                    else:
                        display_where_options = display_where_options + f"toLower(n{0}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(any_starts)} "
                if len(any_ends) > 0:
                    if len(any_starts) > 0:
                        display_where_options = display_where_options + "AND "
                    if ":" in str(any_ends):
                        display_where_options = display_where_options + f"any(x IN {str(any_ends)} WHERE x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                    else:
                        display_where_options = display_where_options + f"toLower(n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(any_ends)} "

                if len(not_starts) > 0:
                    if len(any_starts)+len(any_ends) > 0:
                        display_where_options = display_where_options + "AND "
                    if ":" in str(not_starts):
                        display_where_options = display_where_options + f"none(x IN {str(not_starts)} WHERE x IN reduce(list = [], n IN n{0}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{0}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) " 
                    else:
                        display_where_options = display_where_options + f"NOT toLower(n{0}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(not_starts)} "
                
                if len(not_ends) > 0:
                    if len(any_starts)+len(any_ends)+len(not_starts) > 0:
                        display_where_options = display_where_options + "AND "
                    if ":" in str(not_ends):
                        display_where_options = display_where_options + f"none(x IN {str(not_ends)} WHERE x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                    else:
                        display_where_options = display_where_options + f"NOT toLower(n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(not_ends)} "

            if p_num < len(nodes)-1:
                display_where_options = display_where_options + "AND "
                                           
        print(display_query)
        neo4j_query = f"{neo4j_query}{display_query}{' ' if p_num == (len(nodes)-1) else ', '}"
        p_num += 1

    neo4j_query = neo4j_query + display_where_options + f"RETURN * LIMIT {limit_results}"
    print(neo4j_query)

    return neo4j_query

#Function to test if a given query will return ANY paths (at least 1)
def TestQuery(graph_db,start_nodes,end_nodes,nodes,options,edges,start_end_matching=False):
    if graph_db == "ROBOKOP":
        link = "neo4j://robokopkg.renci.org"
    elif graph_db == "YOBOKOP":
        link = "neo4j://yobokop-neo4j.apps.renci.org"
    elif graph_db == "HetioNet":
        link = "bolt://neo4j.het.io"
    elif graph_db == "SCENT-KOP":
        link = "bolt://scentkop.apps.renci.org"
    elif graph_db == "ComptoxAI":
        link = "bolt://neo4j.comptox.ai:7687"
    try:
        if graph_db == "YOBOKOP":
            G = neo4j.GraphDatabase.driver(link, auth=("neo4j", "ncatgamma"))
        else:
            G = neo4j.GraphDatabase.driver(link)
    except:
        result=['No Results: Connection Broken']
        return (result)
    
    neo4j_query = "MATCH "
    test_where_options = "WHERE "
    p_num = 0
   
    for p in nodes:
        test_query = ""
        k = len(nodes[p])
        for i in range(k):
            if i==0:
                test_query = test_query + f"(n{i}_{p_num}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}_{p_num}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"

            elif i>0 and i<(k-1):
                test_query = test_query + f"(n{i}_{p_num}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})-[r{i}_{p_num}{':'+edges[p][i] if 'wildcard' not in edges[p][i] else ''}]-"




                if options[p][i-1] != "wildcard":
                    options_list = processInputText(options[p][i-1])
                    any_options = [x for x in options_list if x[0:2] != "!="]
                    not_options = [x.replace("!=","") for x in options_list if x[0:2] == "!="]
                    if len(any_options) > 0:
                        if ":" in str(any_options):
                            test_where_options = test_where_options + f"any(x IN {str(any_options)} WHERE x IN reduce(list = [], n IN n{i}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{i}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                        else:
                            test_where_options = test_where_options + f"toLower(n{i}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(any_options)} "
                    
                    if len(not_options) > 0:
                        if len(any_options) > 0:
                            test_where_options = test_where_options + "AND "
                        if ":" in str(not_options):
                            test_where_options = test_where_options + f"none(x IN {str(not_options)} WHERE x IN reduce(list = [], n IN n{i}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{i}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                        else:
                            test_where_options = test_where_options + f"NOT toLower(n{i}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(not_options)} "

            else:
                test_query = test_query + f"(n{i}_{p_num}{':'+nodes[p][i] if 'wildcard' not in nodes[p][i] else ''})"
        
        if len(test_where_options)>6:
            test_where_options = test_where_options + "AND "

        if start_end_matching == False:
            if "wildcard" in start_nodes and "wildcard" in end_nodes:
                continue
            elif "wildcard" in start_nodes:
                any_ends = [x for x in end_nodes if  x[0:2] != "!="]
                not_ends = [x.replace("!=","") for x in end_nodes if x[0:2] == "!="]
                if len(any_ends) > 0:
                    if ":" in str(any_ends):
                        test_where_options = test_where_options + f"any(x IN {str(any_ends)} WHERE x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "               
                    else:
                        test_where_options = test_where_options + f"toLower(n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(any_ends)} "

                if len(not_ends) > 0:
                    if len(any_ends) > 0:
                        test_where_options = test_where_options + "AND "
                    if ":" in str(not_ends):
                        test_where_options = test_where_options + f"none(x IN {str(not_ends)} WHERE x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "               
                    else:
                        test_where_options = test_where_options + f"NOT toLower(n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(not_ends)} "

            elif "wildcard" in end_nodes:
                any_starts = [x for x in start_nodes if  x[0:2] != "!="]
                not_starts = [x.replace("!=","") for x in start_nodes if x[0:2] == "!="]
                if len(any_starts) > 0:
                    if ":" in str(any_starts):
                        test_where_options = test_where_options + f"any(x IN {str(any_starts)} WHERE x IN reduce(list = [], n IN n{0}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{0}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                    else:
                        test_where_options = test_where_options + f"toLower(n{0}.{KGNameIDProps[graph_db][0]}) IN {str(any_starts)} "

                if len(not_starts) > 0:
                    if len(any_starts) > 0:
                        test_where_options = test_where_options + "AND "
                    if ":" in str(not_starts):
                        test_where_options = test_where_options + f"none(x IN {str(not_starts)} WHERE x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "               
                    else:
                        test_where_options = test_where_options + f"NOT toLower(n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(not_starts)} "

            else:
                any_ends = [x for x in end_nodes if  x[0:2] != "!="]
                not_ends = [x.replace("!=","") for x in end_nodes if x[0:2] == "!="]
                any_starts = [x for x in start_nodes if  x[0:2] != "!="]
                not_starts = [x.replace("!=","") for x in start_nodes if x[0:2] == "!="]
                if len(any_starts) > 0:
                    if ":" in str(any_starts):
                        test_where_options = test_where_options + f"any(x IN {str(any_starts)} WHERE x IN reduce(list = [], n IN n{0}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{0}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) " 
                    else:
                        test_where_options = test_where_options + f"toLower(n{0}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(any_starts)} "
                if len(any_ends) > 0:
                    if len(any_starts) > 0:
                        test_where_options = test_where_options + "AND "
                    if ":" in str(any_ends):
                        test_where_options = test_where_options + f"any(x IN {str(any_ends)} WHERE x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                    else:
                        test_where_options = test_where_options + f"toLower(n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(any_ends)} "

                if len(not_starts) > 0:
                    if len(any_starts)+len(any_ends) > 0:
                        test_where_options = test_where_options + "AND "
                    if ":" in str(not_starts):
                        test_where_options = test_where_options + f"none(x IN {str(not_starts)} WHERE x IN reduce(list = [], n IN n{0}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{0}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) " 
                    else:
                        test_where_options = test_where_options + f"NOT toLower(n{0}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(not_starts)} "
                
                if len(not_ends) > 0:
                    if len(any_starts)+len(any_ends)+len(not_starts) > 0:
                        test_where_options = test_where_options + "AND "
                    if ":" in str(not_ends):
                        test_where_options = test_where_options + f"none(x IN {str(not_ends)} WHERE x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]} | list + toLower(n)) OR x IN reduce(list = [], n IN n{k-1}_{p_num}.{KGNameIDProps[graph_db][2]} | list + toLower(n))) "
                    else:
                        test_where_options = test_where_options + f"NOT toLower(n{k-1}_{p_num}.{KGNameIDProps[graph_db][0]}) IN {str(not_ends)} "

            if p_num < len(nodes)-1:
                test_where_options = test_where_options + "AND "
                                           
        neo4j_query = f"{neo4j_query}{test_query}{' ' if p_num == (len(nodes)-1) else ', '}"
        p_num += 1

    neo4j_query = neo4j_query + test_where_options + f"RETURN n0_0.{KGNameIDProps[graph_db][0]} as n0_0 LIMIT 1000"
    if graph_db in ["ROBOKOP","YOBOKOP","ComptoxAI"]:
        neo4j_query = f"CALL apoc.cypher.runTimeboxed(\"{neo4j_query}\",null,10000) YIELD value RETURN value.n0_0"
    print(neo4j_query)
    session = G.session()#.data()
    timestamp1 = datetime.now().timestamp()
    try:
        matches = run_query(session,neo4j_query)
        #any_matches = int(str([m for m in matches][0]).replace('<Record count(*)=','').replace('>',''))
        any_matches = len([m for m in matches])
    except:
        any_matches = "undefined"
    timestamp2 = datetime.now().timestamp()
    if timestamp2-timestamp1 > 10:
        any_matches = "undefined"
    return any_matches

def getNodeAndEdgeLabels(graph_db):
    qualified_predicates=[
            "biolink:causes_increased_expression",
            "biolink:causes_decreased_expression",
            "biolink:causes_increased_secretion",
            "biolink:causes_decreased_activity",
            "biolink:causes_increased_activity",
            "biolink:causes_increased_synthesis",
            "biolink:causes_increased_mutation_rate",
            "biolink:causes_decreased_localization",
            "biolink:causes_increased_localization",
            "biolink:causes_increased_uptake",
            "biolink:causes_increased_degradation",
            "biolink:causes_increased_abundance",
            "biolink:causes_decreased_degradation",
            "biolink:causes_decreased_secretion",
            "biolink:causes_increased_stability",
            "biolink:causes_increased_transport",
            "biolink:causes_decreased_synthesis",
            "biolink:causes_decreased_abundance",
            "biolink:causes_decreased_stability",
            "biolink:causes_increased_molecular_modification",
            "biolink:causes_decreased_uptake",
            "biolink:causes_decreased_transport",
            "biolink:causes_increased_splicing",
            "biolink:causes_decreased_molecular_modification",
            "biolink:causes_decreased_mutation_rate"
        ]
    if graph_db == "ROBOKOP":
        link = "bolt://robokopkg.renci.org"
    if graph_db == "YOBOKOP":
        link = "bolt://yobokop-neo4j.apps.renci.org"
    elif graph_db == "HetioNet":
        link = "bolt://neo4j.het.io"
    elif graph_db == "SCENT-KOP":
        link = "bolt://scentkop.apps.renci.org"
    elif graph_db == "ComptoxAI":
        link = "bolt://neo4j.comptox.ai:7687"
    rk_nodes=[]
    #rk_edges=[]
    if graph_db == "ROBOKOP":
        rk_edges=qualified_predicates
    else:
        rk_edges=[]
    try:
        if graph_db == "YOBOKOP":
            G = py2neo.Graph(link, auth=("neo4j", "ncatgamma"))
        else:
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
    terms = processInputText(terms,lower=False)
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
    if graph_db == "YOBOKOP":
        link = "bolt://yobokop-neo4j.apps.renci.org"
    elif graph_db == "HetioNet":
        link = "bolt://neo4j.het.io"
    elif graph_db == "SCENT-KOP":
        link = "bolt://scentkop.apps.renci.org"
    elif graph_db == "ComptoxAI":
        link = "bolt://neo4j.comptox.ai:7687"
    try:
        if graph_db == "YOBOKOP":
            G = py2neo.Graph(link, auth=("neo4j", "ncatgamma"))
        else:
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
    
    if graph_db in ["ROBOKOP","YOBOKOP","ComptoxAI"]:
        query = f"WITH [{searched_list}] as terms MATCH (n{':'+ Label if Label != 'wildcard' else ''}) WHERE apoc.meta.type(n.{KGNameIDProps[graph_db][0]}) = 'STRING' AND any(term IN terms WHERE toLower(n.{KGNameIDProps[graph_db][0]}) CONTAINS term OR toLower(apoc.text.join(n.{KGNameIDProps[graph_db][2]}, ',')) CONTAINS term) CALL {'{'}WITH n RETURN apoc.node.degree(n) AS degree{'}'} RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}, n.{KGNameIDProps[graph_db][2]}, degree LIMIT 10000"
    else:
        query = f"MATCH (n{':'+Label if Label != 'wildcard' else ''}) WHERE toLower(n.{KGNameIDProps[graph_db][0]}) IN [{searched_list}] OR toLower(apoc.text.join(n.{KGNameIDProps[graph_db][2]}, ',')) IN [{searched_list}] RETURN n.{KGNameIDProps[graph_db][0]}, n.{KGNameIDProps[graph_db][1]}, n.{KGNameIDProps[graph_db][2]} LIMIT 10000"
    
    matches = G.run(query)
    
    for m in matches:
        nodes_output["node name"].append(m[0])
        nodes_output["node id"].append(m[1])
        nodes_output["node eq id"].append(m[2])
        try:
            nodes_output["node degree"].append(m[3])
        except:
            continue

    lower_node_names = [x.lower() for x in nodes_output["node name"]]
    lower_node_ids = [x.lower() for x in nodes_output["node name"]]
    lower_node_eq_ids = [list(map(lambda i:i.lower(), x)) for x in nodes_output["node eq id"]]

    for term in terms:
        lower_term = term.lower()
        if lower_term in lower_node_names:
            indices = [i for i,j in enumerate(lower_node_names) if j == lower_term]
            if graph_db in ["ROBOKOP","YOBOKOP","ComptoxAI"]:
                if term in nodes_output['node name']:
                    message+=f"'{term}' found!\nNode IDs:\n{listToString([nodes_output['node id'][index] for index in indices])}\nNode Degrees: {[nodes_output['node degree'][index] for index in indices]}\n\n"
                else:
                    message+=f"'{term}' found as:\n{listToString([nodes_output['node name'][index] for index in indices])}\nNode IDs:\n{listToString([nodes_output['node id'][index] for index in indices])}\nNode Degrees: {[nodes_output['node degree'][index] for index in indices]}\n\n"
            else:
                if term in nodes_output['node name']:
                    message+=f"'{term}' found!\nNode IDs:\n{listToString([nodes_output['node id'][index] for index in indices])}\n\n"
                else:
                    message+=f"'{term}' found as:\n{listToString([nodes_output['node name'][index] for index in indices])}\nNode IDs:\n{listToString([nodes_output['node id'][index] for index in indices])}\n\n"

        elif lower_term in lower_node_ids:
            indices = [i for i,j in enumerate(lower_node_ids) if j == lower_term]
            if graph_db in ["ROBOKOP","YOBOKOP","ComptoxAI"]:
                #message+=f"'{term}' found!\n"
                message+=f"'{term}' found!\nNode Names:\n{listToString([nodes_output['node name'][index] for index in indices])}\nNode Degrees: {[nodes_output['node degree'][index] for index in indices]}\n\n"
            else:
                #message+=f"'{term}' found!\n"
                message+=f"'{term}' found!\nNode Names:\n{listToString([nodes_output['node name'][index] for index in indices])}\n\n"
        
        elif any(lower_term in sublist for sublist in lower_node_eq_ids):
            found_list = [sublist for sublist in lower_node_eq_ids if lower_term in sublist][0]
            indices = [i for i,j in enumerate(lower_node_eq_ids) if j == found_list]
            if graph_db in ["ROBOKOP","YOBOKOP","ComptoxAI"]:
                #message+=f"'{term}' found!\n"
                message+=f"'{term}' found!\nNode Names:\n{listToString([nodes_output['node name'][index] for index in indices])}\nNode Degrees: {[nodes_output['node degree'][index] for index in indices]}\n\n"
            else:
                #message+=f"'{term}' found!\n"
                message+=f"'{term}' found!\nNode Names:\n{listToString([nodes_output['node name'][index] for index in indices])}\n\n"

        else:
            if graph_db in ["ROBOKOP","YOBOKOP","ComptoxAI"]:
                message+=f"'{term}' not found, try instead:\n"
                for w,x,y,z in zip(nodes_output['node name'],nodes_output['node id'],nodes_output['node eq id'],nodes_output['node degree']):
                    if term.lower() in w.lower():
                        message+=f"{str(w)+', Degree: '+str(z)+', ID: '+str(x)}\n"
                    elif term.lower() in x.lower():
                        message+=f"{str(w)+', '+str(x)+', Degree: '+str(z)+', ID: '+str(x)}\n"
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
