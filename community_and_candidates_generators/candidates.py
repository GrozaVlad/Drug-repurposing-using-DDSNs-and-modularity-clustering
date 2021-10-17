import psycopg2 as psycopg2
from string import Template

conn = psycopg2.connect(
    host="localhost",
    database="drugbank",
    user="vlad",
    password="vlad",
    port=5433)

drugBanks = ['5.0.9']
# drugBanks = ['3.0','4.1','4.2','4.3','4.5.0','5.0.0','5.0.1','5.0.2','5.0.3','5.0.4','5.0.5','5.0.6','5.0.7','5.0.8','5.0.9','5.0.10','5.1.0','5.1.8']
# resolutionValues = ['0.1','0.4','0.7','1.0','1.4','1.7','2.0','100']
resolutionValues = ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9', '1.0',
'1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8', '1.9', '2.0',
'2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8', '2.9', '3.0',
'3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '3.9', '4.0',
'4.1', '4.2', '4.3', '4.4', '4.5', '4.6', '4.7', '4.8', '4.9', '5.0']
# drugBanks = ['4.1','4.2','4.3','4.5.0','5.0.0','5.0.1','5.0.2','5.0.3','5.0.4']

# cursor = conn.cursor()
# maxModularityQuery = 'SELECT MAX(modularity_class) FROM public.drugs_resolution WHERE drugbank_version=%s AND resolution=%s'
# cursor.execute(maxModularityQuery,(drugBanks[0],resolutionValues[0]))
#
# # display the PostgreSQL database server version
# maxModularity = cursor.fetchall()
# print(maxModularity[0][0])


for a in range(0, len(drugBanks)):
    for b in range(0, len(resolutionValues)):
        cursor = conn.cursor()
        maxModularityQuery = 'SELECT MAX(modularity_class) FROM public.drugs_resolution WHERE drugbank_version=%s AND resolution=%s'
        # maxModularityQuery = 'SELECT MAX(modularity_class) FROM public.drugs_resolution WHERE drugbank_version=%s AND resolution=%s'

        cursor.execute(maxModularityQuery, (drugBanks[a], resolutionValues[b]))

        # display the PostgreSQL database server version
        maxModularity = cursor.fetchall()
        maxModularityValue = int(maxModularity[0][0])

        drugCommunityDistribution = {}
        drugCommunities = {}
        print(maxModularityValue)
        for i in range(0, maxModularityValue):
            communityDistribution = {
                "V": set(),
                "M": set(),
                "D": set(),
                "B": set(),
                "S": set(),
                "N": set(),
                "L": set(),
                "G": set(),
                "J": set(),
                "P": set(),
                "A": set(),
                "R": set(),
                "C": set(),
                "H": set()
            }

            #     i = 56
            cursor = conn.cursor()

            # Drugbank from the db with genes that do not care about the interaction
            # t = """	SELECT drugs_resolution.name, drugs_resolution.modularity_class,drugs.atc_code as first_letter FROM(SELECT * FROM
            # drugs_resolution
            # WHERE drugbank_version = %s
            # AND modularity_class = %s
            # AND drugs_resolution.resolution = %s) as drugs_resolution left join
            # (SELECT * FROM all_drugs
            # WHERE CARDINALITY(atc_code) != 0
            # AND cardinality(gene_target_ids)!= 0
            # AND drugbank_version = %s) as drugs on drugs_resolution.name = drugs.name
            # """

            # Drugbank from the db with genes that have the same interaction
            t = """	SELECT drugs_resolution.name, drugs_resolution.modularity_class,drugs.atc_code as first_letter FROM(SELECT * FROM
            drugs_resolution 
            WHERE drugbank_version = %s 
            AND CAST(modularity_class as INTEGER) = %s
            AND drugs_resolution.resolution = %s) as drugs_resolution left join
            (SELECT * FROM all_drugs_info 
            WHERE CARDINALITY(atc_code) != 0 
            AND cardinality(gene_target_ids_array)!= 0
            AND drugbank_version = %s) as drugs on drugs_resolution.name = drugs.name
            """


            cursor.execute(t, (drugBanks[a], i, resolutionValues[b], drugBanks[a]))

            # display the PostgreSQL database server version
            drugs = cursor.fetchall()
            # print(drugs)
            drugCommunities[i] = drugs
            # close the communication with the PostgreSQL
            cursor.close()
            print(drugs)
            for j in range(0, len(drugs)):
                for k in range(0, len(drugs[j][2])):
                    atcCode = drugs[j][2][k]
                    firstAtcLetter = atcCode[0:1]
                    communityDistribution[firstAtcLetter].add(drugs[j][0])

            drugCommunityDistribution[i] = communityDistribution

        excludedDrugsList = list()

        for i in range(0, maxModularityValue):
            modularity = i

            maxCount = 0
            maxKey = 'V'
            for key in drugCommunityDistribution[modularity]:
                #     print(key , len(drugCommunityDistribution[modularity][key]))
                if maxCount < len(drugCommunityDistribution[modularity][key]):
                    maxCount = len(drugCommunityDistribution[modularity][key])
                    maxKey = key


            # print(maxCount)
            #     print(maxKey)

            ### Get all the drugs that are not in the exclusion atc group

            def myFunc(x):
                for val in drugCommunityDistribution[modularity][maxKey]:
                    if x[0] == val:
                        return False

                return True


            excludedDrugs = list(filter(myFunc, drugCommunities[modularity]))

            # for x in excludedDrugs:
            #   print(x)
            for key in excludedDrugs:
                key = list(key)
                key.append(maxKey)
                key = tuple(key)
                excludedDrugsList.append(key)
            #     print(key)

            # type()


        repurposedDrugs = list()
        # print(excludedDrugsList)
        for i in range(0, len(excludedDrugsList)):
            element = excludedDrugsList[i]

            #     print(element)
            #     print(element[0])

            # query = """SELECT atc_code FROM public.drugs WHERE name = '""" + element[0] + """';"""
            query = """SELECT atc_code FROM public.all_drugs_info WHERE drugbank_version = '5.1.8' AND name = '""" + element[0] + """';"""

            #     print(query)

            cursor = conn.cursor()
            cursor.execute(query)

            # display the PostgreSQL database server version
            updated_drug = cursor.fetchall()
            if len(updated_drug) > 0:
                for i in range(0, len(updated_drug[0][0])):
                    atcCode = updated_drug[0][0][i]
                    firstAtcLetter = atcCode[0:1]
                    #             print(firstAtcLetter)
                    if firstAtcLetter == element[3]:
                        repurposedDrugs.append(element)
                        break

        cursor.execute(
            """INSERT INTO public.drug_results(
	        max_modularity, candidates_number, candidates_validated_number, resolution, drugbank_version, candidates, candidates_validated)VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (maxModularityValue,len(excludedDrugsList),len(repurposedDrugs),resolutionValues[b], drugBanks[a],  excludedDrugsList, repurposedDrugs))

        conn.commit()
        cursor.close()
        print(len(excludedDrugsList),repurposedDrugs)
        print(drugBanks[a], resolutionValues[b])


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.

conn.close()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
