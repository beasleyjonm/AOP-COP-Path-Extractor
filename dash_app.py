#from os import sendfile
import pandas as pd
import py2neo
import dash
from dash import dcc
from dash import html
from dash import Dash, dash_table
import dash_daq as daq
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import numpy as np
from dash.dependencies import Output, Input, State
import requests as rq
import xml.etree.cElementTree as ElementTree
import time
from networkx.drawing.nx_pydot import graphviz_layout
from Neo4jSearch import Graphsearch
from Neo4jSearch import getNodeAndEdgeLabels
from Neo4jSearch import checkNodeNameID
import VisualizePaths
from VisualizePaths import VisualizeAnswerRow
from PubMedSearch import PubMedCoMentions
from HGNCProteinNames import GetProteinNames
from RandomForest import RandomForestClassifierTrain
import io
import base64
import PCA


app = dash.Dash()
app.title = 'ExEmPLAR'
app._favicon = 'LogoMML.ico'
app.css.append_css({'external_url': '/assets/styles.css'})

colors = {
    'background': 'white',
    #'background': '#7794B8',
    'dropdown': '#6c6f73',
    'text': '#000000'
}

#rk_nodes_and_edges=getNodeAndEdgeLabels('ROBOKOP')
# rk_nodes=rk_nodes_and_edges[0]
# rk_edges=rk_nodes_and_edges[1]

#Define dcc.Dropdown components used:
kg_dropdown = dcc.Dropdown(
                    id="kg-dropdown",
                    options=[
                    {'label':"ROBOKOP", 'value':"ROBOKOP"},
                    {'label':"SCENT-KOP", 'value':"SCENT-KOP"},
                    {'label':"HetioNet", 'value':"HetioNet"},
                    {'label':"ComptoxAI", 'value':"ComptoxAI"}],
                    value="ROBOKOP",
                    className='dropdownbox',
                    clearable=False)

source_dropdown = dcc.Dropdown(
                    id="source-dropdown",
                    options=[],#{'label':x.replace("biolink:",""), 'value':x} for x in rk_nodes],
                    value="biolink:ChemicalEntity",
                    className='dropdownbox',
                    placeholder='Select Node Type...',
                    clearable=False)

tail_dropdown = dcc.Dropdown(
                    id="tail-dropdown",
                    options=[],#{'label':x.replace("biolink:",""), 'value':x} for x in rk_nodes],
                    value="biolink:DiseaseOrPhenotypicFeature",
                    className='dropdownbox',
                    placeholder='Select Node Type...',
                    clearable=False)

node_drop = dcc.Dropdown(
                    id="node-dropdown",
                    options=[],#{'label':x.replace("biolink:",""), 'value':x} for x in rk_nodes],
                    className='dropdownbox',
                    multi=False
)

#Adds a numeric selector which makes or removes new query patterns to add to selector list.
pattern_select = daq.NumericInput(id="pattern-select",min=1,max=10,value=1,label="Number of Query Patterns") 

#Makes the text input box to name the individual query patterns.
#Default query pattern names are P1, P2, ... Pn.
pattern_name_boxes=[]
for i in range(1,11):
    pattern_name = dcc.Input(
        id="pattern-name-{}".format(i),
        type="text",
        placeholder='P{}'.format(i),
        value='P{}'.format(i),
        style={'width':'7em'})
    pattern_name_boxes.append(pattern_name)

#Make the selection button that determines globally whether or not edges can be specificied.
#Turning on edge selection still allows wildcard searching.
edge_checkbox = dcc.Checklist(id="edge-checkbox",style={'width': '10em'}, options=[{"label":"Use Edges","value":"True"}],value=[])
metadata_checkbox = dcc.Checklist(id="metadata-checkbox",style={'width': '10em'}, options=[{"label":"Get Result MetaData","value":True}],value=[])

#Make the 5 divs containing the node drop down. These also contain
# a bold header saying "Level k-1:". These need to be in seperate
# divs so they can easily be hidden and unhidden when k-val is changed.
all_k_drops = []
for i in range(1,11):
    k_drop = []
    for k in range(1,6):
        edge_drop = html.Div([
            dcc.Dropdown(
            id="edge-dropdown-{}".format(str(i)+"-"+str(k)),
                options=[
                    #{'label':x, 'value':x} for x in rk_edges 
                ],
            placeholder='Select Edge Type...',
            multi=False
            )],
            id="edge-div-{}".format(str(i)+"-"+str(k)),
            className='dropdownbox',
            style={'display':'None'}
        )
        node_options = html.Div([
            dcc.Textarea(
                id="node-options-{}".format(str(i)+"-"+str(k)),
                value="",
                placeholder="Leave blank for *any*...",
                className='nodeOptions'
            )],
            id="node-options-div-{}".format(str(i)+"-"+str(k))
            #style={'display':'None'}
        )
        drop = html.Div([
                html.B(children='Level %i:'%k),
                edge_drop,
                dcc.Dropdown(
                    id="node-dropdown-{}".format(str(i)+"-"+str(k)),
                        options=[
                            #{'label':x, 'value':x} for x in rk_nodes 
                        ],
                    placeholder='Select Node Type...',
                    multi=False
                ),
                node_options
            ],
            id="node-div-{}".format(str(i)+"-"+str(k)),
            className='dropdownbox',
            style={'display':('block' if k<3 else 'None')}
        )
        k_drop.append(drop)
    all_k_drops.append(k_drop)
print(len(all_k_drops))
edge_drop = dcc.Dropdown(
    id="edge-dropdown",
   options=[
       #{'label':x, 'value':x} for x in rk_edges 
   ],
   multi=False,
   className='dropdownbox',
   style={'display':'None'}
)

tail_edge = dcc.Dropdown(
    id="tail-edge",
   options=[
       #{'label':x, 'value':x} for x in rk_edges 
   ],
   multi=False,
   className='dropdownbox',
   placeholder='Select Edge Type...',
   style={'display':'None'}
)


all_k_selects = []
for i in range(1,11):
    k_select = daq.NumericInput(
       id="k-select-%i" % i ,
       min=0,
       max=5,
       value=2
    ) 
    all_k_selects.append(k_select)
print(len(all_k_selects))
starts = html.Div([
    html.Div(html.B(children='Starting Points:')),
    dcc.Textarea(
        id='starts',
        value=
'''ADUCANUMAB
Donepezil
Galantamine
Epicriptine
Acetyl-L-carnitine
Ipidacrine
Memantine
Rivastigmine
Tacrine
Raloxifene
Cadmium
Aluminum
Copper
pesticide
Perfluorooctanoic acid
Diphenhydramine
Chlorpheniramine
Cetirizine
Lorazepam
Diazepam
Temazepam
Clonazepam
Benztropine
Tolterodine
Dicyclomine
Fluoxetine
Sertraline
Citalopram
Escitalopram
Levodopa 
Amantadine
Tolcapone
Warfarin
Atenolol
Metoprolol
Busulfan
Cytarabine
Prednisone
Cortisone acetate
Methylprednisolone
Oxycodone
Morphine 
Codeine
Pentobarbital
Mephobarbital
Atorvastatin
Simvastatin
Rosuvastatin
''', #Causitive drugs taken from: https://www.brightfocus.org/alzheimers/article/is-it-something-im-taking-medications-that-can-mimic-dementia
        placeholder="Leave blank to include *any* start entities...",
        className='searchTerms'
)])

ends = html.Div([
    html.Div(html.B(children='Ending Points:\n')),
    dcc.Textarea(
        id='ends',
        value='''Alzheimer disease''',
        placeholder="Leave blank to include *any* end entities...",
        className='searchTerms'
    )])

#Create buttons to submit ROBOKOP search, get protein names, save settings, and calculate DWPC.
submit_button = html.Button('Submit', id='submit-val', n_clicks=0)#, style={"margin-right": "1em"})
protein_names_button = html.Button('Get Protein Names', id='submit-protein-names', n_clicks=0, style={"display":'None'})
triangulator_button = html.Button('Get PubMed Abstract Co-Mentions', id='submit-triangulator-val', n_clicks=0, style={"display":'None'})
dwpc_button = html.Button('Compute Degree-Weighted Path Counts', id='submit-dwpc-val', n_clicks=0, style={"display":'None'})
dwpc_weight = dcc.Input(id="dwpc-weight-select",
                        value=0,
                        type='number',
                        min=0,
                        max=1,
                        step=0.01,
                        placeholder="Weight",
                        style={'display':'None'})

#Adds a button to check whether names entered into Start and End are matched with search terms in ROBOKOP 
#and a markdown component to display terms that dont match
start_term_map_button = html.Button('Check for Terms in Knowledge Graph', id='start-term-map-val', n_clicks=0)
end_term_map_button = html.Button('Check for Terms in Knowledge Graph', id='end-term-map-val', n_clicks=0)

start_map_output = html.Div([
    html.Div(html.B(children="'Start' Search Results\n")),
    dcc.Textarea(
        id='start-map-output',
        className='searchTerms',
    )],
    id='start-map-div',style={'display': 'None'})

end_map_output = html.Div([
    html.Div(html.B(children="'End' Search Results\n")),
    dcc.Textarea(
        id='end-map-output',
        className='searchTerms',
    )],
    id='end-map-div',style={'display': 'None'})

# download_settings = html.Div([
#                         html.Button("Save Settings", id="btn_csv"),
#                         dcc.Input(id="settings_name",type='text',placeholder="Settings Filename"),
#                         dcc.Download(id="download-dataframe-csv")])
save_settings = html.Div([
                        html.Div([
                            html.Button("Save Settings", id="btn_csv"),
                            dcc.Input(id="settings_name",type='text',placeholder="Settings Filename"),
                            dcc.Download(id="download-dataframe-csv")]),
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select'), " Settings File"]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '3px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px'})   
                    ],
                        style={'display':'flex','flex-direction':'column','align-items':'center','justify-content':'center'})
all_node_edge_divs = []
for j in range(10):
    node_edge_div = html.Div([
        html.Td(all_k_drops[j][0],style={'width': '0em'}),
        html.Td(all_k_drops[j][1],style={'width': '0em'}),
        html.Td(all_k_drops[j][2],style={'width': '0em'}),
        html.Td(all_k_drops[j][3],style={'width': '0em'}),
        html.Td(all_k_drops[j][4],style={'width': '0em'})],
        #style={'width': '100em'},
        id="node-edge-div-%i" % (j+1))
    all_node_edge_divs.append(node_edge_div)
    
