import json
import csv
import itertools
import sys
import pandas as pd
import time
from SPARQLWrapper import SPARQLWrapper, JSON

"""
This file takes a csv-file or txt-file and convert it to JSON-file. For a file name Words_test.txt in the same folder as this file, 
You can run it in the terminal by 
$ python3 ConvertToJSON.py Words_test.txt
The output is a JSON-file  Words_test.json
Then access the JSON-file with the following code:

>> wordToSimilarWordsMap = {}
>> with open(sys.argv[1], "r") as read_file:
>>    data = json.load(read_file)
>>    for wordObj in data:
>>        wordToSimilarWordsMap[wordObj['word']] = [wordObj['entity'], wordObj['lexeme'],  wordObj['verbs']]

>> print(wordToSimilarWordsMap['sister'])
{['L3626', 'L3626'], ['sister', 'sisters'], ['noun', 'noun']}
{'

"""

print('This is the path to your file: ', sys.argv[0])
print('This is the file your going to convert: ', sys.argv[1])

full_data = []
if sys.argv[1].endswith('.csv'):
    with open(sys.argv[1], newline='', encoding="utf-8") as csvfile:
        data = csv.reader(csvfile, delimiter=' ', quotechar='|')
        for row in data:
            new_row = [line.split(",") for line in row]
            new_row = list(itertools.chain.from_iterable(new_row))
            full_data.append(new_row)

elif sys.argv[1].endswith('.txt'):
    with open(sys.argv[1], 'r', encoding="utf-8") as file:
        data = file.read().split('\n')
        for row in data:
            full_data.append(row.strip().split(","))

# Knowledge graph
def get_sparql_dataframe(service, query):
    """
    Helper function to convert SPARQL results into a Pandas data frame.
    """
    sparql = SPARQLWrapper(service)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result = sparql.query()

    processed_results = json.load(result.response)
    cols = processed_results['head']['vars']

    out = []
    for row in processed_results['results']['bindings']:
        item = []
        for c in cols:
            item.append(row.get(c, {}).get('value'))
        out.append(item)
    # pd.DataFrame(out, columns=cols),
    return out


endpoint = "https://query.wikidata.org/sparql"

sparql =  """
    SELECT ?lexeme ?representation ?lexcatLabel ?lemma {
       ?form ontolex:representation "TO_REPLACE"@en .
       ?lexeme ontolex:lexicalForm / ontolex:representation "TO_REPLACE" @en ; 
               ontolex:lexicalForm / ontolex:representation ?representation .
       ?lexeme wikibase:lexicalCategory ?lexcat .
       ?lexeme ontolex:lexicalForm ?form .
       ?lexeme wikibase:lemma ?lemma .
       #OPTIONAL { ?lexeme ontolex:sense ?sense . }
       SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }

"""

data = []
for i in range(1, len(full_data)):
    for j in range(len(full_data[i])):
        success = False
        while not success:
            try:
                m = {}
                m['word'] = full_data[i][j]
                m['lexeme'] = get_sparql_dataframe(endpoint, sparql.replace("TO_REPLACE", full_data[i][j]))
                m['entity'] = [element[0][-5:] for element in m['lexeme']]  # Can't avoid empty lists
                m['verbs'] = [element[2] for element in m['lexeme']]
                m['lexeme'] = [element[1] for element in m['lexeme']]
                if not m['lexeme']:
                    m['lexeme'].append(full_data[i][j])  # Adds the main word to the list to avoid empty lists
                    m['entity'].append('1')
                    m['verbs'].append('None')
                data.append(m)
                success = True
            except Exception as err:
                print("Got error %s for words: %s, retrying in 5 seconds" % (str(err), full_data[i][j]))
                time.sleep(5)
    print('Progress: %.2f %s' % (i/(len(full_data) - 1.0) * 100, "%"))

#print(data)
# sys.exit(0)
# Save as JSON-file
with open((sys.argv[1]).replace(".csv","_full.json").replace(".txt","_full.json"), "w", encoding='utf-8') as write_file:
    json.dump(data, write_file, ensure_ascii=False)

print('The name of the new file is: ', (sys.argv[1]).replace(".csv",".json").replace(".txt",".json"))
