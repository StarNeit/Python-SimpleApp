"""\
--------------------------------------------------------------------------------
    USE: python <PROGNAME> (options)
    ACTION: Performs as a Document Retrieval System.
    OPTIONS:
        -h : print this help message
        -d <filename> : name of the source document collection file.(default value is documents.txt)
        -q <filename> : name of the source query file.(default value is queries.txt)
        -s <filename> : name of the stopwords list file.(default value is stop_list.txt)
        -t : flag option to determine whether stemming is applied or not.
        -w <weight_type> : specify the weight_type - binary, frequency, tf.idf. (default value is td.idf)
        -i <filename> : name of the index file.
        -r <filename> : name of the result output file.
        -S <query_id> : indicates single query.
        -C <query_string>  : indicates custom query.
--------------------------------------------------------------------------------
"""

import getopt, sys, re, math, string
from read_documents import ReadDocuments
from read_documents import ReadIndexFile
from nltk.stem import PorterStemmer

#########################################################################################################################################################################################

##########      Variables that are set from Command Line options.       ##########

doc_file_name       =       'documents.txt'         #       Name of document collection file.
qry_file_name       =       'queries.txt'           #       Name of query file.
stop_list_name      =       'stop_list.txt'         #       Name of stopword list file.
index_file_name     =       'index.txt'             #       Name of index file.
result_file_name    =       'result.txt'            #       Name of result output file.

##########      Variables that are used to store global, document, query tokens.        ##########

stop_words          =       {}                      #       Dictionary variable to store the stopwords.                                                                                     (Each element of this list is a stop word)
doc_tkn_idx         =       []                      #       (Abbreviation of document_token_index)Index list to store the number of terms that are contained in the relevant document.      (Each element of this list is a term of documents.)
qry_tkn_idx         =       []                      #       (Abbreviation of query_token_index)Index list to store the number of terms that are contained in the relevant query.            (Each element of this list is a term of queries.)
colct_tkn_idx       =       {}                      #       (Abbreviation of collection_token_index)Index dictionary to store the number of documents that contains the relevant term.      (Each element of this dictionary is a term of documents.)


stemming            =       False                   #       Variable to determine whether stemming is applied or not.
index_reuse         =       True                    #       Variable to determine whether index file is reused or not.
stop_list_use       =       False                   #       Variable to determine whether the stopword list is reused or not.
sorted_doc_ids      =       []                      #       Variable to store the ranked document ids.
document_count      =       0                       #       Variable to store the document count contained in the collection.
weighting_type      =       'tf.idf'                #       Variable to identify the weighting_type     (tf.idf or frequency or binary)

##########      Variables that are used to handle single query and custom query        ##########

FILE_QUERY          =       1                       #       Means that we get query set from a file.
SINGLE_QUERY        =       2                       #       Means that we get a single query from a file.
CUSTOM_QUERY        =       3                       #       Means that we get query from command line.
query_type          =       FILE_QUERY              #       query_type is set to FILE_QUERY. So default way to get query is to get from a file.
query_index         =       0                       #       Variable to store the index of single query.
query_string        =       ''                      #       Variable to store the user defined custom query.
show_count          =       10                      #       Variable to store the count of result to be shown in console.


#########################################################################################################################################################################################

##########      Function that is used to read stop word list.        ##########

### Input   :   path: filename(including or not path) of the stopword list
def ReadStopWords(path):

    global stop_words

    with open(path) as input_fs:

        for word in input_fs:

            word = word.split('\n')[0];
            stop_words[word] = 1

##########      Function that is used to write index file.        ##########

### Input   :   path: filename(including or not path) of the index file
def WriteIndexFile(path):

    f = open(path, 'w')

    ### Write the document count contained in the collection. It is surrounded by <documentcount>...</documentcount> tag.

    f.write('<documentcount>\n')
    f.write(str(document_count))
    f.write('\n</documentcount>\n')

    ### Write the collection index. It is surrounded by <collection>...</collection> tag.

    f.write('<collection>\n')

    for token in colct_tkn_idx:

        f.write(token)
        f.write(' ')
        f.write(str(colct_tkn_idx[token]))
        f.write('\n')

    f.write('</collection>\n')

    ### Write the document index. It is surrounded by <document>...</document> tag.

    for token_list in doc_tkn_idx:

        f.write('<document>\n')

        for token in token_list:

            f.write(token)
            f.write(' ')
            f.write(str(token_list[token]))
            f.write('\n')

        f.write('</document>\n')

    ### Write the query index. It is surrounded by <query>...</query> tag.

    for token_list in qry_tkn_idx:

        f.write('<query>\n')

        for token in token_list:

            f.write(token)
            f.write(' ')
            f.write(str(token_list[token]))
            f.write('\n')

        f.write('</query>\n')

    f.close()

##########      Function that is used to write result file.        ##########

### Input   :   path: filename(including or not path) of the result outputfile list
def WriteResultFile(path):

    f = open(path, 'w')

    query_index = 0

    for query in qry_tkn_idx:

        for ranking in range(0, 10):

            f.write(str(query_index + 1))
            f.write(' ')
            f.write(str(sorted_doc_ids[query_index][ranking][1]))
            f.write('\n')

        query_index += 1

    f.close()