#Create tables for results
answer_table = html.Div(id='answer-table', style={'color': colors['text']})

#protein_names_answers = html.Div(id='protein-names-answers', style={'color': colors['text']})
dwpc_table = html.Div(id='dwpc-table', style={'color': colors['text']})

#create elements for PCA figures
pca_positives = html.Div([
html.Div(html.B(children='Type Positive Start and End Terms, separated by ":"')),
    dcc.Textarea(id='pca-positives',
        placeholder="Leave blank to perform unlabelled PCA...",
        className='searchTerms')],
        id='pos-search-box',
        style={"display":"None"})
pca_button = html.Button('Perform Principal Component Analysis', id='submit-pca-vis', n_clicks=0, style={"display":'None'})
pca_fig_2comp = dcc.Graph(id='pca-fig-2comp',className="scatterplot",style={'display':'None'})
pca_fig_3comp = dcc.Graph(id='pca-fig-3comp',className="scatterplot",style={'display':'None'})

randomforest_button = html.Button('Train Random Forest Classifier', id='submit-rf-train', n_clicks=0, style={"display":'None'})

#Create elements to visualize subgraphs
subgraph_fig = html.Img(id='subgraph-fig')
#cytoscape_fig = html.Div(id='cytoscape-fig', style={'width': '100%', 'height': '100%'})

#Display Random Forest Cross Validation Stats
rf_5FCV_fig = html.Img(id='rf-5FCV-fig', style={'width':'30%','height':'30%'})

#Create selector element to specify graph search queries.
selector = []
for j in range(10):
    select = html.Div(
        id='selector-%i' % (j+1),
        style={'display':('None' if j != 0 else 'block')},
        children=[
            html.Div(children=[
                html.Td(children=[html.Tr(children='Pattern Name:'),pattern_name_boxes[j]], style={'padding-right':'1em','vertical-align':'top'}),
                html.Td(children=[html.Tr(children='Length:'),all_k_selects[j]], style={'vertical-align':'top'})],
                style={'display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'}),   
            html.Td(children=[all_node_edge_divs[j]],
                style={'display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'})
            ])
    
    selector.append(select)

load =  dcc.Loading(
    id="loading-1",
    type="default",
    color=colors['text'],
    children=html.Div(id="loading-output-1")
)

load_start =  dcc.Loading(
    id="loading-start",
    type="default",
    color=colors['text'],
    children=html.Div(id="loading-output-start")
)

load_end =  dcc.Loading(
    id="loading-end",
    type="default",
    color=colors['text'],
    children=html.Div(id="loading-output-end")
)

load_3 =  dcc.Loading(
    id="loading-3",
    type="default",
    color=colors['text'],
    children=html.Div(id="loading-output-3")
)

load_4 =  dcc.Loading(
    id="loading-4",
    type="default",
    color=colors['text'],
    children=html.Div(id="loading-output-4")
)

load_5 =  dcc.Loading(
    id="loading-5",
    type="default",
    color=colors['text'],
    children=html.Div(id="loading-output-5")
)

row1 = html.Tr([
    html.Td(starts), 
    html.Td(ends),
    html.Div(submit_button),
    html.Td(load),
    answer_table
    #protein_names_answers
])
row0 = html.Tr(selector)
tbody = html.Tbody([row0, row1])
table = html.Table(tbody, style={'color': colors['text']})

# html.Td([html.Tr(html.B(children='To begin:')),
        #         html.Tr(children='(1) Select a biomedical knowledge graph source.'),
        #         html.Tr(children='(2) Choose category of Starting and Ending nodes for pathway.'),
        #         html.Tr(children='(3) Build a series of explanatory intermediates node and/or edge types between Start and End.'),
        #         html.Tr(children='(4) Type names of specific Start and End entities of interest.'),
        #         html.Tr(children='(5) Check these names for terms in the knowledge graph. Copy and paste suggested names if your supplied name is not found.'),
        #         html.Tr(children='(6) Hit "Submit" to retrieve all answer subgraph paths in tabular form.'),
        #         html.Tr(children='(7) If "Gene" nodes are present, you may retrieve HGNC-Approved protein names for all genes by clicking "Get Protein Names".'),
        #         html.Tr(children='(8) Queries often return numerous answer paths. To prioritize paths for deeper exploration, select any 2 or 3 node columns and click "Get PubMed Abstract Co-Mentions".'),
        #         html.Tr(children='This appends columns to the answer table which show the number of PubMed abstracts co-mentioning any term pairs or term triplets from your answer table.'),
        #         html.Tr(children='Typically, high co-mention counts between any pair or triplet of terms indicates strong support or attention for some relationship between co-mentioned terms.'),
        #         html.Tr(children='Each co-mention count cell has a link to PubMed to view these co-mentioning articles.'),
        #         html.Tr(children='(9) You can compute an embedding for each Start and End node pair based on the answer table. Each row in the answer table can be represented as a metapath,'),
        #         html.Tr(children='a pathway from Start to End following a particular sequence of node and edge types. A degree-weighted path count (DWPC) is then computed for each metapath for each Start and End pair (Himmelstein,D.S & Baranzini,S.E., 2015).'),
        #         html.Tr(children='To compute DWPC, change the "Weight" value then click "Submit DWPC".'),
        #         html.Tr(children='A Weight value of 0 returns absolute metapath counts, while higher values increasingly down-weight paths that pass through nodes with high edge-specific node degree (ESND)).')],
        #         style={'margin-left':'0'}),

app.layout = html.Div(style={'display':'flex','flex-direction':'column','align-items':'center','justify-content':'center','background-color': colors['background'], 'color': colors['text']}, 
    children=[
        html.H1(children=['ExEmPLAR!',html.Br(),html.Div('Extracting, Exploring and Embedding Pathways Leading to Actionable Research',style={'font-size':'20px'})],
            style={'padding-top':'1em','padding-bottom':'1em',"color":"white",'background-color':'rgb(10, 24, 53)','width':'100%'}),
        html.Div([

        
            html.Div(children=[
                        #html.Tr(children=['(1) Select a biomedical knowledge graph source.']),
                        html.H1(children='Knowledge Graph:'),
                        kg_dropdown],
                        style={'padding-bottom':'1em','width':'20em','display':'flex','flex-direction':'column','align-items':'center','justify-content':'center'}),
            html.Div(children=[
                        html.Td(children=[pattern_select]),
                        html.Td(edge_checkbox, style={'vertical-align':'bottom'}),
                        html.Td(metadata_checkbox, style={'vertical-align':'bottom'})],
                        style={'display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'})],
            style={'background-color':'whitesmoke','display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'}),

        html.Div(style={'padding-bottom':'3em','vertical-align':'top'},
            children=[
                # html.Div(children=[
                #         html.Td(children=[pattern_select]),
                #         html.Td(edge_checkbox, style={'vertical-align':'bottom'}),
                #         html.Td(metadata_checkbox, style={'vertical-align':'bottom'})],
                #         style={'display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'}),
                # html.Div(children=['(2) Build a series of explanatory intermediates node and/or edge types between Start and End nodes.'],
                #     style={'padding-top':'1em','display':'flex','flex-direction':'column','align-items':'center','justify-content':'center'}),
                html.Td(children=[
                    html.H1(children='Start Node:'),
                    source_dropdown,
                    html.Div([
                        start_map_output,
                        starts],
                        style={'display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'}),
                    # starts,
                    # start_map_output,
                    load_start,
                    start_term_map_button],
                    style={'width':'15em'}),
                html.Td(children=[
                    html.Div(children=selector, style={'padding': '1em'})
                ]),
                html.Td(children=[
                    html.H1(children='End Node:'),
                    tail_edge,
                    tail_dropdown,
                    html.Div([
                        ends,
                        end_map_output],
                        style={'display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'}),
                    # ends,
                    # end_map_output,
                    load_end,
                    end_term_map_button],
                    style={'width':'15em'})
            ]),

            # html.Tr(children='(3) Build a series of explanatory intermediates node and/or edge types between Start and End.'),

            # html.Div(children=selector, style={'padding-bottom': '3em','padding-top': '1em'}),

            #html.Tr(children='(4) Type names of specific Start and End entities of interest.'),

            # html.Div([html.Td(starts),
            #         html.Td(ends),
            #         html.Td(start_map_output),html.Td(end_map_output)], 
            #         style={'padding-top': '1em'}),
                
        html.Div([load,submit_button, save_settings,
            dbc.Tooltip(
            "Check Start and End node names for corresponding terms in the knowledge graph. \
            Copy and paste suggested names if your supplied name is not found.",
            target="term-map-val",
            style={"padding":"1em","background-color":"slategray", "border-radius":"10px", "color": "white", "width":"10%"},
            placement="bottom",
            delay={"show":200,"hide":300}
        )], style={'padding':'2em','display':'flex','flex-direction':'column','align-items':'center','justify-content':'center', 'padding-bottom': '1em','background-color':'whitesmoke','border-style':'outset'}),

        html.Div([#html.Tr([
            html.Tr([protein_names_button,triangulator_button,load_4,#dwpc_button, dwpc_weight, load_3,
                dbc.Tooltip( #For protein-names button
                    "If \"Gene\" nodes are present, you may retrieve HGNC-Approved protein names for all genes.",
                    target="submit-protein-names",
                    style={"padding":"1em","background-color":"slategray", "border-radius":"10px", "color": "white", "width":"10%"},
                    placement="bottom",
                    delay={"show":200,"hide":300}),
                dbc.Tooltip( #For PubMed comentions button.
                    "Queries often return numerous answer paths. To prioritize paths for deeper exploration, select any 2 or 3 node columns and click \"Get PubMed Abstract Co-Mentions\". \
                    This appends columns to the answer table which show the number of PubMed abstracts co-mentioning any term pairs or term triplets from your answer table. \
                    Links to these PubMed abstracts can be found in hidden columns under \"Toggle Columns\".",
                    target="submit-triangulator-val",
                    style={"padding":"1em","background-color":"slategray", "border-radius":"10px", "color": "white", "width":"10%"},
                    placement="bottom",
                    delay={"show":200,"hide":300}),
            ],
                    style={'display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'}), 

            html.Div([answer_table,subgraph_fig],style={"vertical-align":"top",'display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'}),

            #html.Div(cytoscape_fig),

            html.Tr([dwpc_button, dwpc_weight, load_3,
                dbc.Tooltip( #For degree-weight path counts button.
                        "Compute an embedding for each Start and End node pair based on the answer table. Each pair can be represented as a set of metapaths, \
                        a pathway from Start to End following a particular sequence of node and edge types. A degree-weighted path count (DWPC) is then computed for each metapath for each Start and End pair. \
                        A Weight value of 0 returns absolute metapath counts, while higher values increasingly down-weight paths that pass through nodes with high edge-specific node degree (ESND). (Himmelstein,D.S & Baranzini,S.E., 2015)",
                        target="submit-dwpc-val",
                        style={"padding":"1em","background-color":"slategray", "border-radius":"10px", "color": "white", "width":"10%"},
                        placement="bottom",
                        delay={"show":200,"hide":300})],
                style={'display':'flex','flex-direction':'column','align-items':'center','justify-content':'center'})],

            style={'display':'flex','flex-direction':'column','align-items':'center','justify-content':'center'}),

        #html.Div(html.Tr(subgraph_fig,style={"vertical-align":"top",'height':'100%'})),

        # html.Div([
        #     html.Tr(answer_table,style={"vertical-align":"top"}),
        #     html.Tr(subgraph_fig,style={"vertical-align":"top",'height':'100%'})
        # ],
        #     style={'minWidth':'60%', 'width':'60%', 'maxWidth':'60%'}),

        #html.Div([html.Td(protein_names_button), html.Td(triangulator_button),html.Td(load_4)]),
        
        #html.Div([html.Td(dwpc_button),html.Td(dwpc_weight),html.Td(load_3)],style={'padding-bottom': '3em'}),
    
        html.Div(dwpc_table, style={'padding-bottom':'1em','display':'flex','flex-direction':'column','align-items':'center','justify-content':'center'}),#style={'width': '120em','padding-bottom':'1em'}),

        html.Div([html.Td(pca_positives),html.Td([pca_button, randomforest_button],style={'display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'}),load_5
        # dbc.Tooltip( #For degree-weight path counts button.
        #     "You can compute an embedding for each Start and End node pair based on the answer table. Each row in the answer table can be represented as a metapath, \
        #     a pathway from Start to End following a particular sequence of node and edge types. A degree-weighted path count (DWPC) is then computed for each metapath for each Start and End pair. \
        #     Degree-weighting factor can be adjusted below (default=0, no degree weighting). (Himmelstein,D.S & Baranzini,S.E., 2015)",
        #     target="submit-dwpc-val",
        #     style={"background-color":"white", "border-style":"solid", "border-color": "black", "width":"10%"},
        #     placement="bottom",
        #     delay={"show":200,"hide":300})
        ], style={'padding-bottom':'1em','display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'}),
        
        html.Div(pca_fig_2comp),

        html.Div(pca_fig_3comp),

        html.Div(rf_5FCV_fig,style={'display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'})
    ])

