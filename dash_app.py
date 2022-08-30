import pandas as pd
import py2neo
import dash
from dash import dcc
from dash import html
from dash import Dash, dash_table
import dash_daq as daq
import numpy as np
from dash.dependencies import Output, Input, State
import requests as rq
import xml.etree.cElementTree as ElementTree
import time
from networkx.drawing.nx_pydot import graphviz_layout
from Neo4jSearch import Graphsearch
from Neo4jSearch import getNodeAndEdgeLabels
import io
import base64
import PCA

app = dash.Dash()
app.title = 'ExPAT/EmPATH'
app._favicon = 'LogoMML.ico'
app.css.append_css({'external_url': '/assets/styles.css'})

colors = {
    'background': '#7794B8',
    'dropdown': '#6c6f73',
    'text': '#000000'
}

rk_nodes_and_edges=getNodeAndEdgeLabels('ROBOKOP')
rk_nodes=rk_nodes_and_edges[0]
rk_edges=rk_nodes_and_edges[1]

#Define components used:
kg_dropdown = dcc.Dropdown(id="kg-dropdown",
           options=[
           {'label':"ROBOKOP", 'value':"ROBOKOP"},
           {'label':"SCENT-KOP", 'value':"SCENT-KOP"},
           {'label':"HetioNet", 'value':"HetioNet"}],
           value="ROBOKOP",
           className='dropdownbox',
           clearable=False)

source_dropdown = dcc.Dropdown(id="source-dropdown",
           options=[{'label':x.replace("biolink:",""), 'value':x} for x in rk_nodes],
           value="biolink:ChemicalEntity",
           clearable=False)

tail_dropdown = dcc.Dropdown(id="tail-dropdown",
           options=[{'label':x.replace("biolink:",""), 'value':x} for x in rk_nodes],
           value="biolink:DiseaseOrPhenotypicFeature",
           clearable=False)

node_drop = dcc.Dropdown(id="node-dropdown",
    options=[{'label':x.replace("biolink:",""), 'value':x} for x in rk_nodes],
   multi=False
)

#Adds a button to check whether names entered into Start and End are matched with search terms in ROBOKOP 
#and a markdown component to display terms that dont match
term_map_button = html.Button('Check for Terms in Knowledge Graph', id='term-map-val', n_clicks=0)

start_map_output = html.Div([
    html.Div(html.B(children='Starting Terms Mapped to Knowledge Graph:\n')),
    dcc.Textarea(
        id='start-map-output',
        style={'width': '20%', 'height': 140, 'width': 300})],
    id='start-map-div',style={'display': 'None'})

end_map_output = html.Div([
    html.Div(html.B(children='Ending Terms Mapped to Knowledge Graph:\n')),
    dcc.Textarea(
        id='end-map-output',
        style={'width': '20%', 'height': 140, 'width': 300})],
    id='end-map-div',style={'display': 'None'})

#Adds a numeric selector which makes or removes new query patterns to add to selector list.
pattern_select = daq.NumericInput(id="pattern-select",min=1,max=10,value=1,label="Number of Query Patterns") 

#Makes the text input box to name the individual query patterns.
#Default query pattern names are P1, P2, ... Pn.
pattern_name_boxes=[]
for i in range(1,11):
    pattern_name = dcc.Input(id="pattern-name-{}".format(i), type="text", placeholder='P{}'.format(i), value='P{}'.format(i))
    pattern_name_boxes.append(pattern_name)

#Make the selection button that determines globally whether or not edges can be specificied.
#Turning on edge selection still allows wildcard searching.
edge_checkbox = dcc.Checklist(id="edge-checkbox",style={'width': '10em'}, options=[{"label":"Use Edges","value":"True"}],value=[])

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
                    {'label':x, 'value':x} for x in rk_edges 
                ],
            multi=False
            )],
            id="edge-div-{}".format(str(i)+"-"+str(k)),
            style={'display':'block', 'width': '20%'}
        )
        drop = html.Div([
            html.B(children='Level k-%i:'%k),
            edge_drop,
            dcc.Dropdown(
            id="node-dropdown-{}".format(str(i)+"-"+str(k)),
                options=[
                    {'label':x, 'value':x} for x in rk_nodes 
                ],
            multi=False
            )

            ],
            id="node-div-{}".format(str(i)+"-"+str(k)),
            style={'display':('block' if k<3 else 'None'), 'width': '20%'}
            )
        k_drop.append(drop)
    all_k_drops.append(k_drop)
print(len(all_k_drops))
edge_drop = dcc.Dropdown(
    id="edge-dropdown",
   options=[
       {'label':x, 'value':x} for x in rk_edges 
   ],
   multi=False,
   style={'display':'None'}
)

tail_edge = dcc.Dropdown(
    id="tail-edge",
   options=[
       {'label':x, 'value':x} for x in rk_edges 
   ],
   multi=False,
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
'''Triphenyl phosphate
Bisphenol A
Pyrene
Tricresyl phosphate''',
        placeholder="Leave blank to include *any* start entities...",
        className='searchTerms'
)])