##########      Function that is used to analyse command line options.        ##########

### Explanation about each command line option is at the beginning of this file.
def AnalyseCommandLine():

    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:q:s:tw:i:r:h:S:C:N:")

    except getopt.GetoptError as err:
        sys.exit(2)

    for opt, arg in opts:

        global doc_file_name, qry_file_name, stop_list_name, stop_list_use, index_reuse, result_file_name, stemming, weighting_type, query_type, query_index, query_string, show_count

        if opt in ("-d"):               ### Document file option
            doc_file_name = arg

        elif opt in ("-a"):
            print(arg)

        elif opt in ("-q"):             ### Query file option
            qry_file_name = arg

        elif opt in ("-s"):             ### Stopword list file option

            stop_list_use = True
            stop_list_name = arg

        elif opt in ("-t"):             ### Stemming option
            stemming = True

        elif opt in ("-w"):             ### WeightType option

            weighting_type = arg

            if weighting_type != 'binary' and weighting_type != 'frequency' and weighting_type != 'tf.idf':

                print ("\nNo such weighting type : Only \"binary\", \"frequency\", \"tf.idf\" are required.")
                exit(1)

        elif opt in ("-i"):             ### Index file reuse option

            index_reuse = False
            index_file_name = arg

        elif opt in ("-h"):             ### Showing help option
            printHelp()

        elif opt in ("-r"):             ### Result output file option
            result_file_name = arg

        elif opt in ("-S"):                     ### Query type setting option (this option indicates both single query and custom query)

            query_type = SINGLE_QUERY
            query_index = (int)(arg)

        elif opt in ("-C"):

            query_type = CUSTOM_QUERY
            query_string = arg

        elif opt in ("-N"):

            show_count = (int)(arg)

        else:
            assert False, "unhandled option"

##########      Function that is used to show help on console.        ##########

def printHelp():
        help = __doc__.replace('<PROGNAME>',sys.argv[0],1)
        print (help)
        exit()

##########      Function that is used to tokenize document and query.       ##########

def Tokenize():

    global          doc_file_name, qry_file_name, stemming
    global          colct_tkn_idx, doc_tkn_idx, qry_tkn_idx

    stemmer         =   PorterStemmer()
    documents       =   ReadDocuments(doc_file_name)

    ###     Tokenize all documents in collection.

    for doc in documents:

        global document_count

        token_list = {}
        document_count += 1

        for line in doc.lines:

            tokens = re.split('\-|\,|\&|\ |\"|\(|\)|\:|\;|\=|\/|\?\|\~|\`|\!|\@|\#|\$|\^|\*|\[|\]|\{|\}|\'|\<|\>|\/|\\n|\.', line)      ###     Each line is splitted by special characters.(Simple method)

            for token in tokens:

                if (token != None) and (token != ''):

                    token = token.lower()                   ###     All character in tokens are lowercased.

                    if stemming == True:                    ###     if stemming == True(that is -s option is set in command line) then stemming is performed.
                        token = stemmer.stem(token)

                    if token not in stop_words:

                        if token not in token_list:         ###     If the term is not registed before then it is registed.

                            token_list[token] = 1

                            if token not in colct_tkn_idx:      ###     Count of documents that contains each term is calculated.
                                colct_tkn_idx[token] = 1

                            elif token in colct_tkn_idx:
                                colct_tkn_idx[token] = colct_tkn_idx[token] + 1

                        elif token in token_list:           ###     If the term is registed before then the count is increased.
                            token_list[token] = token_list[token] + 1

        doc_tkn_idx.append(token_list)

    ###     Tokenize all queries in query set.

    if query_type != CUSTOM_QUERY:                          ###     Means that we get query not from command line.

        documents = ReadDocuments(qry_file_name)

        for doc in documents:

            if query_type == SINGLE_QUERY and doc.docid != query_index:     ###     This if statement is called only when query_type is SINGLE_QUERY
                continue                                                    ###             The purpose of this statement is to ignore other queries in case of SINGLE_QUERY

            token_list = {}

            query = ''

            for line in doc.lines:
                query = query + line

            tokens = re.split('\-|\,|\&|\ |\"|\(|\)|\:|\;|\=|\/|\?\|\~|\`|\!|\@|\#|\$|\^|\*|\[|\]|\{|\}|\'|\<|\>|\/|\\n|\.', query)      ###     Each line is splitted by special characters.(Simple method)
            token_list = GetTokenList(tokens)
            qry_tkn_idx.append(token_list)

    elif query_type == CUSTOM_QUERY:

        token_list  = {}
        tokens      = re.split('\-|\,|\&|\ |\"|\(|\)|\:|\;|\=|\/|\?\|\~|\`|\!|\@|\#|\$|\^|\*|\[|\]|\{|\}|\'|\<|\>|\/|\\n|\.', query_string)      ###     User defined custom query is splitted by special characters.(Simple method)
        token_list  = GetTokenList(tokens)

        qry_tkn_idx.append(token_list)

