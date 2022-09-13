
import pandas as pd

def GetProteinNames(dff):
    gene_cols = [col for col in dff.columns if ":Gene" in col]
    #print(dff.columns)
    if len(gene_cols) == 0: return dff.to_dict('records'), [{"name": i, "id": i, "hideable": True, "selectable": [True if "node" in i else False]} for i in dff.columns], "No \"Gene\" column detected."

    genes = dict()
    proteins = list()
    #protname_df = pd.read_csv("hgnc_complete_set.csv", encoding="utf-8")
    protname_df = pd.read_csv("hgnc_complete_set.csv", encoding="utf-8")
    print("Read HGNC protein names!")

    for col in gene_cols:
        genes[col] = dff[col].tolist() 
    for col_x in genes:
        print(col_x)
        proteins = list()
        failed_proteins = list()
        for gene in genes[col_x]:
            try:
                i = protname_df[protname_df['symbol']==gene.upper()].index.values
                #print(str(i) + " is the index")
                index = int(i[0])
                protein = protname_df.at[index, 'name']
                proteins.append(protein)
                print(gene + " maps to " + protein)

            except:
                if gene == "Ins1":
                    proteins.append("insulin 1 (rodent)")
                    #print(gene + " maps to " + "insulin 1 (rodent)")
                else:
                    proteins.append('FAILED')
                    failed_proteins.append(gene)
                    print(f"Could not map gene symbol:{gene}")

        loc = dff.columns.get_loc(col_x)
        dff.insert(loc+1, col_x+' protein names', proteins)
        #print(dff.columns)

    ammended_answers = dff.to_dict('records')
    ammended_columns = [{"name": i.replace("`","").replace("biolink:",""), "id": i, "hideable": True, "selectable": [True if "node" in i else False]} for i in dff.columns]
    if len(failed_proteins) != 0:
        fails = ''.join([str(x)+", " for x in failed_proteins])
        message = f"Finished retrieving protein names!\nFailed on {fails.rstrip(', ')}."
    else:
        message = "Finished retrieving protein names!"
    hidden_columns=[i for i in dff.columns if " link" in i]+[i for i in dff.columns if "esnd" in i]
    return ammended_answers, ammended_columns, hidden_columns, message
