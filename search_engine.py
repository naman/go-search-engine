from porter_stemmer import PorterStemmer
import os
import re
import sys
import math
import json


def load_stop_words():
    f = open(sys.argv[2])
    for word in f:
        stop_words.append(word.strip())


def add_to_dictionary(docname, term_frequency, position, word):
    if word not in dictionary.keys():  # or dictionary.keys()
        # print "Creating a new dictionary entry!"
        posting = {
            'name': docname,
            'frequency': 1,
            'tf_idf_weight': 0,
            'positions': [position]
        }

        dictionary[word] = [posting]  # creating postings list
    else:
        present = False
        for x in dictionary[word]:
            if x['name'] == docname:
                x['frequency'] += 1
                x['positions'].append(position)
                present = True
                break
            else:
                present = False

        if not present:  # doc not present in the term index
            # print "Creating a new dictionary entry!"
            posting = {
                'name': docname,
                'frequency': term_frequency,
                'tf_idf_weight': 0,
                'positions': [position]
            }

            dictionary[word].append(posting)


def hasNumbers(inputString):
    return bool(re.search(r'\d', inputString))


def normalize():
    print "Calculating idf weights for each term(in all documents)!"
    idf_weights = {}

    N = 0  # 101 documents
    for file_name in os.listdir(path_to_documents):
        if file_name.endswith(".txt"):
            N += 1

    for term in dictionary:
        df = len(dictionary[term])
        idf = math.log10(N / float(df))
        idf_weights[term] = idf

    print "Calculating term frequencies for a term in each doc."
    for file_name in os.listdir(path_to_documents):
        if file_name.endswith(".txt"):
            doc_vector = []
            for term in dictionary:  # x is unknown term, we dont care
                for doc in dictionary[term]:
                    if doc['name'] == file_name:
                        frequency = doc['frequency']
                        doc_vector.append(doc['frequency'])
                        break
            # magnitude of doc_vector
            D = math.sqrt(sum([x**2 for x in doc_vector]))
            # scoring of tf-idf for a term in each doc
            for term in dictionary:
                for doc in dictionary[term]:
                    if doc['name'] == file_name:
                        frequency = doc['frequency']
                        tf = frequency / float(D)

                        # tf = frequency
                        # w_tf = 0
                        # if tf > 0:
                        #     w_tf = 1 + math.log10(tf)
                        #
                        # idf is constant for all the docs a term appears in
                        idf = idf_weights[term]
                        # score for each term in doc
                        doc['tf_idf_weight'] = tf * idf
                        break


def build_index():
    for file_name in os.listdir(path_to_documents):
        if file_name.endswith(".txt"):
            f = open(path_to_documents + file_name)
            term_frequency = 0
            position = 0
            for line in f:
                words_in_line = clean_split(line)

                if len(words_in_line) > 1:
                    for word in words_in_line:
                        if (word is '') or (word in stop_words) or (hasNumbers(word)):
                            continue
                        else:
                            word = porter.stem(word, 0, len(word) - 1)
                            position += 1
                            term_frequency += 1
                            add_to_dictionary(
                                file_name, term_frequency, position, word)
            # break
            f.close()


def clean_split(string):
    return re.split('|'.join(map(re.escape, delimiters)), string.lower().strip())


def loadDocuments():
    os.system(
        "wget -nd -r -P ./Documents -A txt http://www.textfiles.com/computers/DOCUMENTATION/")


def write_inverted_index_to_file():
    with open(sys.argv[1], 'w') as outfile:
        json.dump(dictionary, outfile, sort_keys=True, indent=4)


def intersection(lists):
    try:
        intersected = set(lists[0]).intersection(*lists)
    except ValueError:
        intersected = set()  # empty
    return list(intersected)


def MultiWordQ(words_in_query):
    all_results = []

    for query in words_in_query:
        query = porter.stem(query, 0, len(query) - 1)
        if (query is '') or (query in stop_words) or (hasNumbers(query)) or (query not in dictionary):
            print query, "word is not in any document."
            continue
        else:
            for x in dictionary[query]:
                all_results.append(x['name'])

    final_results = list(set(all_results))

    if len(final_results) == 0:
        print "Sorry! No results found!"

    for x in xrange(len(final_results)):
        print "[" + str(x + 1) + "]", "in", final_results[x]