selected_nodes = []
selected_edges = []

def checkToBool(show_edge):
    if(len(show_edge)==1): return True
    else: return False
    
@app.callback(Output("source-dropdown",'value'),Output("source-dropdown",'options'),Output("tail-dropdown",'value'),Output("tail-dropdown",'options'),
    Output("node-dropdown-1-1",'options'),Output("node-dropdown-1-2",'options'),Output("node-dropdown-1-3",'options'),Output("node-dropdown-1-4",'options'),Output("node-dropdown-1-5",'options'),
    Output("node-dropdown-2-1",'options'),Output("node-dropdown-2-2",'options'),Output("node-dropdown-2-3",'options'),Output("node-dropdown-2-4",'options'),Output("node-dropdown-2-5",'options'),
    Output("node-dropdown-3-1",'options'),Output("node-dropdown-3-2",'options'),Output("node-dropdown-3-3",'options'),Output("node-dropdown-3-4",'options'),Output("node-dropdown-3-5",'options'),
    Output("node-dropdown-4-1",'options'),Output("node-dropdown-4-2",'options'),Output("node-dropdown-4-3",'options'),Output("node-dropdown-4-4",'options'),Output("node-dropdown-4-5",'options'),
    Output("node-dropdown-5-1",'options'),Output("node-dropdown-5-2",'options'),Output("node-dropdown-5-3",'options'),Output("node-dropdown-5-4",'options'),Output("node-dropdown-5-5",'options'),
    Output("node-dropdown-6-1",'options'),Output("node-dropdown-6-2",'options'),Output("node-dropdown-6-3",'options'),Output("node-dropdown-6-4",'options'),Output("node-dropdown-6-5",'options'),
    Output("node-dropdown-7-1",'options'),Output("node-dropdown-7-2",'options'),Output("node-dropdown-7-3",'options'),Output("node-dropdown-7-4",'options'),Output("node-dropdown-7-5",'options'),
    Output("node-dropdown-8-1",'options'),Output("node-dropdown-8-2",'options'),Output("node-dropdown-8-3",'options'),Output("node-dropdown-8-4",'options'),Output("node-dropdown-8-5",'options'),
    Output("node-dropdown-9-1",'options'),Output("node-dropdown-9-2",'options'),Output("node-dropdown-9-3",'options'),Output("node-dropdown-9-4",'options'),Output("node-dropdown-9-5",'options'),
    Output("node-dropdown-10-1",'options'),Output("node-dropdown-10-2",'options'),Output("node-dropdown-10-3",'options'),Output("node-dropdown-10-4",'options'),Output("node-dropdown-10-5",'options'),
    Output("edge-dropdown-1-1",'options'),Output("edge-dropdown-1-2",'options'),Output("edge-dropdown-1-3",'options'),Output("edge-dropdown-1-4",'options'),Output("edge-dropdown-1-5",'options'),
    Output("edge-dropdown-2-1",'options'),Output("edge-dropdown-2-2",'options'),Output("edge-dropdown-2-3",'options'),Output("edge-dropdown-2-4",'options'),Output("edge-dropdown-2-5",'options'),
    Output("edge-dropdown-3-1",'options'),Output("edge-dropdown-3-2",'options'),Output("edge-dropdown-3-3",'options'),Output("edge-dropdown-3-4",'options'),Output("edge-dropdown-3-5",'options'),
    Output("edge-dropdown-4-1",'options'),Output("edge-dropdown-4-2",'options'),Output("edge-dropdown-4-3",'options'),Output("edge-dropdown-4-4",'options'),Output("edge-dropdown-4-5",'options'),
    Output("edge-dropdown-5-1",'options'),Output("edge-dropdown-5-2",'options'),Output("edge-dropdown-5-3",'options'),Output("edge-dropdown-5-4",'options'),Output("edge-dropdown-5-5",'options'),
    Output("edge-dropdown-6-1",'options'),Output("edge-dropdown-6-2",'options'),Output("edge-dropdown-6-3",'options'),Output("edge-dropdown-6-4",'options'),Output("edge-dropdown-6-5",'options'),
    Output("edge-dropdown-7-1",'options'),Output("edge-dropdown-7-2",'options'),Output("edge-dropdown-7-3",'options'),Output("edge-dropdown-7-4",'options'),Output("edge-dropdown-7-5",'options'),
    Output("edge-dropdown-8-1",'options'),Output("edge-dropdown-8-2",'options'),Output("edge-dropdown-8-3",'options'),Output("edge-dropdown-8-4",'options'),Output("edge-dropdown-8-5",'options'),
    Output("edge-dropdown-9-1",'options'),Output("edge-dropdown-9-2",'options'),Output("edge-dropdown-9-3",'options'),Output("edge-dropdown-9-4",'options'),Output("edge-dropdown-9-5",'options'),
    Output("edge-dropdown-10-1",'options'),Output("edge-dropdown-10-2",'options'),Output("edge-dropdown-10-3",'options'),Output("edge-dropdown-10-4",'options'),Output("edge-dropdown-10-5",'options'),
    Output("tail-edge",'options'), 
    Input("kg-dropdown", 'value')
)
def UpdateNodeAndEdgeLabels(graph_db):
    if graph_db == "ROBOKOP":
        starter = "biolink:ChemicalEntity"
        ender = "biolink:DiseaseOrPhenotypicFeature"
    elif graph_db == "HetioNet":
        starter = "Compound"
        ender = "Disease"
    elif graph_db == "SCENT-KOP":
        starter = "odorant"
        ender = "verbal_scent_descriptor"
    elif graph_db == "ComptoxAI":
        starter = "Chemical"
        ender = "Disease"
    rk_nodes_and_edges=getNodeAndEdgeLabels(graph_db)
    rk_nodes=rk_nodes_and_edges[0]
    rk_edges=rk_nodes_and_edges[1]
    #cmap = rk_nodes_and_edges[2]
    #print(cmap)
    node_options = [{'label':x.replace("biolink:",""), 'value':x} for x in rk_nodes]
    edge_options = [{'label':x.replace("biolink:",""), 'value':x} for x in rk_edges]

    return (starter, node_options,ender,
    node_options,node_options,node_options,node_options,
    node_options,node_options,node_options,node_options,
    node_options,node_options,node_options,node_options,
    node_options,node_options,node_options,node_options,
    node_options,node_options,node_options,node_options,
    node_options,node_options,node_options,node_options,
    node_options,node_options,node_options,node_options,
    node_options,node_options,node_options,node_options,
    node_options,node_options,node_options,node_options,
    node_options,node_options,node_options,node_options,
    node_options,node_options,node_options,node_options,
    node_options,node_options,node_options,node_options,
    node_options,node_options,node_options,
    edge_options,edge_options,edge_options,edge_options,
    edge_options,edge_options,edge_options,edge_options,
    edge_options,edge_options,edge_options,edge_options,
    edge_options,edge_options,edge_options,edge_options,
    edge_options,edge_options,edge_options,edge_options,
    edge_options,edge_options,edge_options,edge_options,
    edge_options,edge_options,edge_options,edge_options,
    edge_options,edge_options,edge_options,edge_options,
    edge_options,edge_options,edge_options,edge_options,
    edge_options,edge_options,edge_options,edge_options,
    edge_options,edge_options,edge_options,edge_options,
    edge_options,edge_options,edge_options,edge_options,
    edge_options,edge_options,edge_options)

