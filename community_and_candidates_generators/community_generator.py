import psycopg2 as psycopg2
import pandas as pd
import networkx as nx

conn = psycopg2.connect(
    host="localhost",
    database="drugbank",
    user="drugbank",
    password="drugbank",
    port=5433)

drugbanks = ['5.0.9']
# drugbanks = ['3.0','4.1','4.2','4.3','4.5.0','5.0.0','5.0.1','5.0.2','5.0.3','5.0.4','5.0.5','5.0.6','5.0.7','5.0.8','5.0.9','5.0.10','5.1.0','5.1.8']
# drugbanks = ['4.1','4.2','4.3','4.5.0','5.0.0','5.0.1','5.0.2','5.0.3','5.0.4']
# drugbanks = ['5.0.9','5.0.10','5.1.0']

for z in range(0, len(drugbanks)):
    drugbankVersion = drugbanks[z]
    # FETCH DRUGS
    # execute a statement
    cursor = conn.cursor()
    cursor.execute('SELECT  name, cas, gene_target_ids_array, smiles_code, inchi_code, inchi_key, molecular_formula, atc_code FROM public.all_drugs_info WHERE cardinality(gene_target_ids_array)!= 0 AND CARDINALITY(atc_code) != 0  AND drugbank_version = %s',
        (drugbankVersion,))

    # display the PostgreSQL database server version
    drugs = cursor.fetchall()

    # close the communication with the PostgreSQL
    cursor.close()

    #     print(drugs)
    df_drugs = pd.DataFrame(drugs)
    # print(df_drugs[0].to_numpy())
    drug_nodes = df_drugs[0].to_numpy()
    edges = []
    #     for gene in genes:
    #         for drug in gene[3]:
    #             edges.append((gene[1],drug))

    for i in range(0, len(drugs)):
        k = i + 1
        for j in range(k, len(drugs)):
            weight = 0
            # print(drugs[i][3])
            for gene in drugs[i][2]:
                for gene2 in drugs[j][2]:
                    # print(gene)
                    if gene[1] and gene2[1]:
                        if gene[0] == gene2[0] and gene[1] == gene2[1]:
                            weight += 1

            if weight > 0:
                # print((drugs[i][0], drugs[j][0], weight))
                # print()
                edges.append((drugs[i][0], drugs[j][0], weight))

    B = nx.Graph()
    # Add nodes with the node attribute \"bipartite\"
    #     B.add_nodes_from(gene_nodes) #, bipartite=0
    B.add_nodes_from(drug_nodes)  # , bipartite=1
    # Add edges only between nodes of opposite node sets
    B.add_weighted_edges_from(edges)
    B.degree()
    from networkx.algorithms import bipartite, community
    from cdlib import algorithms


    G = bipartite.weighted_projected_graph(B, drug_nodes,ratio=False)
# D = bipartite.projected_graph(B, gene_nodes, multigraph=True)
#     nx.write_gexf(G, "./test_project_drugs_weighted_projection_5.1.8.gexf")
    resolutionValues = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,
                        1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.0,
                        2.1,2.2,2.3,2.4,2.5,2.6,2.7,2.8,2.9,3.0,
                        3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.8,3.9,4.0,
                        4.1,4.2,4.3,4.4,4.5,4.6,4.7,4.8,4.9,5.0]
    for k in range(0,len(resolutionValues)):

        coms = algorithms.louvain(G, weight='weight', resolution = resolutionValues[k])
        print(len(coms.communities),resolutionValues[k],drugbankVersion)
        cursor = conn.cursor()

        for i in range(0,len(coms.communities)):
            for j in range (0, len(coms.communities[i])):
                cursor.execute("INSERT INTO  public.drugs_resolution (name, drugbank_version, resolution, modularity_class) VALUES (%s, %s, %s, %s)",
                      (coms.communities[i][j], drugbankVersion, resolutionValues[k], i))

        conn.commit()
        cursor.close()

conn.close()


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
