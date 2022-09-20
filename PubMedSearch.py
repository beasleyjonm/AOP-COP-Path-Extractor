import pandas as pd
import requests as rq
import xml.etree.cElementTree as ElementTree
import time

def PubMedCoMentions(dff,selected_columns,expand=True):
    expand = True
    number = len(selected_columns)
    two_term_dict = dict()
    three_term_dict = dict()
    comention_counts_1_2 = list()
    comention_counts_1_2_link = list()
    comention_counts_1_3 = list()
    comention_counts_1_3_link = list()
    comention_counts_2_3 = list()
    comention_counts_2_3_link = list()
    comention_counts_1_2_3 = list()
    comention_counts_1_2_3_link = list()
    URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    if number not in [2,3]:
        ammended_answers = dff.to_dict('records')
        ammended_columns = [{"name": i.replace("`","").replace("biolink:",""), "id": i, "hideable":True, "selectable": False, "presentation":"markdown"} if " link" in i else {"name": i.replace("`","").replace("biolink:",""), "id": i, "hideable": True, "selectable": [True if "node" in i and " counts" not in i else False]} for i in dff.columns]
        hidden_columns=[i for i in dff.columns if " link" in i]+[i for i in dff.columns if "esnd" in i]
        message = "Please select 2 or 3 node columns for PubMed search."
        return (ammended_answers, ammended_columns, hidden_columns, message)
        
    print("Running PubMed Check")
    if number == 2:
        print('number=2')
        Term1=selected_columns[0].replace('`','').replace('biolink:','')
        Term2=selected_columns[1].replace('`','').replace('biolink:','')
        if f"{Term1}-{Term2} counts" or f"{Term1}-{Term2} counts" not in dff.columns:
            term1_list=dff[selected_columns[0]].tolist()
            term2_list=dff[selected_columns[1]].tolist()
            for (term1, term2) in zip(term1_list, term2_list):
                key=f"{term1}:{term2}"
                if key not in two_term_dict.keys():
                    if(expand):
                        two_term = f'{term1} AND {term2}'
                    else:
                        two_term = f'"{term1}"[All Fields] AND "{term2}"[All Fields]'

                    PARAMS = {'db':'pubmed','term':two_term,'retmax':'0','api_key':'0595c1cc493e78f5a76d62b9f0cdc845e309'}
                    time.sleep(0.1)
                    r = rq.get(url = URL, params = PARAMS)
                    if(r.status_code != rq.codes.ok):
                        time.sleep(1.0)
                        r = rq.get(url = URL, params = PARAMS)
                    tree = ElementTree.fromstring(r.text)
                    cnt = int(tree.find("Count").text)
                    print(f"{term1}-{term2}:{cnt}")
                    two_term_dict[key] = cnt
                else:
                    cnt = two_term_dict[key]
                comention_counts_1_2.append(cnt)
                comention_counts_1_2_link.append(f"{str(cnt)} <a href='https://pubmed.ncbi.nlm.nih.gov/?term={term1} AND {term2}' target='_blank' rel='noopener noreferrer'>[Link]</a>")

            dff.insert(0, f"{Term1}-{Term2} counts", comention_counts_1_2)
            dff.insert(0, f"{Term1}-{Term2} link", comention_counts_1_2_link)

    elif number == 3:
        print('number=3')
        Term1=selected_columns[0].replace('`','').replace('biolink:','')
        Term2=selected_columns[1].replace('`','').replace('biolink:','')
        Term3=selected_columns[2].replace('`','').replace('biolink:','')
        term1_list=dff[selected_columns[0]].tolist()
        term2_list=dff[selected_columns[1]].tolist()
        term3_list=dff[selected_columns[2]].tolist()
        for (term1, term2, term3) in zip(term1_list, term2_list, term3_list):
            onetwokey=f"{term1}_{term2}"
            onethreekey=f"{term1}_{term3}"
            twothreekey=f"{term2}_{term3}"
            onetwothreekey=f"{term1}_{term2}_{term3}"
            
            if(expand):
                term_1_2 = f'{term1} AND {term2}'
                term_1_3 = f'{term1} AND {term3}'
                term_2_3 = f'{term2} AND {term3}'
                term_1_2_3 = f'{term1} AND {term2} AND {term3}'
            else:
                term_1_2 = f'"{term1}"[All Fields] AND "{term2}"[All Fields]'
                term_1_3 = f'"{term1}"[All Fields] AND "{term3}"[All Fields]'
                term_2_3 = f'"{term2}"[All Fields] AND "{term3}"[All Fields]'
                term_1_2_3 = f'"{term1}"[All Fields] AND "{term2}"[All Fields] AND "{term3}"[All Fields]'

            if f"{Term1}-{Term2} counts" or f"{Term2}-{Term1} counts" not in dff.columns:
                if onetwokey not in two_term_dict.keys():
                    PARAMS = {'db':'pubmed','term':term_1_2,'retmax':'0','api_key':'0595c1cc493e78f5a76d62b9f0cdc845e309'}
                    time.sleep(0.1)
                    r = rq.get(url = URL, params = PARAMS)
                    if(r.status_code != rq.codes.ok):
                        time.sleep(1.0)
                        r = rq.get(url = URL, params = PARAMS)
                    tree = ElementTree.fromstring(r.text)
                    cnt = int(tree.find("Count").text)
                    two_term_dict[onetwokey] = cnt
                else:
                    cnt = two_term_dict[onetwokey]
                comention_counts_1_2.append(cnt)
                comention_counts_1_2_link.append(f"{str(cnt)} <a href='https://pubmed.ncbi.nlm.nih.gov/?term={term1} AND {term2}' target='_blank' rel='noopener noreferrer'>[Link]</a>")

            if f"{Term1}-{Term3} counts" or f"{Term3}-{Term1} counts" not in dff.columns:
                if onethreekey not in two_term_dict.keys():
                    PARAMS = {'db':'pubmed','term':term_1_3,'retmax':'0','api_key':'0595c1cc493e78f5a76d62b9f0cdc845e309'}
                    time.sleep(0.1)
                    r = rq.get(url = URL, params = PARAMS)
                    if(r.status_code != rq.codes.ok):
                        time.sleep(1.0)
                        r = rq.get(url = URL, params = PARAMS)
                    tree = ElementTree.fromstring(r.text)
                    cnt = int(tree.find("Count").text)
                    two_term_dict[onethreekey] = cnt
                else:
                    cnt = two_term_dict[onethreekey]
                comention_counts_1_3.append(cnt)
                comention_counts_1_3_link.append(f"{str(cnt)} <a href='https://pubmed.ncbi.nlm.nih.gov/?term={term1} AND {term3}' target='_blank' rel='noopener noreferrer'>[Link]</a>")
            
            if f"{Term2}-{Term3} counts" or f"{Term3}-{Term2} counts"  not in dff.columns:
                if twothreekey not in two_term_dict.keys():
                    PARAMS = {'db':'pubmed','term':term_2_3,'retmax':'0','api_key':'0595c1cc493e78f5a76d62b9f0cdc845e309'}
                    time.sleep(0.1)
                    r = rq.get(url = URL, params = PARAMS)
                    if(r.status_code != rq.codes.ok):
                        time.sleep(1.0)
                        r = rq.get(url = URL, params = PARAMS)
                    tree = ElementTree.fromstring(r.text)
                    cnt = int(tree.find("Count").text)
                    two_term_dict[twothreekey] = cnt
                else:
                    cnt = two_term_dict[twothreekey]
                comention_counts_2_3.append(cnt)
                comention_counts_2_3_link.append(f"{str(cnt)} <a href='https://pubmed.ncbi.nlm.nih.gov/?term={term2} AND {term3}' target='_blank' rel='noopener noreferrer'>[Link]</a>")
            
            if f"{Term1}-{Term2}-{Term3} counts" or f"{Term1}-{Term3}-{Term2} counts" not in dff.columns:
                if f"{Term2}-{Term1}-{Term3} counts" or f"{Term2}-{Term3}-{Term1} counts" not in dff.columns:
                    if f"{Term3}-{Term1}-{Term2} counts" or f"{Term3}-{Term2}-{Term1} counts" not in dff.columns:
                        if onetwothreekey not in three_term_dict.keys():
                            PARAMS = {'db':'pubmed','term':term_1_2_3,'retmax':'0','api_key':'0595c1cc493e78f5a76d62b9f0cdc845e309'}
                            time.sleep(0.1)
                            r = rq.get(url = URL, params = PARAMS)
                            if(r.status_code != rq.codes.ok):
                                time.sleep(1.0)
                                r = rq.get(url = URL, params = PARAMS)
                            tree = ElementTree.fromstring(r.text)
                            cnt = int(tree.find("Count").text)
                            three_term_dict[onetwothreekey] = cnt
                            print(f"{term1}-{term2}-{term3}")
                        else:
                            cnt = three_term_dict[onetwothreekey]
                        comention_counts_1_2_3.append(cnt)
                        comention_counts_1_2_3_link.append(f"{str(cnt)} <a href=\"https://pubmed.ncbi.nlm.nih.gov/?term={term1} AND {term2} AND {term3}\" target=\"_blank\" rel=\"noopener noreferrer\">[Link]</a>")
            
        if f"{Term1}-{Term2} counts" or f"{Term2}-{Term1} counts"not in dff.columns:
            dff.insert(0, f"{Term1}-{Term2} counts", comention_counts_1_2)
        if f"{Term1}-{Term2} link" or f"{Term2}-{Term1} link"not in dff.columns:
            dff.insert(0, f"{Term1}-{Term2} link", comention_counts_1_2_link)
        if f"{Term1}-{Term3} counts" or f"{Term3}-{Term1} counts" not in dff.columns:
            dff.insert(0, f"{Term1}-{Term3} counts", comention_counts_1_3)
        if f"{Term1}-{Term3} link" or f"{Term3}-{Term1} link" not in dff.columns:
            dff.insert(0, f"{Term1}-{Term3} link", comention_counts_1_3_link)
        if f"{Term2}-{Term3} counts" or f"{Term3}-{Term2} counts" not in dff.columns:
            dff.insert(0, f"{Term2}-{Term3} counts", comention_counts_2_3)
        if f"{Term2}-{Term3} link" or f"{Term3}-{Term2} link"not in dff.columns:
            dff.insert(0, f"{Term2}-{Term3} link", comention_counts_2_3_link)
        if f"{Term1}-{Term2}-{Term3} counts" or f"{Term1}-{Term3}-{Term2} counts" not in dff.columns:
            if f"{Term2}-{Term1}-{Term3} counts" or f"{Term2}-{Term3}-{Term1} counts" not in dff.columns:
                if f"{Term3}-{Term1}-{Term2} counts" or f"{Term3}-{Term2}-{Term1} counts" not in dff.columns:
                    dff.insert(0, f"{Term1}-{Term2}-{Term3} counts", comention_counts_1_2_3)
        if f"{Term1}-{Term2}-{Term3} link" or f"{Term1}-{Term3}-{Term2} link" not in dff.columns:
            if f"{Term2}-{Term1}-{Term3} link" or f"{Term2}-{Term3}-{Term1} link" not in dff.columns:
                if f"{Term3}-{Term1}-{Term2} link" or f"{Term3}-{Term2}-{Term1} link" not in dff.columns:
                    dff.insert(0, f"{Term1}-{Term2}-{Term3} link", comention_counts_1_2_3_link)

    ammended_answers = dff.to_dict('records')
    ammended_columns = [{"name": i.replace("`","").replace("biolink:",""), "id": i, "hideable":True, "selectable": False, "presentation":"markdown"} if " link" in i else {"name": i.replace("`","").replace("biolink:",""), "id": i, "hideable": True, "selectable": [True if "node" in i and " counts" not in i else False]} for i in dff.columns]
    hidden_columns=[i for i in dff.columns if " link" in i]+[i for i in dff.columns if "esnd" in i]

    message = "Finished retrieving PubMed Abstract Co-Mentions!"

    return (ammended_answers, ammended_columns, hidden_columns, message)