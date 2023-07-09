# ExEmPLAR: AOP/COP Path-Extractor and Knowledge Graph Interface
Construct Adverse/Clinical Outcome Pathway queries and extract path information from ROBOKOP or other Biomedical Knowledge Graphs
## Link to online ExEmPLAR application: https://www.exemplar.mml.unc.edu
## Visual User Guide: https://www.exemplar.mml.unc.edu/user_guide
## Publication: To be included upon publication.

## Instructions for setting up local ExEmPLAR instance:
  1. Clone "AOP-COP-Path-Extractor" Github repository
  2. Create new P



## Description
Biomedical Knowledge Graph Sources\
We developed ExEmPLAR around the Neo4j graph database platform (https://neo4j.com/). The tool is designed to operate on knowledge graphs implemented in Neo4j such that any new Neo4j knowledge graph could be added with minimal development. Biomedical KGs currently implemented in ExEmPLAR include:\
•	ROBOKOP\
•	Hetionet\
•	CompToxAI\
•	SCENTKOP

### Query Construction Tool
The primary functionality of ExEmPLAR is a graphical user interface (GUI) for rapidly constructing and editing queries in the Cypher query language (https://neo4j.com/developer/cypher/) and executing those queries on knowledge graphs hosted on Neo4j databases. This GUI for Cypher query building is critical for opening the use of biomedical knowledge graphs to the broader biomedical research community because it allows users to experiment with highly tunable queries without developing specialized knowledge about Neo4j or the Cypher query language. User-constructed queries are automatically processed to maximize flexibility, while maintaining query efficiency. To limit query load on the Neo4j graph databases, ExEmPLAR queries are designed to time out after 60 seconds of work.\
The query construction interface allows users to construct queries that traverse a KG from a specified Start Node type to a specified End Node type. Users may construct up to 10 unique paths (P1-P10) from Start to End, with each individual path comprising up to 5 intermediate nodes with user-defined type (Levels 1-5). Start, End, and Level 1-5 nodes all include a text box for users to define specific node names or IDs that a query pattern must include. To prevent against long-running, open-ended queries, users must define at least one specific node name or ID for either the Start or End nodes. In addition to defining node types and entities, users may also define specific predicates between nodes by selecting the “Use Edges” checkbox. Selecting the “Get Result MetaData” checkbox will return additional node and edge properties in the Answer Table.
### Node Search Function
Because users may not know the exact names or IDs of nodes in a KG, ExEmPLAR includes a function to search the selected KG for nodes names. Users can type partial or full node names in the “Starting Points” or “Ending Points” text boxes and select “Check for Terms in Knowledge Graph” to search for nodes of the defined type which contain the searched string in a case-insensitive manner. If the searched string is found exactly as typed, a message will appear in the result text box saying “{searched string} found!” If the searched string is found in other nodes, the suggested node names, and their node degree (number of connect edges), will be shown. These suggestions could be copy-and-pasted into the search box.
### Answer Table and Visualization
Answers to users’ queries will appear in tabular form below the query construction interface. Each row in the answer table represents a single answer subgraph. Each answer row lists the user-generated query path (P1-P10) corresponding to the answer. Columns not involved in a row’s corresponding metapath will be instead populated with a “?” character. The answer table can be sorted, filtered, and hidden by preference. Hidden columns can be displayed by clicking the “Toggle Columns” button and selecting the desired column. The table can be downloaded as a CSV file by clicking the “Export” button.\
If the “Get Result MetaData” checkbox was selected, the text of node and edge properties will be hidden by default. To view these properties in the answer table, simply unhide the columns as described above. Otherwise, node and edge properties can be viewed by hovering over the node or edge name with the mouse cursor.
To visualize individual answer subgraphs, select the checkbox on the answer row. A subgraph figure will be generated using the NetworkX Python library (https://networkx.org/). The subgraph figure is color-coded, according to node type. Multiple answer rows can be added to build out a larger network based on a selected subset of answers. This function helps highlights critical answers and can aid hypothesis communication since the figure can be downloaded as an image file.
### Ranking by PubMed Abstract Co-Mentions
Due to the highly interconnected nature of biomedical KGs, longer query paths tend to return numerous answer subgraphs. To reason over potentially thousands of unique answers, an answer ranking system is needed. ExEmPLAR uses a simple, yet informative, ranking system based on the number of abstracts available on PubMed, the largest freely available biomedical literature repository (https://pubmed.ncbi.nlm.nih.gov/), which co-mention node names from KG answers.\ 
Users can select the checkboxes on any 2 or 3 columns in the answer table and click the “Get PubMed Abstracts Co-Mentions” button to use the E-utilities API (https://www.ncbi.nlm.nih.gov/books/NBK25501/) to return the count of abstracts co-mentioning terms in those columns. When 2 columns are selected, only the counts between terms in the columns are returned. When 3 columns are selected, 4 abstract counts are returned: node(A)-node(B) counts, node(A)-node(C) counts, node(B)-node(C) counts, and the counts co-mention node(A), node(B), and node(C). ExEmPLAR appends new columns to the answer table that contain these count values and creates a hidden column with both the count and a link to PubMed to view the co-mentioning abstracts behind the counts. Users can then sort the answer table using these count columns to prioritize answer subgraphs with high, or low, co-mention counts.\
Because the user can select the columns used, this ranking system is highly tunable to user needs. Furthermore, the user can choose to prioritize either well-known or under-described relationships between nodes depending on the context (e.g., prioritizing strong support or novelty in answers). Returning co-mention counts for 3 columns provides the additional benefit of allowing the user to “triangulate” support between the nodes in the columns. For example, when co-mentions exist for node(A)-node(B), node(A)-node(C), and node(B)-node(C) pairs, but no co-mentions exist for the node(A)-node(B)-node(C) triplet, one could infer that the individual facts between any 2 of A, B, and C are understood, but no known mechanism or hypothesis exists that encompasses all 3 nodes. Another “triangulation” approach is imputing a potentially novel relationship between node(A) and node(C) when co-mention counts exist for node(A)-node(B) and node(B)-node(C) pairs. Historically, a version of this “ABC triangle” method was applied to a literature citation network to predict a therapeutic relationship between fish oil and Raynaud’s syndrome (Swanson, 1986), and later, magnesium and migraine (Swanson, 1988). More recently, we used this method in combination with ROBOKOP to explore biological mechanisms behind metal implant toxicity (Beasley et al., 2022).\
Since this ranking system is sensitive to node names and genes in biomedical KGs are often represented by their gene symbols, ExEmPLAR includes a function to convert gene symbols to the corresponding protein name according to the HUGO Gene Nomenclature Committee (Tweedie et al., 2021). These protein names can be used to improve specificity of the PubMed co-mention search and can help avoid situations where gene symbols match English words (e.g., CAT gene encodes “catalase” protein, but PubMed search would return counts for abstracts mentioning the animal “cat”).
### Answer Embeddings and Principal Component Clustering
A degree-weighted path count (DWPC) embedding for Start-End node pairs can be generated from the ExEmPLAR answer table. DWPC embeds the count of each metapath, or specific sequence of node and edge types between start and end nodes, and down-weights the contribution of paths through highly connected nodes. The details of the DWPC algorithm have been described previously (Himmelstein & Baranzini, 2015) and machine learning using DWPC features been applied to drug repurposing (Himmelstein et al., 2017) and AD risk factor gene prediction (Binder et al., 2022).  