@app.callback([Output("selector-1",'style'),Output("selector-2",'style'),Output("selector-3",'style'),Output("selector-4",'style'),Output("selector-5",'style'),
    Output("selector-6",'style'),Output("selector-7",'style'),Output("selector-8",'style'),Output("selector-9",'style'),Output("selector-10",'style')], 
    Input('pattern-select', 'value'),
    prevent_initial_call=True)
def hide_elements_p(p):
    pattern_1 = {'display':'block'} if p>=1 else {'display':'None'}
    pattern_2 = {'display':'block'} if p>=2 else {'display':'None'}
    pattern_3 = {'display':'block'} if p>=3 else {'display':'None'}
    pattern_4 = {'display':'block'} if p>=4 else {'display':'None'}
    pattern_5 = {'display':'block'} if p>=5 else {'display':'None'}
    pattern_6 = {'display':'block'} if p>=6 else {'display':'None'}
    pattern_7 = {'display':'block'} if p>=7 else {'display':'None'}
    pattern_8 = {'display':'block'} if p>=8 else {'display':'None'}
    pattern_9 = {'display':'block'} if p>=9 else {'display':'None'}
    pattern_10 = {'display':'block'} if p>=10 else {'display':'None'}

    return pattern_1,pattern_2,pattern_3,pattern_4,pattern_5,pattern_6,pattern_7,pattern_8,pattern_9,pattern_10

@app.callback([Output("node-div-1-1",'style'),Output("node-div-1-2",'style'),Output("node-div-1-3",'style'),Output("node-div-1-4",'style'),Output("node-div-1-5",'style'),
    Output("edge-div-1-1",'style'),Output("edge-div-1-2",'style'),Output("edge-div-1-3",'style'),Output("edge-div-1-4",'style'),Output("edge-div-1-5",'style')], 
    [Input("k-select-1", 'value'),Input("edge-checkbox", 'value')],
    prevent_initial_call=True)
def hide_elements_k1(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-2-1",'style'),Output("node-div-2-2",'style'),Output("node-div-2-3",'style'),Output("node-div-2-4",'style'),Output("node-div-2-5",'style'),
    Output("edge-div-2-1",'style'),Output("edge-div-2-2",'style'),Output("edge-div-2-3",'style'),Output("edge-div-2-4",'style'),Output("edge-div-2-5",'style')], 
    [Input("k-select-2", 'value'),Input("edge-checkbox", 'value')],
    prevent_initial_call=True)
def hide_elements_k2(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-3-1",'style'),Output("node-div-3-2",'style'),Output("node-div-3-3",'style'),Output("node-div-3-4",'style'),Output("node-div-3-5",'style'),
    Output("edge-div-3-1",'style'),Output("edge-div-3-2",'style'),Output("edge-div-3-3",'style'),Output("edge-div-3-4",'style'),Output("edge-div-3-5",'style')], 
    [Input("k-select-3", 'value'),Input("edge-checkbox", 'value')],
    prevent_initial_call=True)
def hide_elements_k3(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-4-1",'style'),Output("node-div-4-2",'style'),Output("node-div-4-3",'style'),Output("node-div-4-4",'style'),Output("node-div-4-5",'style'),
    Output("edge-div-4-1",'style'),Output("edge-div-4-2",'style'),Output("edge-div-4-3",'style'),Output("edge-div-4-4",'style'),Output("edge-div-4-5",'style')], 
    [Input("k-select-4", 'value'),Input("edge-checkbox", 'value')],
    prevent_initial_call=True)
def hide_elements_k4(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-5-1",'style'),Output("node-div-5-2",'style'),Output("node-div-5-3",'style'),Output("node-div-5-4",'style'),Output("node-div-5-5",'style'),
    Output("edge-div-5-1",'style'),Output("edge-div-5-2",'style'),Output("edge-div-5-3",'style'),Output("edge-div-5-4",'style'),Output("edge-div-5-5",'style')], 
    [Input("k-select-5", 'value'),Input("edge-checkbox", 'value')],
    prevent_initial_call=True)
def hide_elements_k5(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-6-1",'style'),Output("node-div-6-2",'style'),Output("node-div-6-3",'style'),Output("node-div-6-4",'style'),Output("node-div-6-5",'style'),
    Output("edge-div-6-1",'style'),Output("edge-div-6-2",'style'),Output("edge-div-6-3",'style'),Output("edge-div-6-4",'style'),Output("edge-div-6-5",'style')], 
    [Input("k-select-6", 'value'),Input("edge-checkbox", 'value')],
    prevent_initial_call=True)
def hide_elements_k6(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-7-1",'style'),Output("node-div-7-2",'style'),Output("node-div-7-3",'style'),Output("node-div-7-4",'style'),Output("node-div-7-5",'style'),
    Output("edge-div-7-1",'style'),Output("edge-div-7-2",'style'),Output("edge-div-7-3",'style'),Output("edge-div-7-4",'style'),Output("edge-div-7-5",'style')], 
    [Input("k-select-7", 'value'),Input("edge-checkbox", 'value')],
    prevent_initial_call=True)
def hide_elements_k7(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-8-1",'style'),Output("node-div-8-2",'style'),Output("node-div-8-3",'style'),Output("node-div-8-4",'style'),Output("node-div-8-5",'style'),
    Output("edge-div-8-1",'style'),Output("edge-div-8-2",'style'),Output("edge-div-8-3",'style'),Output("edge-div-8-4",'style'),Output("edge-div-8-5",'style')], 
    [Input("k-select-8", 'value'),Input("edge-checkbox", 'value')],
    prevent_initial_call=True)
def hide_elements_k8(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-9-1",'style'),Output("node-div-9-2",'style'),Output("node-div-9-3",'style'),Output("node-div-9-4",'style'),Output("node-div-9-5",'style'),
    Output("edge-div-9-1",'style'),Output("edge-div-9-2",'style'),Output("edge-div-9-3",'style'),Output("edge-div-9-4",'style'),Output("edge-div-9-5",'style')], 
    [Input("k-select-9", 'value'),Input("edge-checkbox", 'value')],
    prevent_initial_call=True)
def hide_elements_k9(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-10-1",'style'),Output("node-div-10-2",'style'),Output("node-div-10-3",'style'),Output("node-div-10-4",'style'),Output("node-div-10-5",'style'),
    Output("edge-div-10-1",'style'),Output("edge-div-10-2",'style'),Output("edge-div-10-3",'style'),Output("edge-div-10-4",'style'),Output("edge-div-10-5",'style')], 
    [Input("k-select-10", 'value'),Input("edge-checkbox", 'value')],
    prevent_initial_call=True)