ends = html.Div([
    html.Div(html.B(children='Ending Points:\n')),
    dcc.Textarea(
        id='ends',
        value='''Neurodevelopmental Disorders''',
        placeholder="Leave blank to include *any* end entities...",
        className='searchTerms'
    )])

#Create buttons to submit ROBOKOP search, get protein names, and calculate DWPC.
submit_button = html.Button('Submit', id='submit-val', n_clicks=0, style={"margin-right": "1em"})
protein_names_button = html.Button('Get Protein Names', id='submit-protein-names', n_clicks=0, style={"display":'None'})
triangulator_button = html.Button('Get PubMed Abstract Co-Mentions', id='submit-triangulator-val', n_clicks=0, style={"display":'None'})
dwpc_button = html.Button('Submit DWPC', id='submit-dwpc-val', n_clicks=0, style={"display":'None'})
dwpc_weight = dcc.Input(id="dwpc-weight-select",
                        value=0,
                        type='number',
                        min=0,
                        max=1,
                        step=0.01,
                        placeholder="Weight",
                        style={'display':'None','vertical-align':'center','padding':'1em'})

all_node_edge_divs = []
for j in range(10):
    node_edge_div = html.Div([html.Td(all_k_drops[j][0], style={'width': '20em'}),
        html.Td(all_k_drops[j][1], style={'width': '20em'}),
        html.Td(all_k_drops[j][2],style={'width': '20em'}),
        html.Td(all_k_drops[j][3],style={'width': '20em'}),
        html.Td(all_k_drops[j][4],style={'width': '20em'})],
        style={'width': '100em'},id="node-edge-div-%i" % (j+1))
    all_node_edge_divs.append(node_edge_div)
    
#Create tables for results
answer_table = html.Div(id='answer-table', style={'color': colors['text']})
protein_names_answers = html.Div(id='protein-names-answers', style={'color': colors['text']})
dwpc_table = html.Div(id='dwpc-table', style={'color': colors['text']})

#create div for PCA figure output
#pca_fig = html.Img(id='pca-fig')
pca_button = html.Button('Perform Principal Component Analysis', id='submit-pca-vis', n_clicks=0, style={"display":'None'})
pca_fig_2comp = dcc.Graph(id='pca-fig-2comp',className="scatterplot",style={'display':'None'})
pca_fig_3comp = dcc.Graph(id='pca-fig-3comp',className="scatterplot",style={'display':'None'})

selector = []
for j in range(10):
    select = html.Div(id='selector-%i' % (j+1), style={'display':('None' if j != 0 else 'block')}, children=[
        html.Td(children=[html.Td(style={'text-align':'center'},children=html.B(children='Query Pattern Name:')),pattern_name_boxes[j]]),                              
        html.Td(children=[html.Td(style={'text-align':'center'},children=html.B(children='K Value:')),all_k_selects[j]]),
        html.Td(children=[html.Td(style={'text-align':'center'},children=html.B(children='')),html.B(children='==>',style={'vertical-align':'bottom'})]),      
        html.Td(children=[all_node_edge_divs[j]])
        ])
    
    selector.append(select)

load =  dcc.Loading(
    id="loading-1",
    type="default",
    color=colors['text'],
    children=html.Div(id="loading-output-1")
)

load_2 =  dcc.Loading(
    id="loading-2",
    type="default",
    color=colors['text'],
    children=html.Div(id="loading-output-2")
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

row1 = html.Tr([
    html.Td(starts), 
    html.Td(ends),
    html.Div(submit_button),
    html.Td(load),
    answer_table,
    protein_names_answers
])
row0 = html.Tr(selector)
tbody = html.Tbody([row0, row1])
table = html.Table(tbody, style={'color': colors['text']})

app.layout = html.Div(style={'padding-left': '3em','background-color': colors['background'], 'color': colors['text']}, children=[

        html.Div(html.Tr(html.B(children='Welcome to ExPAT (Extracting and Exploring Explanatory Pathways About Therapeutics)!')),
            style={'padding-top':'1em','padding-bottom':'1em','font-size':'40px'}), 
        
        html.Div([html.B(children='To begin:'),
            html.Tr(children='(1) Select a biomedical knowledge graph source.'),
            html.H1(children='Knowledge Graph:'),kg_dropdown],
            style={'width': '20em'}), 

            html.Div(style={'padding-bottom':'3em','vertical-align':'top'}, children=[
                html.Tr(children='(2) Choose category of Starting and Ending nodes for pathway.'),
                html.Td(children=[html.H1(children='Start Node:'),source_dropdown],
                    style={'width': '20em'}),
                html.Td(children=[html.H1(children='Tail Node:'),tail_edge,tail_dropdown],
                    style={'width': '20em'}),
                html.Td(children=[pattern_select]),
                html.Td(edge_checkbox, style={'vertical-align':'bottom'})]),

            html.Div(children=selector, style={'padding-bottom': '3em'}),
        
            html.Div([html.Td(starts),
                    html.Td(ends),
                    html.Td(start_map_output),html.Td(end_map_output)]),
        
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
                
        html.Div([submit_button, term_map_button, load, load_2], style={'padding-bottom': '3em'}),
    
        html.Div([answer_table, protein_names_answers], style={'width': '120em', 'padding-bottom': '1em'}),

        html.Div([html.Td(protein_names_button), html.Td(triangulator_button), html.Td(dwpc_button),html.Td(dwpc_weight),html.Td(load_3), html.Td(load_4)], style={'padding-bottom': '3em'}),
    
        html.Div(dwpc_table, style={'width': '120em', 'padding-bottom': '3em'}),

        html.Div(pca_button),
        
        html.Div(pca_fig_2comp),

        html.Div(pca_fig_3comp),
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
    rk_nodes_and_edges=getNodeAndEdgeLabels(graph_db)
    rk_nodes=rk_nodes_and_edges[0]
    rk_edges=rk_nodes_and_edges[1]
    node_options = [{'label':x.replace("biolink:",""), 'value':x} for x in rk_nodes]
    edge_options = [{'label':x.replace("biolink:",""), 'value':x} for x in rk_edges]
    print(node_options)
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
    Input('pattern-select', 'value'))
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
    [Input("k-select-1", 'value'),Input("edge-checkbox", 'value')])
def hide_elements_k1(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-2-1",'style'),Output("node-div-2-2",'style'),Output("node-div-2-3",'style'),Output("node-div-2-4",'style'),Output("node-div-2-5",'style'),
    Output("edge-div-2-1",'style'),Output("edge-div-2-2",'style'),Output("edge-div-2-3",'style'),Output("edge-div-2-4",'style'),Output("edge-div-2-5",'style')], 
    [Input("k-select-2", 'value'),Input("edge-checkbox", 'value')])