def OneWordQ(query):
    # or dictionary.keys()
    query = porter.stem(query, 0, len(query) - 1)
    if (query is '') or (query in stop_words) or (hasNumbers(query)) or (query not in dictionary):
        # short cicruiting at its best in python :D
        print "Sorry! No results found!"
    else:
        rank = []
        for x in dictionary[query]:
            rank.append(x['tf_idf_weight'])
        print "Found", len(rank), "results. Sorted with relevance!"

        rank = sorted(rank)
        for x in xrange(len(rank)):
            for result in dictionary[query]:
                if rank[x] == result['tf_idf_weight']:
                    print "[" + str(x + 1) + "]", "in", result['name'], result['frequency'], "times. Score:[", result['tf_idf_weight'], "]"
                    break


def PhraseQ(words_in_query):
    all_results = []

    for query in words_in_query:
        if query is not '':
            query = porter.stem(query, 0, len(query) - 1)
            if (query in stop_words) or (hasNumbers(query)) or (query not in dictionary):
                print query, "word is not in any document."
                continue
            else:
                results = []
                for x in dictionary[query]:
                    results.append(x['name'])
                all_results.append(results)

    intersect_docs = intersection(all_results)

    for doc in intersect_docs:
        positions = []
        q_no = 0
        for query in words_in_query:
            if query is not '':
                query = porter.stem(query, 0, len(query) - 1)
                if (query in stop_words) or (hasNumbers(query)) or (query not in dictionary):
                    print query, "word is not in any document."
                    continue
                else:
                    q_no += 1
                    for x in dictionary[query]:
                        if x['name'] == doc:
                            temp = [(p - q_no) for p in x['positions']]
                            positions.append(temp)
                            break
        intersect_positions = intersection(positions)
        if len(intersect_positions) > 0:
            print "Match found in document", doc
        else:
            print doc, "is not a match!"


def load_index_in_memory():
    with open(sys.argv[1]) as data_file:
        dictionary = dict(json.load(data_file))
    return dictionary


def run_query(query):
    words_in_query = clean_split(query)
    if '"' in query:
        PhraseQ(words_in_query)
    elif len(words_in_query) == 1:
        OneWordQ(query)
    else:
        MultiWordQ(words_in_query)


def take_commands():
    print "Please enter your query at the prompt!\n"
    while 1:
        sys.stdout.write("> ")
        query = raw_input().strip()
        run_query(query)


if len(sys.argv) < 4:
    print "USAGE: python search_engine.py <inverted_index> <stop_words> <path_to_docs>\n"
    print "PLEASE USE INVERTED INDEX IF YOU ALREADY HAVE IT."
    print "PLEASE USE STOP WORDS IF YOU ALREADY HAVE IT."
    print "PLEASE USE PATH TO DOCUMENTATION IF YOU ALREADY HAVE IT."

    exit(1)

path_to_documents = sys.argv[3]

dictionary = {
    'code': [{
        'name': 'abc.txt',  # primary_key
        'frequency': 1,
        'tf_idf_weight': 0,
        'positions': [1]
    }]  # postings_list
}

stop_words = []
delimiters = ['\n', ' ', ',', '.', '?', '!', ':', '#', '$', '[', ']',
              '(', ')', '-', '=', '@', '%', '&', '*', '_', '>', '<',
              '{', '}', '|', '/', '\\', '\'', '"', '\t', '+', '~', ':',
              '^']

porter = PorterStemmer()

os.system("clear")

print ".........................................................."
print "\t\tWelcome to Go!"
print "..........................................................\n"

print "Do you want to update/build inverted index?[y/n]"
if raw_input() == 'y':
    # process
    # loadDocuments()
    print "Loading Stop Words..."
    load_stop_words()
    print "Building inverted index..."
    build_index()
    print "normalizing!"
    normalize()
    print "Writing the inverted index to", sys.argv[1]
    write_inverted_index_to_file()
    print "Data munching complete! Use Go now!"

    print "Complete!\n"

    take_commands()
else:
    print "Congrats! You just saved 15s in your life.\n"
    print "Loading inverted index in memory..."
    dictionary = load_index_in_memory()
    print "Loaded inverted index in memory!"

    take_commands()