def hide_elements_k10(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback(
    Output("tail-edge", 'style'),
    Input("edge-checkbox", 'value'),
    prevent_initial_call=True
)
def hide_elements_edges(show_edge):
    show_edge = checkToBool(show_edge)
    tail_edge_style = {'display':'block'} if show_edge else {'display':'None'}

    return tail_edge_style

def processInputText(text):
    l1 = []
    for line in text.split('\n'):
        a = line
        if a != "":
            l1.append(a.strip())
    return l1

@app.callback(
    [Output('loading-1', 'children'),Output('answer-table', 'children'),Output('submit-dwpc-val', 'style'),Output('submit-protein-names', 'style'),Output('submit-triangulator-val', 'style'),Output('dwpc-weight-select', 'style')],
    [Input('submit-val', 'n_clicks')],
    [State("kg-dropdown", 'value'),State('starts', 'value'),State('ends','value'),State("source-dropdown", 'value'), State("tail-dropdown", 'value'), State('tail-edge','value'),
    State('edge-checkbox', 'value'),State('metadata-checkbox', 'value'),State('pattern-select', 'value'),

    State("node-dropdown-1-1", 'value'),State("node-dropdown-1-2", 'value'),State("node-dropdown-1-3", 'value'),State("node-dropdown-1-4", 'value'),State("node-dropdown-1-5", 'value'),
    State("node-options-1-1", 'value'),State("node-options-1-2", 'value'),State("node-options-1-3", 'value'),State("node-options-1-4", 'value'),State("node-options-1-5", 'value'),
    State("edge-dropdown-1-1", 'value'),State("edge-dropdown-1-2", 'value'),State("edge-dropdown-1-3", 'value'),State("edge-dropdown-1-4", 'value'),State("edge-dropdown-1-5", 'value'),

    State("node-dropdown-2-1", 'value'),State("node-dropdown-2-2", 'value'),State("node-dropdown-2-3", 'value'),State("node-dropdown-2-4", 'value'),State("node-dropdown-2-5", 'value'),
    State("node-options-2-1", 'value'),State("node-options-2-2", 'value'),State("node-options-2-3", 'value'),State("node-options-2-4", 'value'),State("node-options-2-5", 'value'),
    State("edge-dropdown-2-1", 'value'),State("edge-dropdown-2-2", 'value'),State("edge-dropdown-2-3", 'value'),State("edge-dropdown-2-4", 'value'),State("edge-dropdown-2-5", 'value'),
    
    State("node-dropdown-3-1", 'value'),State("node-dropdown-3-2", 'value'),State("node-dropdown-3-3", 'value'),State("node-dropdown-3-4", 'value'),State("node-dropdown-3-5", 'value'),
    State("node-options-3-1", 'value'),State("node-options-3-2", 'value'),State("node-options-3-3", 'value'),State("node-options-3-4", 'value'),State("node-options-3-5", 'value'),
    State("edge-dropdown-3-1", 'value'),State("edge-dropdown-3-2", 'value'),State("edge-dropdown-3-3", 'value'),State("edge-dropdown-3-4", 'value'),State("edge-dropdown-3-5", 'value'),

    State("node-dropdown-4-1", 'value'),State("node-dropdown-4-2", 'value'),State("node-dropdown-4-3", 'value'),State("node-dropdown-4-4", 'value'),State("node-dropdown-4-5", 'value'),
    State("node-options-4-1", 'value'),State("node-options-4-2", 'value'),State("node-options-4-3", 'value'),State("node-options-4-4", 'value'),State("node-options-4-5", 'value'),
    State("edge-dropdown-4-1", 'value'),State("edge-dropdown-4-2", 'value'),State("edge-dropdown-4-3", 'value'),State("edge-dropdown-4-4", 'value'),State("edge-dropdown-4-5", 'value'),
    
    State("node-dropdown-5-1", 'value'),State("node-dropdown-5-2", 'value'),State("node-dropdown-5-3", 'value'),State("node-dropdown-5-4", 'value'),State("node-dropdown-5-5", 'value'),
    State("node-options-5-1", 'value'),State("node-options-5-2", 'value'),State("node-options-5-3", 'value'),State("node-options-5-4", 'value'),State("node-options-5-5", 'value'),
    State("edge-dropdown-5-1", 'value'),State("edge-dropdown-5-2", 'value'),State("edge-dropdown-5-3", 'value'),State("edge-dropdown-5-4", 'value'),State("edge-dropdown-5-5", 'value'),

    State("node-dropdown-6-1", 'value'),State("node-dropdown-6-2", 'value'),State("node-dropdown-6-3", 'value'),State("node-dropdown-6-4", 'value'),State("node-dropdown-6-5", 'value'),
    State("node-options-6-1", 'value'),State("node-options-6-2", 'value'),State("node-options-6-3", 'value'),State("node-options-6-4", 'value'),State("node-options-6-5", 'value'),
    State("edge-dropdown-6-1", 'value'),State("edge-dropdown-6-2", 'value'),State("edge-dropdown-6-3", 'value'),State("edge-dropdown-6-4", 'value'),State("edge-dropdown-6-5", 'value'),

    State("node-dropdown-7-1", 'value'),State("node-dropdown-7-2", 'value'),State("node-dropdown-7-3", 'value'),State("node-dropdown-7-4", 'value'),State("node-dropdown-7-5", 'value'),
    State("node-options-7-1", 'value'),State("node-options-7-2", 'value'),State("node-options-7-3", 'value'),State("node-options-7-4", 'value'),State("node-options-7-5", 'value'),
    State("edge-dropdown-7-1", 'value'),State("edge-dropdown-7-2", 'value'),State("edge-dropdown-7-3", 'value'),State("edge-dropdown-7-4", 'value'),State("edge-dropdown-7-5", 'value'),

    State("node-dropdown-8-1", 'value'),State("node-dropdown-8-2", 'value'),State("node-dropdown-8-3", 'value'),State("node-dropdown-8-4", 'value'),State("node-dropdown-8-5", 'value'),
    State("node-options-8-1", 'value'),State("node-options-8-2", 'value'),State("node-options-8-3", 'value'),State("node-options-8-4", 'value'),State("node-options-8-5", 'value'),
    State("edge-dropdown-8-1", 'value'),State("edge-dropdown-8-2", 'value'),State("edge-dropdown-8-3", 'value'),State("edge-dropdown-8-4", 'value'),State("edge-dropdown-8-5", 'value'),

    State("node-dropdown-9-1", 'value'),State("node-dropdown-9-2", 'value'),State("node-dropdown-9-3", 'value'),State("node-dropdown-9-4", 'value'),State("node-dropdown-9-5", 'value'),
    State("node-options-9-1", 'value'),State("node-options-9-2", 'value'),State("node-options-9-3", 'value'),State("node-options-9-4", 'value'),State("node-options-9-5", 'value'),
    State("edge-dropdown-9-1", 'value'),State("edge-dropdown-9-2", 'value'),State("edge-dropdown-9-3", 'value'),State("edge-dropdown-9-4", 'value'),State("edge-dropdown-9-5", 'value'),

    State("node-dropdown-10-1", 'value'),State("node-dropdown-10-2", 'value'),State("node-dropdown-10-3", 'value'),State("node-dropdown-10-4", 'value'),State("node-dropdown-10-5", 'value'),
    State("node-options-10-1", 'value'),State("node-options-10-2", 'value'),State("node-options-10-3", 'value'),State("node-options-10-4", 'value'),State("node-options-10-5", 'value'),
    State("edge-dropdown-10-1", 'value'),State("edge-dropdown-10-2", 'value'),State("edge-dropdown-10-3", 'value'),State("edge-dropdown-10-4", 'value'),State("edge-dropdown-10-5", 'value'),

    State('k-select-1', 'value'),State('k-select-2', 'value'),State('k-select-3', 'value'),State('k-select-4', 'value'),State('k-select-5', 'value'),
    State('k-select-6', 'value'),State('k-select-7', 'value'),State('k-select-8', 'value'),State('k-select-9', 'value'),State('k-select-10', 'value'),
    State('pattern-name-1', 'value'),State('pattern-name-2', 'value'),State('pattern-name-3', 'value'),State('pattern-name-4', 'value'),State('pattern-name-5', 'value'),
    State('pattern-name-6', 'value'),State('pattern-name-7', 'value'),State('pattern-name-8', 'value'),State('pattern-name-9', 'value'),State('pattern-name-10', 'value')],
    prevent_initial_call=True)
def submit_path_search(n_clicks,graph_db,start_node_text,end_node_text,s,t,t_edges,show_edges,get_metadata,pattern_select,
        k1_1_nodes,k1_2_nodes,k1_3_nodes,k1_4_nodes,k1_5_nodes,k1_1_options,k1_2_options,k1_3_options,k1_4_options,k1_5_options,k1_1_edges,k1_2_edges,k1_3_edges,k1_4_edges,k1_5_edges,
        k2_1_nodes,k2_2_nodes,k2_3_nodes,k2_4_nodes,k2_5_nodes,k2_1_options,k2_2_options,k2_3_options,k2_4_options,k2_5_options,k2_1_edges,k2_2_edges,k2_3_edges,k2_4_edges,k2_5_edges,
        k3_1_nodes,k3_2_nodes,k3_3_nodes,k3_4_nodes,k3_5_nodes,k3_1_options,k3_2_options,k3_3_options,k3_4_options,k3_5_options,k3_1_edges,k3_2_edges,k3_3_edges,k3_4_edges,k3_5_edges,
        k4_1_nodes,k4_2_nodes,k4_3_nodes,k4_4_nodes,k4_5_nodes,k4_1_options,k4_2_options,k4_3_options,k4_4_options,k4_5_options,k4_1_edges,k4_2_edges,k4_3_edges,k4_4_edges,k4_5_edges,
        k5_1_nodes,k5_2_nodes,k5_3_nodes,k5_4_nodes,k5_5_nodes,k5_1_options,k5_2_options,k5_3_options,k5_4_options,k5_5_options,k5_1_edges,k5_2_edges,k5_3_edges,k5_4_edges,k5_5_edges,
        k6_1_nodes,k6_2_nodes,k6_3_nodes,k6_4_nodes,k6_5_nodes,k6_1_options,k6_2_options,k6_3_options,k6_4_options,k6_5_options,k6_1_edges,k6_2_edges,k6_3_edges,k6_4_edges,k6_5_edges,
        k7_1_nodes,k7_2_nodes,k7_3_nodes,k7_4_nodes,k7_5_nodes,k7_1_options,k7_2_options,k7_3_options,k7_4_options,k7_5_options,k7_1_edges,k7_2_edges,k7_3_edges,k7_4_edges,k7_5_edges,
        k8_1_nodes,k8_2_nodes,k8_3_nodes,k8_4_nodes,k8_5_nodes,k8_1_options,k8_2_options,k8_3_options,k8_4_options,k8_5_options,k8_1_edges,k8_2_edges,k8_3_edges,k8_4_edges,k8_5_edges,
        k9_1_nodes,k9_2_nodes,k9_3_nodes,k9_4_nodes,k9_5_nodes,k9_1_options,k9_2_options,k9_3_options,k9_4_options,k9_5_options,k9_1_edges,k9_2_edges,k9_3_edges,k9_4_edges,k9_5_edges,
        k10_1_nodes,k10_2_nodes,k10_3_nodes,k10_4_nodes,k10_5_nodes,k10_1_options,k10_2_options,k10_3_options,k10_4_options,k10_5_options,k10_1_edges,k10_2_edges,k10_3_edges,k10_4_edges,k10_5_edges,
        k_val_1,k_val_2,k_val_3,k_val_4,k_val_5,k_val_6,k_val_7,k_val_8,k_val_9,k_val_10,
        pattern_name_1,pattern_name_2,pattern_name_3,pattern_name_4,pattern_name_5,pattern_name_6,pattern_name_7,pattern_name_8,pattern_name_9,pattern_name_10):
    if(n_clicks <= 0): return ""
    print("Running PATH SEARCH!")
    all_k_nodes={
    pattern_name_1:[k1_1_nodes,k1_2_nodes,k1_3_nodes,k1_4_nodes,k1_5_nodes],
    pattern_name_2:[k2_1_nodes,k2_2_nodes,k2_3_nodes,k2_4_nodes,k2_5_nodes],
    pattern_name_3:[k3_1_nodes,k3_2_nodes,k3_3_nodes,k3_4_nodes,k3_5_nodes],
    pattern_name_4:[k4_1_nodes,k4_2_nodes,k4_3_nodes,k4_4_nodes,k4_5_nodes],
    pattern_name_5:[k5_1_nodes,k5_2_nodes,k5_3_nodes,k5_4_nodes,k5_5_nodes],
    pattern_name_6:[k6_1_nodes,k6_2_nodes,k6_3_nodes,k6_4_nodes,k6_5_nodes],
    pattern_name_7:[k7_1_nodes,k7_2_nodes,k7_3_nodes,k7_4_nodes,k7_5_nodes],
    pattern_name_8:[k8_1_nodes,k8_2_nodes,k8_3_nodes,k8_4_nodes,k8_5_nodes],
    pattern_name_9:[k9_1_nodes,k9_2_nodes,k9_3_nodes,k9_4_nodes,k9_5_nodes],
    pattern_name_10:[k10_1_nodes,k10_2_nodes,k10_3_nodes,k10_4_nodes,k10_5_nodes]
    }
    all_k_options={
    pattern_name_1:[k1_1_options,k1_2_options,k1_3_options,k1_4_options,k1_5_options],
    pattern_name_2:[k2_1_options,k2_2_options,k2_3_options,k2_4_options,k2_5_options],
    pattern_name_3:[k3_1_options,k3_2_options,k3_3_options,k3_4_options,k3_5_options],
    pattern_name_4:[k4_1_options,k4_2_options,k4_3_options,k4_4_options,k4_5_options],
    pattern_name_5:[k5_1_options,k5_2_options,k5_3_options,k5_4_options,k5_5_options],
    pattern_name_6:[k6_1_options,k6_2_options,k6_3_options,k6_4_options,k6_5_options],
    pattern_name_7:[k7_1_options,k7_2_options,k7_3_options,k7_4_options,k7_5_options],
    pattern_name_8:[k8_1_options,k8_2_options,k8_3_options,k8_4_options,k8_5_options],
    pattern_name_9:[k9_1_options,k9_2_options,k9_3_options,k9_4_options,k9_5_options],
    pattern_name_10:[k10_1_options,k10_2_options,k10_3_options,k10_4_options,k10_5_options]
    }
    all_k_edges={
    pattern_name_1:[k1_1_edges,k1_2_edges,k1_3_edges,k1_4_edges,k1_5_edges],
    pattern_name_2:[k2_1_edges,k2_2_edges,k2_3_edges,k2_4_edges,k2_5_edges],
    pattern_name_3:[k3_1_edges,k3_2_edges,k3_3_edges,k3_4_edges,k3_5_edges],
    pattern_name_4:[k4_1_edges,k4_2_edges,k4_3_edges,k4_4_edges,k4_5_edges],
    pattern_name_5:[k5_1_edges,k5_2_edges,k5_3_edges,k5_4_edges,k5_5_edges],
    pattern_name_6:[k6_1_edges,k6_2_edges,k6_3_edges,k6_4_edges,k6_5_edges],
    pattern_name_7:[k7_1_edges,k7_2_edges,k7_3_edges,k7_4_edges,k7_5_edges],
    pattern_name_8:[k8_1_edges,k8_2_edges,k8_3_edges,k8_4_edges,k8_5_edges],
    pattern_name_9:[k9_1_edges,k9_2_edges,k9_3_edges,k9_4_edges,k9_5_edges],
    pattern_name_10:[k10_1_edges,k10_2_edges,k10_3_edges,k10_4_edges,k10_5_edges]
    }
    k_values=[k_val_1,k_val_2,k_val_3,k_val_4,k_val_5,k_val_6,k_val_7,k_val_8,k_val_9,k_val_10]
    pattern_names=[pattern_name_1,pattern_name_2,pattern_name_3,pattern_name_4,pattern_name_5,
                    pattern_name_6,pattern_name_7,pattern_name_8,pattern_name_9,pattern_name_10]
    edges_bool = checkToBool(show_edges)
    start_nodes = processInputText(start_node_text)
    if start_nodes==[]:
        start_nodes=["wildcard"]
    end_nodes = processInputText(end_node_text)
    if end_nodes==[]:
        end_nodes=["wildcard"]
    searched_nodes_dict = {}
    searched_options_dict = {}
    searched_edges_dict = {}
    
    i=0
    for pattern in pattern_names:
        if i < pattern_select:
            k_nodes = [f"{s}",f"{all_k_nodes[pattern][0]}",f"{all_k_nodes[pattern][1]}",f"{all_k_nodes[pattern][2]}",f"{all_k_nodes[pattern][3]}",f"{all_k_nodes[pattern][4]}",f"{t}"]
            wildcarded_k_nodes = ['wildcard' if x == "None" else x for x in k_nodes]
            clean_k_nodes = ['`'+x+'`' if 'biolink' in x else x for x in wildcarded_k_nodes]
            searched_nodes = {pattern:clean_k_nodes[:k_values[i]+1]+[clean_k_nodes[-1]]}
            #print(searched_nodes)
            searched_nodes_dict.update(searched_nodes)

            if len("".join(all_k_options[pattern])) > 0:
                k_options = [f"{all_k_options[pattern][0]}",f"{all_k_options[pattern][1]}",f"{all_k_options[pattern][2]}",f"{all_k_options[pattern][3]}",f"{all_k_options[pattern][4]}"]
                wildcarded_k_options = ['wildcard' if x == "" else x for x in k_options]
                clean_k_options = wildcarded_k_options
            else:
                clean_k_options = ['wildcard', 'wildcard', 'wildcard', 'wildcard', 'wildcard']
            searched_options={pattern:clean_k_options[:k_values[i]]+[clean_k_options[-1]]}
            #print(searched_options)
            searched_options_dict.update(searched_options)

            if edges_bool == True:
                k_edges = [f"{all_k_edges[pattern][0]}",f"{all_k_edges[pattern][1]}",f"{all_k_edges[pattern][2]}",f"{all_k_edges[pattern][3]}",f"{all_k_edges[pattern][4]}",f"{t_edges}"]
                wildcarded_k_edges = ['wildcard' if x == "None" else x for x in k_edges]
                clean_k_edges = ['`'+x+'`' if 'biolink' in x else x for x in wildcarded_k_edges]
            else:
                clean_k_edges = ['wildcard', 'wildcard', 'wildcard', 'wildcard', 'wildcard', 'wildcard']
            searched_edges={pattern:clean_k_edges[:k_values[i]]+[clean_k_edges[-1]]}
            #print(searched_edges)
            searched_edges_dict.update(searched_edges)
            i+=1
        else:
            break
    if len(get_metadata) > 0:
        metadata_bool = get_metadata[0]
    else: 
        metadata_bool = False
    ans = Graphsearch(graph_db,start_nodes,end_nodes,searched_nodes_dict,searched_options_dict,searched_edges_dict,metadata_bool,timeout_ms=60000,limit_results=10000)

    answersdf = ans.drop_duplicates()
    columns = answersdf.columns
    size = len(answersdf.index)

    answers_table = dash_table.DataTable(id="answers",data=answersdf.to_dict('records'),
                        columns=[{"name": i.replace("`","").replace("biolink:",""), "id": i, "hideable": True, "selectable": [True if "node" in i else False]} for i in columns],
                        hidden_columns=[i for i in columns if "esnd" in i or "MetaData" in i],
                        tooltip_data=[{columns[col]: {'value': answersdf.iat[ind,col+1].replace(', ',',\\\n'), 'type': 'markdown'} if 'MetaData' in columns[col+1] else {} for col in range(len(columns)-1)} for ind in answersdf.index],
                         css=[{
                            'selector': '.dash-table-tooltip',
                            'rule': 'background-color: slategray; font-family: monospace; color: white; width: auto; word-break: normal'
                        }],
                        tooltip_duration=None,
                        sort_action="native",
                        filter_action="native",
                        column_selectable="multi",
                        row_selectable="multi",
                        selected_rows=[],
                        selected_columns=[],
                        #page_size=20,
                        style_table={'overflowX': 'auto','overflowY': 'auto','maxHeight':'40em','width':'70em','box-shadow':"0px 4px 6px -1px rgba(0, 0, 0, 0.2),0px 2px 4px -1px rgba(0, 0, 0, 0.06)"},
                        style_cell={
                            'color': "#000000",
                            'whiteSpace': "normal",
                            'textOverflow': 'ellipsis',
                            'text-align': 'center', 
                            #'maxWidth': '230px',
                            'height': 'auto'
                        },
                        style_header={
                            'fontWeight': "bold",
                            'whiteSpace': "normal",
                            'backgroundColor': 'rgb(200, 200, 200)'
                        },
                        style_data={
                            'whiteSpace': "normal",
                            'height': "auto",
                            #'lineHeight': '15px',
                        },
                        style_data_conditional=[{
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(230, 230, 230)',
                        }],
                        markdown_options={"html": True},
                        export_format="csv")
    
    return ([f"{graph_db} search complete! {size} unique answers found."],
            answers_table,
            {"margin-right":"1em",'display':'block'},
            {"margin-right":"1em",'display':'block'},
            {"margin-right":"1em",'display':'block'},
            {"margin":"1em",'display':'block', 'width':'69%'})

@app.callback([Output('loading-start', 'children'),Output('start-map-output', 'value'),Output('start-map-div', 'style')],
    [Input('start-term-map-val', 'n_clicks')],
    [State('starts', 'value'), State('kg-dropdown', 'value'),State("source-dropdown", 'value'),State('start-map-output', 'value'),State('start-map-div', 'style')],
    prevent_initial_call=True)
def KGNodeMapper(start_n_clicks, start_terms, graph_db, start_label, s_map_val, s_map_style):
    button_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    styleOn = {"display":'block'}
    styleOff = {"display":'None'}
    if button_id == 'start-term-map-val' and start_n_clicks != 0:
        nodeCheck = checkNodeNameID(graph_db, start_terms, start_label)
        if nodeCheck == "":
            return ([f"{graph_db} Term Mapping Complete!"], nodeCheck, styleOff)
        else:
            return ([f"{graph_db} Term Mapping Complete!"], nodeCheck, styleOn)
    else:
        return dash.no_update

@app.callback([Output('loading-end', 'children'),Output('end-map-output', 'value'),Output('end-map-div', 'style')],
    [Input('end-term-map-val', 'n_clicks')],
    [State('ends','value'), State('kg-dropdown', 'value'),State("tail-dropdown", 'value'),State('end-map-output', 'value'),State('end-map-div', 'style')],
    prevent_initial_call=True)
def KGNodeMapper(end_n_clicks, end_terms, graph_db, end_label, e_map_val, e_map_style):
    button_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    styleOn = {"display":'block'}
    styleOff = {"display":'None'}
    if button_id == 'end-term-map-val' and end_n_clicks != 0:
        nodeCheck = checkNodeNameID(graph_db, end_terms, end_label)
        if nodeCheck == "":
            return ([f"{graph_db} Term Mapping Complete!"], nodeCheck, styleOff)
        else:
            return ([f"{graph_db} Term Mapping Complete!"], nodeCheck, styleOn)
    else:
        return dash.no_update


@app.callback(
    Output('subgraph-fig','src'),
    #Output('cytoscape-fig','children'),
    Input('answers','selected_rows'),
    State('answer-table','children'),
    prevent_initial_call=True)
def ShowAnswerSubgraph(selected_rows,answer_datatable):
    if len(selected_rows)<1: return ""
    dff = pd.DataFrame(answer_datatable['props']['data'])
    fig = VisualizeAnswerRow(dff,selected_rows)
    return fig

@app.callback(
    [Output('loading-3','children'),
    Output('dwpc-table', 'children'),
    Output('submit-pca-vis', 'style'),
    Output('submit-rf-train', 'style'),
    Output('pos-search-box', 'style')],
    Input('submit-dwpc-val', 'n_clicks'),
    [State('answer-table', 'children'),
    State("source-dropdown", 'value'), 
    State("tail-dropdown", 'value'),
    State("dwpc-weight-select", 'value')],
    prevent_initial_call=True)
def CalculateDWPC(n_clicks,answer_datatable,start_type,end_type,w):
    if(n_clicks <= 0): return ""
    #dff = pd.DataFrame.from_dict(answer_datatable)
    dff = pd.DataFrame(answer_datatable['props']['data'])
    PDP = []
    metapathnames=[]
    W = w
    column_names = list(dff)
    print(column_names)
    for ind in dff.index:
        row = dff.iloc[ind]
        pdp = 1
        metapath=row['path']+":"
        for col in column_names:
            if "esnd" in col and row[col] != "?":
                pdp = pdp*(row[col]**(-W))
            if "edge" in col:
                edgelabel=row[col].replace("biolink:", "")
                metapath=metapath+edgelabel+"|"
        PDP.append(pdp)
        metapathnames.append(metapath)
    dff["PathDegreeProduct"] = PDP
    dff["Metapath Name"] = metapathnames
    node_columns = [x for x in column_names if end_type in x]
    print(node_columns)
    #To change whole df column at once
    #dff.loc[dff[node_columns[-1]] == '?', node_columns[-1]] = dff[]
    i=-2
    while abs(i)<=len(node_columns):
        dff[node_columns[-1]] = dff.apply(lambda x: x[node_columns[i]] if x[node_columns[-1]] =="?" else x[node_columns[-1]], axis=1)
        i+=-1
    #print(dff[node_columns[-1]])
    #gkindex=["node0: biolink:ChemicalEntity", "node2: biolink:DiseaseOrPhenotypicFeature"]
    gkindex=["node0: `"+start_type+"`",node_columns[-1]]
    gk = pd.pivot_table(dff, index=gkindex,columns=["Metapath Name"], values="PathDegreeProduct", aggfunc=sum)
    gk = gk.fillna(0)
    gk.reset_index(inplace=True)
    first=gk.columns[0][6:]
    second=gk.columns[1][6:]
    gk.rename(columns={gk.columns[0]:first,gk.columns[1]:second}, inplace = True)
    dwpc_table = dash_table.DataTable(id="dwpc",data=gk.to_dict('records'),
                        columns=[{"name": i.replace("`","").replace("biolink:",""), "id": i, "hideable": True} for i in gk.columns],
                        sort_action='native',
                        filter_action="native",
                        row_selectable="multi",
                        selected_rows=[],
                        #page_size=20,
                        style_table={'overflowX': 'auto','overflowY': 'auto','maxHeight':'40em','width':'70em'},
                        style_header={
                            'fontWeight': "bold",
                            'whiteSpace': "normal",
                            'backgroundColor': 'rgb(200, 200, 200)'
                        },
                        style_cell={
                            'color': "#000000",
                            'whiteSpace': "normal",
                            'textOverflow': 'ellipsis',
                            'text-align': 'center', 
                            #'maxWidth': '230px',
                            'height': 'auto'
                        },
                        style_data={
                            'whiteSpace': "normal",
                            'height': "auto"},
                        style_data_conditional=[{
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(230, 230, 230)',
                        }],
                        export_format="csv")

    style={'display':'block'}
    return ["Finished Calculating Degree-Weighted Path Counts!"],dwpc_table,style,style,style
    
@app.callback([Output('pca-fig-2comp', 'figure'),
    Output('pca-fig-3comp', 'figure'),
    Output('pca-fig-2comp', 'style'),
    Output('pca-fig-3comp', 'style'),
    Output('rf-5FCV-fig','src'),
    Output('loading-5','children')],
    [Input('submit-pca-vis', 'n_clicks'), 
    Input('submit-rf-train', 'n_clicks')],
    [State('dwpc-table', 'children'),
    State('dwpc', 'selected_rows'),
    State('pca-positives', 'value')],
    prevent_initial_call=True)
def MachineLearning(pca_clicks,rf_clicks,dwpc_datatable,selected_rows,positive_rows):
    button_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    print(button_id)
    if button_id == 'submit-pca-vis' and pca_clicks:
    #if(n_clicks <= 0): return ""
        print(selected_rows)
        print(type(selected_rows))
        # if positive_rows is None:
        #     positives=[]
        # else:
        if positive_rows != None:
            positives=processInputText(positive_rows)
        else:
            positives=[]

        gk = pd.DataFrame(dwpc_datatable['props']['data'])
        if selected_rows != None:
            for row in selected_rows:
                positives.append(f"{gk.iat[row,0]}:{gk.iat[row,1]}")
        pca2comp=PCA.performPCA(gk,positives,2)
        pca3comp=PCA.performPCA(gk,positives,3)
        style2comp={'display':'block'}#,'width':'1000px','height':'1000px'}
        style3comp={'display':f"{'None' if pca3comp=='' else 'block'}"}
        message = "Completed PCA Visualization"
        return [pca2comp,pca3comp,style2comp,style3comp,"",message]
        
    elif button_id == 'submit-rf-train' and rf_clicks:
    #if(n_clicks <= 0): return ""
        print(selected_rows)
        print(type(selected_rows))
        if positive_rows != None:
            positives=processInputText(positive_rows)
        else:
            positives=[]

        gk = pd.DataFrame(dwpc_datatable['props']['data'])
        if selected_rows != None:
            for row in selected_rows:
                positives.append(f"{gk.iat[row,0]}:{gk.iat[row,1]}")
        train_stats=RandomForestClassifierTrain(gk, positives, balance_data=False)
        styleOn={'display':'block'}
        styleOff={'display':'None'}
        stats_fig=train_stats[0]
        message = train_stats[1]
        return ["","",styleOff,styleOff,stats_fig,message]

# @app.callback([Output('pca-fig-2comp', 'figure'),
#     Output('pca-fig-3comp', 'figure'),
#     Output('pca-fig-2comp', 'style'),
#     Output('pca-fig-3comp', 'style')],
#     Input('submit-pca-vis', 'n_clicks'),
#     [State('dwpc-table', 'children'),
#     State('dwpc', 'selected_rows'),
#     State('pca-positives', 'value')])
# def MachineLearning(pca_clicks,rf_clicks,dwpc_datatable,selected_rows,positive_rows):
#     button_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
#     print(button_id)
#     if button_id == 'submit-pca-vis' and pca_clicks:
#     #if(n_clicks <= 0): return ""
#         print(selected_rows)
#         print(type(selected_rows))
#         # if positive_rows is None:
#         #     positives=[]
#         # else:
#         if positive_rows != None:
#             positives=processInputText(positive_rows)
#         else:
#             positives=[]

#         gk = pd.DataFrame(dwpc_datatable['props']['data'])
#         if selected_rows != None:
#             for row in selected_rows:
#                 positives.append(f"{gk.iat[row,0]}-{gk.iat[row,1]}")
#         RandomForestClassifierTrain(gk, positives, balance_data=False)
#         pca2comp=PCA.performPCA(gk,positives,2)
#         pca3comp=PCA.performPCA(gk,positives,3)
#         style2comp={'display':'block'}#,'width':'1000px','height':'1000px'}
#         style3comp={'display':f"{'None' if pca3comp=='' else 'block'}"}

#         return [pca2comp,pca3comp,style2comp,style3comp]

#     elif button_id == 'submit-rf-train' and rf_clicks:
#     #if(n_clicks <= 0): return ""
#         print(selected_rows)
#         print(type(selected_rows))
#         if positive_rows != None:
#             positives=processInputText(positive_rows)
#         else:
#             positives=[]

#         gk = pd.DataFrame(dwpc_datatable['props']['data'])
#         if selected_rows != None:
#             for row in selected_rows:
#                 positives.append(f"{gk.iat[row,0]}-{gk.iat[row,1]}")
#         RandomForestClassifierTrain(gk, positives, balance_data=False)

#         return ["pca2comp",pca3comp,style2comp,style3comp]

@app.callback(
    [Output('answers', 'data'), Output('answers', 'columns'), Output('answers','hidden_columns'),Output('loading-4', 'children')],
    [Input('submit-protein-names', 'n_clicks'), Input('submit-triangulator-val', 'n_clicks')],
    [State('answer-table', 'children'), State('answers', 'selected_columns')],
    prevent_initial_call=True)
def UpdateAnswers(protein_names_clicks,triangulator_clicks,answer_datatable,selected_columns):
    button_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    print(button_id)
    if button_id == 'submit-protein-names' and protein_names_clicks:
        #Get protein names from HGNC
        dff = pd.DataFrame.from_dict(answer_datatable['props']['data'])
        protein_names = GetProteinNames(dff)

        ammended_answers=protein_names[0]
        ammended_columns=protein_names[1]
        hidden_columns=protein_names[2]
        message=protein_names[3]

        return ammended_answers, ammended_columns, hidden_columns, message
    elif button_id == 'submit-triangulator-val' and triangulator_clicks:
        print(selected_columns)
        #Find number of co-mentioning abstracts from Pubmed for 2 or 3 terms.
        dff = pd.DataFrame.from_dict(answer_datatable['props']['data'])

        comentions=PubMedCoMentions(dff,selected_columns,expand=True)
        
        ammended_answers=comentions[0]
        ammended_columns=comentions[1]
        hidden_columns=comentions[2]
        message=comentions[3]
        return (ammended_answers, ammended_columns, hidden_columns, message)
    else:
        raise dash.exceptions.PreventUpdate
# @app.callback(
#     Output("download-dataframe-csv", "data"),
#     Input("btn_csv", "n_clicks"),
#     State("layout", "children"),
#     prevent_initial_call=True
# )
# def DownloadSettings(n_clicks, layout):
#     if(n_clicks <= 0): return ""
#     print(type(layout))
#     settings = pickle.dump(layout)
#     return settings
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    [State('starts','value'),
    State('ends','value'),
    State('pos-search-box','value'),
    # State("source-dropdown",'value'),State("tail-dropdown",'value'),
    # State("node-dropdown-1-1",'value'),State("node-dropdown-1-2",'value'),State("node-dropdown-1-3",'value'),State("node-dropdown-1-4",'value'),State("node-dropdown-1-5",'value'),
    # State("node-dropdown-2-1",'value'),State("node-dropdown-2-2",'value'),State("node-dropdown-2-3",'value'),State("node-dropdown-2-4",'value'),State("node-dropdown-2-5",'value'),
    # State("node-dropdown-3-1",'value'),State("node-dropdown-3-2",'value'),State("node-dropdown-3-3",'value'),State("node-dropdown-3-4",'value'),State("node-dropdown-3-5",'value'),
    # State("node-dropdown-4-1",'value'),State("node-dropdown-4-2",'value'),State("node-dropdown-4-3",'value'),State("node-dropdown-4-4",'value'),State("node-dropdown-4-5",'value'),
    # State("node-dropdown-5-1",'value'),State("node-dropdown-5-2",'value'),State("node-dropdown-5-3",'value'),State("node-dropdown-5-4",'value'),State("node-dropdown-5-5",'value'),
    # State("node-dropdown-6-1",'value'),State("node-dropdown-6-2",'value'),State("node-dropdown-6-3",'value'),State("node-dropdown-6-4",'value'),State("node-dropdown-6-5",'value'),
    # State("node-dropdown-7-1",'value'),State("node-dropdown-7-2",'value'),State("node-dropdown-7-3",'value'),State("node-dropdown-7-4",'value'),State("node-dropdown-7-5",'value'),
    # State("node-dropdown-8-1",'value'),State("node-dropdown-8-2",'value'),State("node-dropdown-8-3",'value'),State("node-dropdown-8-4",'value'),State("node-dropdown-8-5",'value'),
    # State("node-dropdown-9-1",'value'),State("node-dropdown-9-2",'value'),State("node-dropdown-9-3",'value'),State("node-dropdown-9-4",'value'),State("node-dropdown-9-5",'value'),
    # State("node-dropdown-10-1",'value'),State("node-dropdown-10-2",'value'),State("node-dropdown-10-3",'value'),State("node-dropdown-10-4",'value'),State("node-dropdown-10-5",'value'),
    # State("edge-dropdown-1-1",'value'),State("edge-dropdown-1-2",'value'),State("edge-dropdown-1-3",'value'),State("edge-dropdown-1-4",'value'),State("edge-dropdown-1-5",'value'),
    # State("edge-dropdown-2-1",'value'),State("edge-dropdown-2-2",'value'),State("edge-dropdown-2-3",'value'),State("edge-dropdown-2-4",'value'),State("edge-dropdown-2-5",'value'),
    # State("edge-dropdown-3-1",'value'),State("edge-dropdown-3-2",'value'),State("edge-dropdown-3-3",'value'),State("edge-dropdown-3-4",'value'),State("edge-dropdown-3-5",'value'),
    # State("edge-dropdown-4-1",'value'),State("edge-dropdown-4-2",'value'),State("edge-dropdown-4-3",'value'),State("edge-dropdown-4-4",'value'),State("edge-dropdown-4-5",'value'),
    # State("edge-dropdown-5-1",'value'),State("edge-dropdown-5-2",'value'),State("edge-dropdown-5-3",'value'),State("edge-dropdown-5-4",'value'),State("edge-dropdown-5-5",'value'),
    # State("edge-dropdown-6-1",'value'),State("edge-dropdown-6-2",'value'),State("edge-dropdown-6-3",'value'),State("edge-dropdown-6-4",'value'),State("edge-dropdown-6-5",'value'),
    # State("edge-dropdown-7-1",'value'),State("edge-dropdown-7-2",'value'),State("edge-dropdown-7-3",'value'),State("edge-dropdown-7-4",'value'),State("edge-dropdown-7-5",'value'),
    # State("edge-dropdown-8-1",'value'),State("edge-dropdown-8-2",'value'),State("edge-dropdown-8-3",'value'),State("edge-dropdown-8-4",'value'),State("edge-dropdown-8-5",'value'),
    # State("edge-dropdown-9-1",'value'),State("edge-dropdown-9-2",'value'),State("edge-dropdown-9-3",'value'),State("edge-dropdown-9-4",'value'),State("edge-dropdown-9-5",'value'),
    # State("edge-dropdown-10-1",'value'),State("edge-dropdown-10-2",'value'),State("edge-dropdown-10-3",'value'),State("edge-dropdown-10-4",'value'),State("edge-dropdown-10-5",'value'),
    # State("tail-edge",'value'), 
    # State('selector-1','style'),
    # State('selector-1','children'),
    # State('selector-2','style'),
    # State('selector-2','children'),
    # State('selector-3','style'),
    # State('selector-3','children'),
    # State('selector-4','style'),
    # State('selector-4','children'),
    # State('selector-5','style'),
    # State('selector-5','children'),
    # State('selector-6','style'),
    # State('selector-6','children'),
    # State('selector-7','style'),
    # State('selector-7','children'),
    # State('selector-8','style'),
    # State('selector-8','children'),
    # State('selector-9','style'),
    # State('selector-9','children'),
    # State('selector-10','style'),
    # State('selector-10','children'),
    State('kg-dropdown','value'),
    State('edge-checkbox','value'),
    State('settings_name','value')],
    prevent_initial_call=True)