def hide_elements_k2(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-3-1",'style'),Output("node-div-3-2",'style'),Output("node-div-3-3",'style'),Output("node-div-3-4",'style'),Output("node-div-3-5",'style'),
    Output("edge-div-3-1",'style'),Output("edge-div-3-2",'style'),Output("edge-div-3-3",'style'),Output("edge-div-3-4",'style'),Output("edge-div-3-5",'style')], 
    [Input("k-select-3", 'value'),Input("edge-checkbox", 'value')])
def hide_elements_k3(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-4-1",'style'),Output("node-div-4-2",'style'),Output("node-div-4-3",'style'),Output("node-div-4-4",'style'),Output("node-div-4-5",'style'),
    Output("edge-div-4-1",'style'),Output("edge-div-4-2",'style'),Output("edge-div-4-3",'style'),Output("edge-div-4-4",'style'),Output("edge-div-4-5",'style')], 
    [Input("k-select-4", 'value'),Input("edge-checkbox", 'value')])
def hide_elements_k4(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-5-1",'style'),Output("node-div-5-2",'style'),Output("node-div-5-3",'style'),Output("node-div-5-4",'style'),Output("node-div-5-5",'style'),
    Output("edge-div-5-1",'style'),Output("edge-div-5-2",'style'),Output("edge-div-5-3",'style'),Output("edge-div-5-4",'style'),Output("edge-div-5-5",'style')], 
    [Input("k-select-5", 'value'),Input("edge-checkbox", 'value')])
def hide_elements_k5(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-6-1",'style'),Output("node-div-6-2",'style'),Output("node-div-6-3",'style'),Output("node-div-6-4",'style'),Output("node-div-6-5",'style'),
    Output("edge-div-6-1",'style'),Output("edge-div-6-2",'style'),Output("edge-div-6-3",'style'),Output("edge-div-6-4",'style'),Output("edge-div-6-5",'style')], 
    [Input("k-select-6", 'value'),Input("edge-checkbox", 'value')])
def hide_elements_k6(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-7-1",'style'),Output("node-div-7-2",'style'),Output("node-div-7-3",'style'),Output("node-div-7-4",'style'),Output("node-div-7-5",'style'),
    Output("edge-div-7-1",'style'),Output("edge-div-7-2",'style'),Output("edge-div-7-3",'style'),Output("edge-div-7-4",'style'),Output("edge-div-7-5",'style')], 
    [Input("k-select-7", 'value'),Input("edge-checkbox", 'value')])
def hide_elements_k7(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-8-1",'style'),Output("node-div-8-2",'style'),Output("node-div-8-3",'style'),Output("node-div-8-4",'style'),Output("node-div-8-5",'style'),
    Output("edge-div-8-1",'style'),Output("edge-div-8-2",'style'),Output("edge-div-8-3",'style'),Output("edge-div-8-4",'style'),Output("edge-div-8-5",'style')], 
    [Input("k-select-8", 'value'),Input("edge-checkbox", 'value')])
def hide_elements_k8(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-9-1",'style'),Output("node-div-9-2",'style'),Output("node-div-9-3",'style'),Output("node-div-9-4",'style'),Output("node-div-9-5",'style'),
    Output("edge-div-9-1",'style'),Output("edge-div-9-2",'style'),Output("edge-div-9-3",'style'),Output("edge-div-9-4",'style'),Output("edge-div-9-5",'style')], 
    [Input("k-select-9", 'value'),Input("edge-checkbox", 'value')])