##########      Function that is used to get token information from string       ##########

def GetTokenList(tokens):

    stemmer         =       PorterStemmer()
    token_list      =       {}

    for token in tokens:

        if (token != None) and (token != ''):

            token = token.lower();                      ###     All character in tokens are lowercased.

            if stemming == True:                        ###     if stemming == True(that is -s option is set in command line) then stemming is performed.
                token = stemmer.stem(token)

            if token not in stop_words:

                if token not in token_list:             ###     If the term is not registed before then it is registed.
                    token_list[token] = 1

                elif token in token_list:               ###     If the term is registed before then the count is increased.
                    token_list[token] = token_list[token] + 1

    return token_list


##########      Function that is used to rank documents.       ##########

def DocumentRanking():

    global doc_tkn_idx, qry_tkn_idx, colct_tkn_idx

    doc_magnitudes      =       []
    qry_magnitudes      =       []

    ###     For each document in the collection, the magnitude of each document vector is calculated according to vector space model.

    for token_list in doc_tkn_idx:

        doc_magnitude = 0

        for token in token_list:

            if weighting_type       ==      'binary':                  ###     Weighting_type == 'binary' means that all document and query vectors are represented as binary vector.
                doc_magnitude += 1

            elif weighting_type     ==      'frequency':             ###     Weighting_type == 'frequency' means that all document and query vectors are calculated according to the frequency of a term.
                doc_magnitude += token_list[token]

            elif weighting_type     ==      'tf.idf':                ###     Weighting_type == 'tf.idf' means that all document and query vectors are represented according to tf.idf method.
                doc_magnitude += math.pow(math.log(1 + token_list[token]) * math.log(1 + document_count / colct_tkn_idx[token]), 2)

        doc_magnitudes.append(math.sqrt(doc_magnitude))

    ###     For each query in the queryset, the magnitude of each query vector is calculated according to vector space model.

    for token_list in qry_tkn_idx:
        qry_magnitude = 0

        for token in token_list:
            if (token in colct_tkn_idx):

                if weighting_type == 'binary' or weighting_type == 'frequency':     ###     'binary' and 'frequency' are the same for query vector.
                    qry_magnitude += 1

                elif weighting_type == 'tf.idf':                                    ###     query vector is calculated according to tf.idf method.
                    qry_magnitude += math.pow(math.log(1 + document_count / colct_tkn_idx[token]), 2)

        qry_magnitudes.append(math.sqrt(qry_magnitude))

    ###     For each query and for each document cosine similarity is calculated.

    qry_index = 0

    for qry_token_list in qry_tkn_idx:

        doc_index       =       0
        match_scores    =       []

        for doc_token_list in doc_tkn_idx:

            match_score = 0

            for token in qry_token_list:

                if token in doc_token_list:
                    match_score += math.log(1 + doc_token_list[token]) * math.pow(math.log(1 + document_count / colct_tkn_idx[token]), 2)   ###     Cosine similarity calculation.

            match_score /= doc_magnitudes[doc_index] * qry_magnitudes[qry_index]        ###     similarity is length-normalized
            match_scores.append([match_score, doc_index + 1])
            doc_index += 1

        match_scores.sort()
        match_scores.reverse()
        sorted_doc_ids.append(match_scores)
        qry_index += 1


##########      Main Function       ##########

def main():

    global colct_tkn_idx, doc_tkn_idx,  qry_tkn_idx, document_count, query_type

    AnalyseCommandLine()                                        ###     First, analyze command line.

    if stop_list_use == True:                                   ###     stop_list_use == True means that stop_list is used and -s option is set in command line.
        ReadStopWords(stop_list_name)                           ###     if -s option is set in command line read stopwords from stopword list file.

    if index_reuse == True:                                     ###     index_reuse == True means that index is reused and -i option is set in command line.

        index           = ReadIndexFile(index_file_name)                  ###     if -i option is set in command line
        colct_tkn_idx   = index.ReadCollectionIndex()             ###             Read collection index.
        doc_tkn_idx     = index.ReadDocumentIndex()                 ###             Read document index.
        qry_tkn_idx     = index.ReadQueryIndex()                    ###             Read Query index.
        document_count  = (int)(index.ReadDocumentCount())       ###             Read document count that is contained in collection file.

    else:
        Tokenize()                                              ###     if -i option is unset in command line then tokenizing is performed to configure index data structure.
        WriteIndexFile(index_file_name)                         ###             and index is written in the file on disk.

    DocumentRanking()                                           ###     Ranking is performed.
    WriteResultFile(result_file_name)                           ###     Finally the list of document ids relevant to each query is written in a file to perform performance evaluation.

    if query_type != FILE_QUERY:

        query_index = 0

        for query in qry_tkn_idx:

            for ranking in range(0, show_count):

                print (query_index + 1, ':', sorted_doc_ids[query_index][ranking][1])

            query_index += 1


if __name__ == "__main__":
    main()