def DownloadSettings(n_clicks, start_node_text, end_node_text, positive_rows,
    # starter,ender,
    # node_value-1-1,node_value-1-2,node_value-1-3,node_value-1-4,node_value-1-5,
    # node_value-2-1,node_value-2-2,node_value-2-3,node_value-2-4,node_value-2-5,
    # node_value-3-1,node_value-3-2,node_value-3-3,node_value-3-4,node_value-3-5,
    # node_value-4-1,node_value-4-2,node_value-4-3,node_value-4-4,node_value-4-5,
    # node_value-5-1,node_value-5-2,node_value-5-3,node_value-5-4,node_value-5-5,
    # node_value-6-1,node_value-6-2,node_value-6-3,node_value-6-4,node_value-6-5,
    # node_value-7-1,node_value-7-2,node_value-7-3,node_value-7-4,node_value-7-5,
    # node_value-8-1,node_value-8-2,node_value-8-3,node_value-8-4,node_value-8-5,
    # node_value-9-1,node_value-9-2,node_value-9-3,node_value-9-4,node_value-9-5,
    # node_value-10-1,node_value-10-2,node_value-10-3,node_value-10-4,node_value-10-5,
    # edge_value-1-1,edge_value-1-2,edge_value-1-3,edge_value-1-4,edge_value-1-5,
    # edge_value-2-1,edge_value-2-2,edge_value-2-3,edge_value-2-4,edge_value-2-5,
    # edge_value-3-1,edge_value-3-2,edge_value-3-3,edge_value-3-4,edge_value-3-5,
    # edge_value-4-1,edge_value-4-2,edge_value-4-3,edge_value-4-4,edge_value-4-5,
    # edge_value-5-1,edge_value-5-2,edge_value-5-3,edge_value-5-4,edge_value-5-5,
    # edge_value-6-1,edge_value-6-2,edge_value-6-3,edge_value-6-4,edge_value-6-5,
    # edge_value-7-1,edge_value-7-2,edge_value-7-3,edge_value-7-4,edge_value-7-5,
    # edge_value-8-1,edge_value-8-2,edge_value-8-3,edge_value-8-4,edge_value-8-5,
    # edge_value-9-1,edge_value-9-2,edge_value-9-3,edge_value-9-4,edge_value-9-5,
    # edge_value-10-1,edge_value-10-2,edge_value-10-3,edge_value-10-4,edge_value-10-5,
    # tail_edge_value,
    kgdrop,edgecheck,fname):
    # button_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    # print(button_id)
    # if button_id == 'btn_csv' and n_clicks:
    if(n_clicks <= 0): return ""

    if start_node_text != None:
        start_nodes = processInputText(start_node_text)
    else:
        start_nodes = []

    if end_node_text != None:
        end_nodes = processInputText(end_node_text)
    else:
        end_nodes = []

    if positive_rows != None:
        positives = processInputText(positive_rows)
    else:
        positives = []

    #selector = [s1s,s1c,s2s,s2c,s3s,s3c,s4s,s4c,s5s,s5c,s6s,s6c,s7s,s7c,s8s,s8c,s9s,s9c,s10s,s10c]
    
    
    d = dict(Starts=np.array(start_nodes), Ends=np.array(end_nodes), Positives=np.array(positives), KnowledgeGraph=np.array(kgdrop))#,Edges=np.array(edgecheck)) #Selector=np.array(selector))
    df = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in d.items() ]))
    return dcc.send_data_frame(df.to_csv, f"{fname}.csv")

@app.callback([
    Output('starts','value'),
    Output('ends','value'),
    Output('pos-search-box','value'),
    Output('kg-dropdown','value')
    #Output('edge-checkbox','value')
    ],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True)
def UploadSettings(contents,filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')),index_col=False)
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded),index_col=False)
    except Exception as e:
        print(e)
        return ""
    starts=''''''
    for n in df['Starts'].dropna().to_list():
        print(n)
        starts = starts+n+"\n"
    # for n in range(len(starts)):
    #     starts[n].replace(",","\n")
    ends=''''''
    for n in df['Ends'].dropna().to_list():
        ends = ends+n+"\n"
    # for n in range(len(ends)):
    #     ends[n].replace(",","\n")
    positives=''''''
    for n in df['Positives'].dropna().to_list():
        positives = positives+n+"\n"
    # for n in range(len(positives)):
    #     positives[n].replace(",","\n")
    kgdrop=df['KnowledgeGraph'][0]
    #edgecheck=df['Edges'][0]

    return starts,ends,positives,kgdrop#,edgecheck

 #############################################################    

if __name__ == '__main__':

    #app.run_server()
    app.run_server(host='0.0.0.0', port=80,debug=False) #For production