def hide_elements_k9(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback([Output("node-div-10-1",'style'),Output("node-div-10-2",'style'),Output("node-div-10-3",'style'),Output("node-div-10-4",'style'),Output("node-div-10-5",'style'),
    Output("edge-div-10-1",'style'),Output("edge-div-10-2",'style'),Output("edge-div-10-3",'style'),Output("edge-div-10-4",'style'),Output("edge-div-10-5",'style')], 
    [Input("k-select-10", 'value'),Input("edge-checkbox", 'value')])
def hide_elements_k10(k,show_edge):
    show_edge = checkToBool(show_edge)
    node_style_1 = {'display':'block'} if k>=1 else {'display':'None'};node_style_2 = {'display':'block'} if k>=2 else {'display':'None'};node_style_3 = {'display':'block'} if k>=3 else {'display':'None'};node_style_4 = {'display':'block'} if k>=4 else {'display':'None'};node_style_5 = {'display':'block'} if k>=5 else {'display':'None'}
    edge_style_1 = {'display':'block'} if show_edge and k>=1 else {'display':'None'};edge_style_2 = {'display':'block'} if show_edge and k>=2 else {'display':'None'};edge_style_3 = {'display':'block'} if show_edge and k>=3 else {'display':'None'};edge_style_4 = {'display':'block'} if show_edge and k>=4 else {'display':'None'};edge_style_5 = {'display':'block'} if show_edge and k>=5 else {'display':'None'}
    return node_style_1,node_style_2,node_style_3,node_style_4,node_style_5,edge_style_1,edge_style_2,edge_style_3,edge_style_4,edge_style_5

@app.callback(
    Output("tail-edge", 'style'),
    Input("edge-checkbox", 'value')
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
    [Output('loading-1', 'children'),
    Output('answer-table', 'children'),
    Output('submit-dwpc-val', 'style'),
    Output('submit-protein-names', 'style'),
    Output('submit-triangulator-val', 'style'),
    Output('dwpc-weight-select', 'style')],
    [Input('submit-val', 'n_clicks')],
    [State("kg-dropdown", 'value'),
    State('starts', 'value'),
    State('ends','value'),
    State("source-dropdown", 'value'), 
    State("tail-dropdown", 'value'), 
    State('tail-edge','value'),
    State('edge-checkbox', 'value'),
    State('pattern-select', 'value'),
    State("node-dropdown-1-1", 'value'),State("node-dropdown-1-2", 'value'),State("node-dropdown-1-3", 'value'),State("node-dropdown-1-4", 'value'),State("node-dropdown-1-5", 'value'),
    State("edge-dropdown-1-1", 'value'),State("edge-dropdown-1-2", 'value'),State("edge-dropdown-1-3", 'value'),State("edge-dropdown-1-4", 'value'),State("edge-dropdown-1-5", 'value'),
    State("node-dropdown-2-1", 'value'),State("node-dropdown-2-2", 'value'),State("node-dropdown-2-3", 'value'),State("node-dropdown-2-4", 'value'),State("node-dropdown-2-5", 'value'),
    State("edge-dropdown-2-1", 'value'),State("edge-dropdown-2-2", 'value'),State("edge-dropdown-2-3", 'value'),State("edge-dropdown-2-4", 'value'),State("edge-dropdown-2-5", 'value'),
    State("node-dropdown-3-1", 'value'),State("node-dropdown-3-2", 'value'),State("node-dropdown-3-3", 'value'),State("node-dropdown-3-4", 'value'),State("node-dropdown-3-5", 'value'),
    State("edge-dropdown-3-1", 'value'),State("edge-dropdown-3-2", 'value'),State("edge-dropdown-3-3", 'value'),State("edge-dropdown-3-4", 'value'),State("edge-dropdown-3-5", 'value'),
    State("node-dropdown-4-1", 'value'),State("node-dropdown-4-2", 'value'),State("node-dropdown-4-3", 'value'),State("node-dropdown-4-4", 'value'),State("node-dropdown-4-5", 'value'),
    State("edge-dropdown-4-1", 'value'),State("edge-dropdown-4-2", 'value'),State("edge-dropdown-4-3", 'value'),State("edge-dropdown-4-4", 'value'),State("edge-dropdown-4-5", 'value'),
    State("node-dropdown-5-1", 'value'),State("node-dropdown-5-2", 'value'),State("node-dropdown-5-3", 'value'),State("node-dropdown-5-4", 'value'),State("node-dropdown-5-5", 'value'),
    State("edge-dropdown-5-1", 'value'),State("edge-dropdown-5-2", 'value'),State("edge-dropdown-5-3", 'value'),State("edge-dropdown-5-4", 'value'),State("edge-dropdown-5-5", 'value'),
    State("node-dropdown-6-1", 'value'),State("node-dropdown-6-2", 'value'),State("node-dropdown-6-3", 'value'),State("node-dropdown-6-4", 'value'),State("node-dropdown-6-5", 'value'),
    State("edge-dropdown-6-1", 'value'),State("edge-dropdown-6-2", 'value'),State("edge-dropdown-6-3", 'value'),State("edge-dropdown-6-4", 'value'),State("edge-dropdown-6-5", 'value'),
    State("node-dropdown-7-1", 'value'),State("node-dropdown-7-2", 'value'),State("node-dropdown-7-3", 'value'),State("node-dropdown-7-4", 'value'),State("node-dropdown-7-5", 'value'),
    State("edge-dropdown-7-1", 'value'),State("edge-dropdown-7-2", 'value'),State("edge-dropdown-7-3", 'value'),State("edge-dropdown-7-4", 'value'),State("edge-dropdown-7-5", 'value'),
    State("node-dropdown-8-1", 'value'),State("node-dropdown-8-2", 'value'),State("node-dropdown-8-3", 'value'),State("node-dropdown-8-4", 'value'),State("node-dropdown-8-5", 'value'),
    State("edge-dropdown-8-1", 'value'),State("edge-dropdown-8-2", 'value'),State("edge-dropdown-8-3", 'value'),State("edge-dropdown-8-4", 'value'),State("edge-dropdown-8-5", 'value'),
    State("node-dropdown-9-1", 'value'),State("node-dropdown-9-2", 'value'),State("node-dropdown-9-3", 'value'),State("node-dropdown-9-4", 'value'),State("node-dropdown-9-5", 'value'),
    State("edge-dropdown-9-1", 'value'),State("edge-dropdown-9-2", 'value'),State("edge-dropdown-9-3", 'value'),State("edge-dropdown-9-4", 'value'),State("edge-dropdown-9-5", 'value'),
    State("node-dropdown-10-1", 'value'),State("node-dropdown-10-2", 'value'),State("node-dropdown-10-3", 'value'),State("node-dropdown-10-4", 'value'),State("node-dropdown-10-5", 'value'),
    State("edge-dropdown-10-1", 'value'),State("edge-dropdown-10-2", 'value'),State("edge-dropdown-10-3", 'value'),State("edge-dropdown-10-4", 'value'),State("edge-dropdown-10-5", 'value'),
    State('k-select-1', 'value'),State('k-select-2', 'value'),State('k-select-3', 'value'),State('k-select-4', 'value'),State('k-select-5', 'value'),
    State('k-select-6', 'value'),State('k-select-7', 'value'),State('k-select-8', 'value'),State('k-select-9', 'value'),State('k-select-10', 'value'),
    State('pattern-name-1', 'value'),State('pattern-name-2', 'value'),State('pattern-name-3', 'value'),State('pattern-name-4', 'value'),State('pattern-name-5', 'value'),
    State('pattern-name-6', 'value'),State('pattern-name-7', 'value'),State('pattern-name-8', 'value'),State('pattern-name-9', 'value'),State('pattern-name-10', 'value')])
def submit_path_search(n_clicks,graph_db,start_node_text,
        end_node_text,s,t,t_edges,show_edges, pattern_select,
        k1_1_nodes,k1_2_nodes,k1_3_nodes,k1_4_nodes,k1_5_nodes,
        k1_1_edges,k1_2_edges,k1_3_edges,k1_4_edges,k1_5_edges,
        k2_1_nodes,k2_2_nodes,k2_3_nodes,k2_4_nodes,k2_5_nodes,
        k2_1_edges,k2_2_edges,k2_3_edges,k2_4_edges,k2_5_edges,
        k3_1_nodes,k3_2_nodes,k3_3_nodes,k3_4_nodes,k3_5_nodes,
        k3_1_edges,k3_2_edges,k3_3_edges,k3_4_edges,k3_5_edges,
        k4_1_nodes,k4_2_nodes,k4_3_nodes,k4_4_nodes,k4_5_nodes,
        k4_1_edges,k4_2_edges,k4_3_edges,k4_4_edges,k4_5_edges,
        k5_1_nodes,k5_2_nodes,k5_3_nodes,k5_4_nodes,k5_5_nodes,
        k5_1_edges,k5_2_edges,k5_3_edges,k5_4_edges,k5_5_edges,
        k6_1_nodes,k6_2_nodes,k6_3_nodes,k6_4_nodes,k6_5_nodes,
        k6_1_edges,k6_2_edges,k6_3_edges,k6_4_edges,k6_5_edges,
        k7_1_nodes,k7_2_nodes,k7_3_nodes,k7_4_nodes,k7_5_nodes,
        k7_1_edges,k7_2_edges,k7_3_edges,k7_4_edges,k7_5_edges,
        k8_1_nodes,k8_2_nodes,k8_3_nodes,k8_4_nodes,k8_5_nodes,
        k8_1_edges,k8_2_edges,k8_3_edges,k8_4_edges,k8_5_edges,
        k9_1_nodes,k9_2_nodes,k9_3_nodes,k9_4_nodes,k9_5_nodes,
        k9_1_edges,k9_2_edges,k9_3_edges,k9_4_edges,k9_5_edges,
        k10_1_nodes,k10_2_nodes,k10_3_nodes,k10_4_nodes,k10_5_nodes,
        k10_1_edges,k10_2_edges,k10_3_edges,k10_4_edges,k10_5_edges,
        k_val_1,k_val_2,k_val_3,k_val_4,k_val_5,k_val_6,k_val_7,k_val_8,k_val_9,k_val_10,
        pattern_name_1,pattern_name_2,pattern_name_3,pattern_name_4,pattern_name_5,
        pattern_name_6,pattern_name_7,pattern_name_8,pattern_name_9,pattern_name_10):
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
    searched_edges_dict = {}
    i=0
    for pattern in pattern_names:
        if i < pattern_select:
            k_nodes = [f"{s}",f"{all_k_nodes[pattern][0]}",f"{all_k_nodes[pattern][1]}",f"{all_k_nodes[pattern][2]}",f"{all_k_nodes[pattern][3]}",f"{all_k_nodes[pattern][4]}",f"{t}"]
            wildcarded_k_nodes = ['wildcard' if x == "None" else x for x in k_nodes]
            clean_k_nodes = ['`'+x+'`' if 'biolink' in x else x for x in wildcarded_k_nodes]
            searched_nodes = {pattern:clean_k_nodes[:k_values[i]+1]+[clean_k_nodes[-1]]}
            print(searched_nodes)
            searched_nodes_dict.update(searched_nodes)
            
            if edges_bool == True:
                k_edges = [f"{all_k_edges[pattern][0]}",f"{all_k_edges[pattern][1]}",f"{all_k_edges[pattern][2]}",f"{all_k_edges[pattern][3]}",f"{all_k_edges[pattern][4]}",f"{t_edges}"]
                wildcarded_k_edges = ['wildcard' if x == "None" else x for x in k_edges]
                clean_k_edges = ['`'+x+'`' if 'biolink' in x else x for x in wildcarded_k_edges]
            else:
                clean_k_edges = ['wildcard', 'wildcard', 'wildcard', 'wildcard', 'wildcard', 'wildcard']
            searched_edges={pattern:clean_k_edges[:k_values[i]]+[clean_k_edges[-1]]}
            print(searched_edges)
            searched_edges_dict.update(searched_edges)
            i+=1
        else:
            break
    ans = Graphsearch(graph_db,start_nodes,end_nodes,searched_nodes_dict,searched_edges_dict,10000000)
    answersdf = ans.drop_duplicates()
    answers_table = dash_table.DataTable(id="answers",data=answersdf.to_dict('records'),
                        columns=[{"name": i.replace("`","").replace("biolink:",""), "id": i, "hideable": True, "selectable": [True if "node" in i else False]} for i in answersdf.columns],
                        hidden_columns=[i for i in answersdf.columns if "esnd" in i],
                        sort_action='native',
                        filter_action="native",
                        column_selectable="multi",
                        row_selectable="single",
                        selected_rows=[],
                        selected_columns=[],
                        page_size=20,
                        style_table={'overflowX': 'auto'},
                        style_header={
                            'fontWeight': "bold",
                            'whiteSpace': "normal",
                            'height': "auto"},
                        style_cell={
                            'color': "#000000",
                            'text-align': 'center'
                            #'minWidth': '90px', 
                            #'width': '90px', 
                            #'maxWidth': '90px',
                            },
                        style_data={
                            'whiteSpace': "normal",
                            'height': "auto"},
                        markdown_options={"html": True},
                        export_format="csv")
    
    return ([f"{graph_db} Search Complete!"],
            answers_table,
            {"margin-right":"1em",'display':'block'},
            {"margin-right":"1em",'display':'block'},
            {"margin-right":"1em",'display':'block'},
            {'display':'block', 'width':'5em'})

@app.callback(
    [Output('loading-2', 'children'),
    Output('start-map-output', 'value'),
    Output('start-map-div', 'style'),
    Output('end-map-output', 'value'),
    Output('end-map-div', 'style')],
    Input('term-map-val', 'n_clicks'),
    [
    State('kg-dropdown', 'value'),
    State('starts', 'value'),
    State('ends','value'),
    State("source-dropdown", 'value'), 
    State("tail-dropdown", 'value')]
    )
def KGNodeMapper(n_clicks, graph_db, start_terms, end_terms, start_label, end_label):
    if(n_clicks <= 0): return ""
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
    G = py2neo.Graph(link)
   # nodes_output = {"search term":[], "node name":[], "node id":[], "node degree":[]}
    start_message = ""
    end_message = ""
    for term in starts:
        nodes_output = {"search term":[], "node name":[], "node id":[], "node degree":[]}
        a=len(nodes_output['node name'])
        if graph_db == "ROBOKOP":
            query = f"MATCH (n{':'+startLabel if startLabel != 'wildcard' else ''}) WHERE apoc.meta.type(n.name) = 'STRING' AND toLower(n.name) CONTAINS \"{term.lower()}\" CALL {'{'}WITH n RETURN apoc.node.degree(n) AS degree{'}'} RETURN n.name, n.id, degree"
        else:
            query = f"MATCH (n{':'+startLabel if startLabel != 'wildcard' else ''}) WHERE toLower(n.name) CONTAINS \"{term.lower()}\" RETURN n.name, n.identifier"
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
                start_message+=f"'{term}' found! ID: {nodes_output['node id'][0]}, Degree: {nodes_output['node degree'][0]}\n"
            else:
                start_message+=f"'{term}' found! ID: {nodes_output['node id'][0]}\n"
        else:
            if graph_db == "ROBOKOP":
                start_message+=f"'{term}' not in {graph_db} under '{start_label}' category, try instead {str([str(x)+'('+str(y)+')' for x,y in zip(nodes_output['node name'],nodes_output['node degree'])])}\n"
            else:
                start_message+=f"'{term}' not in {graph_db} under '{start_label}' category, try instead {str([str(x) for x in nodes_output['node name']])}\n"
    for term in ends:
        nodes_output = {"search term":[], "node name":[], "node id":[], "node degree":[]}
        a=len(nodes_output['node name'])
        if graph_db == "ROBOKOP":
            query = f"MATCH (n{':'+endLabel if endLabel != 'wildcard' else ''}) WHERE apoc.meta.type(n.name) = 'STRING' AND toLower(n.name) CONTAINS \"{term.lower()}\" CALL {'{'}WITH n RETURN apoc.node.degree(n) AS degree{'}'} RETURN n.name, n.id, degree"
        else:
            query = f"MATCH (n{':'+endLabel if endLabel != 'wildcard' else ''}) WHERE toLower(n.name) CONTAINS \"{term.lower()}\" RETURN n.name, n.identifier"
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
    
    return ([f"{graph_db} Term Mapping Complete!"],start_message,{"display":'block'},end_message,{"display":'block'})

@app.callback(
    [Output('loading-3','children'),
    Output('dwpc-table', 'children'),
    Output('submit-pca-vis', 'style')],
    Input('submit-dwpc-val', 'n_clicks'),
    [State('answer-table', 'children'),
    State("source-dropdown", 'value'), 
    State("tail-dropdown", 'value'),
    State("dwpc-weight-select", 'value')])
def CalculateDWPC(n_clicks,answer_datatable,start_type,end_type,w):
    if(n_clicks <= 0): return ""
    #dff = pd.DataFrame.from_dict(answer_datatable)
    dff = pd.DataFrame(answer_datatable['props']['data'])
    PDP = []
    metapathnames=[]
    W = w
    column_names = list(dff)
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
    gkindex=["node0:`"+start_type+"`",node_columns[-1]]
    gk = pd.pivot_table(dff, index=gkindex,columns=["Metapath Name"], values="PathDegreeProduct", aggfunc=sum)
    gk = gk.fillna(0)
    gk.reset_index(inplace=True)
    first=gk.columns[0][6:]
    second=gk.columns[1][6:]
    gk.rename(columns={gk.columns[0]:first,gk.columns[1]:second}, inplace = True)
    dwpc_table = dash_table.DataTable(id="dwpc",data=gk.to_dict('records'),
                        columns=[{"name": i.replace("`","").replace("biolink:",""), "id": i, "hideable": True} for i in gk.columns],
                        sort_action='native',
                        row_selectable="multi",
                        selected_rows=[],
                        page_size=20,
                        style_table={'overflowX': 'auto'},
                        style_cell={'color': "#000000",
                            #'minWidth': '60px', 
                            #'width': '60px', 
                            #'maxWidth': '60px',
                            'whiteSpace': "normal",
                            'height': "auto"},
                        style_header={
                            'fontWeight': "bold"},
                        #style_data={
                        #    'whiteSpace': "normal",
                         #   'height': "auto"},
                        export_format="csv")
    style={'display':'block'}
    return ["Finished Calculating Degree-Weighted Path Counts!"],dwpc_table,style
    
@app.callback([Output('pca-fig-2comp', 'figure'),
    Output('pca-fig-3comp', 'figure'),
    Output('pca-fig-2comp', 'style'),
    Output('pca-fig-3comp', 'style')],
    Input('submit-pca-vis', 'n_clicks'),
    [State('dwpc-table', 'children'),
    State('dwpc', 'selected_rows')])
def VisualizePCA(n_clicks,dwpc_datatable,positive_rows):
    if(n_clicks <= 0): return ""
    gk = pd.DataFrame(dwpc_datatable['props']['data'])
    positives=[]
    for i in positive_rows:
        pos=f"{gk.iat[i,0]}-{gk.iat[i,1]}"
        positives.append(pos)
    pca2comp=PCA.performPCA(gk,positives,2)
    pca3comp=PCA.performPCA(gk,positives,3)
    style2comp={'display':'block'}#,'width':'1000px','height':'1000px'}
    style3comp={'display':f"{'None' if pca3comp=='' else 'block'}"}

    return [pca2comp,pca3comp,style2comp,style3comp]

@app.callback(
    [Output('answers', 'data'), Output('answers', 'columns'), Output('loading-4', 'children')],
    [Input('submit-protein-names', 'n_clicks'), Input('submit-triangulator-val', 'n_clicks')],
    [State('answer-table', 'children'), State('answers', 'selected_columns')])
def UpdateAnswers(protein_names_clicks,triangulator_clicks,answer_datatable,selected_columns):
    button_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    print(button_id)
    if button_id == 'submit-protein-names' and protein_names_clicks:
        #Get protein names from HGNC
        dff = pd.DataFrame.from_dict(answer_datatable['props']['data'])
        gene_cols = [col for col in dff.columns if ":Gene" in col]
        print(dff.columns)
        if len(gene_cols) == 0: return dff.to_dict('records'), [{"name": i, "id": i, "hideable": True, "selectable": [True if "node" in i else False]} for i in dff.columns], "No \"Gene\" column detected."

        genes = dict()
        proteins = list()
        protname_df = pd.read_csv("hgnc_complete_set.csv", encoding="utf-8")

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
                    #print(gene + " maps to " + protein)

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
            print(dff.columns)

        ammended_answers = dff.to_dict('records')
        ammended_columns = [{"name": i, "id": i, "hideable": True, "selectable": [True if "node" in i else False]} for i in dff.columns]
        if len(failed_proteins) != 0:
            fails = ''.join([str(x)+", " for x in failed_proteins])
            message = f"Finished retrieving protein names!\nFailed on {fails.rstrip(', ')}."
        else:
            message = "Finished retrieving protein names!"

        return ammended_answers, ammended_columns, message
    elif button_id == 'submit-triangulator-val' and triangulator_clicks:
        print(selected_columns)
        #Find number of co-mentioning abstracts from Pubmed for 2 or 3 terms.
        dff = pd.DataFrame.from_dict(answer_datatable['props']['data'])
        expand = True
        number = len(selected_columns)
        two_term_dict = dict()
        three_term_dict = dict()
        comention_counts_1_2 = list()
        comention_counts_1_3 = list()
        comention_counts_2_3 = list()
        comention_counts_1_2_3 = list()
        URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        if number not in [2,3]:
            return dff.to_dict('records'), [{"name": i, "id": i, "hideable": True, "selectable": [True if "node" in i else False]} for i in dff.columns], "Please select 2 or 3 node columns for PubMed search."
        print("Running PubMed Check")
        if number == 2:
            print('number=2')
            Term1=selected_columns[0].replace('`','').replace('biolink:','')
            Term2=selected_columns[1].replace('`','').replace('biolink:','')
            if f"{Term1}-{Term2} counts" not in dff.columns:
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
                    comention_counts_1_2.append(f"{str(cnt)} <a href='https://pubmed.ncbi.nlm.nih.gov/?term={term1} AND {term2}' target='_blank' rel='noopener noreferrer'>[Link]</a>")

                dff.insert(0, f"{Term1}-{Term2} counts", comention_counts_1_2)

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

                if f"{Term1}-{Term2} counts" not in dff.columns:
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
                    comention_counts_1_2.append(f"{str(cnt)} <a href='https://pubmed.ncbi.nlm.nih.gov/?term={term1} AND {term2}' target='_blank' rel='noopener noreferrer'>[Link]</a>")

                if f"{Term1}-{Term3} counts" not in dff.columns:
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
                    comention_counts_1_3.append(f"{str(cnt)} <a href='https://pubmed.ncbi.nlm.nih.gov/?term={term1} AND {term3}' target='_blank' rel='noopener noreferrer'>[Link]</a>")
                
                if f"{Term2}-{Term3} counts" not in dff.columns:
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
                    comention_counts_2_3.append(f"{str(cnt)} <a href='https://pubmed.ncbi.nlm.nih.gov/?term={term2} AND {term3}' target='_blank' rel='noopener noreferrer'>[Link]</a>")
                
                if f"{Term1}-{Term2}-{Term3} counts" not in dff.columns:
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
                    comention_counts_1_2_3.append(f"{str(cnt)} [<a href='https://pubmed.ncbi.nlm.nih.gov/?term={term1} AND {term2} AND {term3}' target='_blank' rel='noopener noreferrer'>[Link]]</a>")
                
            if f"{Term1}-{Term2} counts" not in dff.columns:
                dff.insert(0, f"{Term1}-{Term2} counts", comention_counts_1_2)
            if f"{Term1}-{Term3} counts" not in dff.columns:
                dff.insert(0, f"{Term1}-{Term3} counts", comention_counts_1_3)
            if f"{Term2}-{Term3} counts" not in dff.columns:
                dff.insert(0, f"{Term2}-{Term3} counts", comention_counts_2_3)
            if f"{Term1}-{Term2}-{Term3} counts" not in dff.columns:
                dff.insert(0, f"{Term1}-{Term2}-{Term3} counts", comention_counts_1_2_3)

        ammended_answers = dff.to_dict('records')
        ammended_columns = [{"name": i, "id": i, "hideable": True, "selectable": False, "presentation":"markdown"} if " counts" in i else {"name": i, "id": i, "hideable": True, "selectable": [True if "node" in i and " counts" not in i else False]} for i in dff.columns]
        message = "Finished retrieving PubMed Abstract Co-Mentions!"
        return (ammended_answers, ammended_columns, message)
    else:
        raise dash.exceptions.PreventUpdate
        
 #############################################################    

if __name__ == '__main__':
    app.run_server()
    #app.run_server(host='0.0.0.0', port=80,debug=True) #For production
