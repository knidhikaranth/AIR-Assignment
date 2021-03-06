#Import statements
import os
import pandas
import nltk
import numpy
import csv
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import sigmoid_kernel
from sklearn.metrics.pairwise import linear_kernel

#Pandas options
pandas.set_option('display.max_rows', None)
pandas.set_option('display.max_columns', None)
pandas.set_option('display.width', None)
pandas.set_option('display.max_colwidth', -1)


#Symbols
symbols = "!\"#$%&()*+-./:;<=>?@[\\]^_`{|}~\n"

#Stemmer
stemmer = nltk.stem.PorterStemmer()

#Path
path = os.getcwd()+'/AIR-Dataset'

# To read from files
def load_data(path):
    path += '/'
    with open('index.p', 'rb') as fin:
        index = pickle.load(fin)
    with open('documents.p', 'rb') as fin:
        documents = pickle.load(fin)
    with open('docindex.p', 'rb') as fin:
        docindex = pickle.load(fin)
    with open('bigrams.p', 'rb') as fin:
        bigrams = pickle.load(fin)
    return index,documents,docindex,bigrams


#Function to create bigrams
def wildcard(word, bigrams, st):
    word = "$"+word+"$"
    for i in range(len(word)-1):
        bi = word[i:i+2]
        if bi not in bigrams.keys():
            bigrams[bi] = set()
            bigrams[bi].add(st)
        elif st not in bigrams[bi]:
            bigrams[bi].add(st)
            
            
#Function used to process snippets prior to indexing
def process(row, bigrams):
    data = numpy.char.lower(row)
    for i in range(len(symbols)):
        data = numpy.char.replace(data, symbols[i], '')
    data = numpy.char.replace(data, ',', '')
    data = numpy.char.replace(data, "'", "")
    words = nltk.tokenize.word_tokenize(str(data))
    new_data = ""
    for w in words:
        st = stemmer.stem(w)
        wildcard(w, bigrams, st)
        new_data = new_data + " " + st
    data = numpy.char.strip(new_data)
    return data
  


####### HANDLING DIFFERENT TYPES OF QUERIES #############

#####SINGLE WORD QUERIES
def singleWordQuery(query):
    cleaned = str(processQueryRanking(query))
    ans = index.get(cleaned)
    return ans



####PHRASE QUERIES

def getDocs(term):
    if term in index.keys():
        #print(term, index[term])
        return index[term]
    else:
        return []

def getCommon(dind1, dind2):
    ans = []
    for i in dind1:
        if i in dind2:
            ans.append(i)
    return ans

def getCommonRows(rows1, rows2, k):
    rows = []
    for i in rows1.keys():
        if i in rows2.keys():
            pos1 = rows1[i]
            pos2 = rows2[i]
            j1 = 0
            j2 = 0
            while j1<len(pos1) and j2<len(pos2):
                if pos2[j2] - pos1[j1] == k:
                    rows.append(i)
                    j1 = j1+1
                    j2 = j2+1
                elif pos1[j1]<pos2[j2]:
                    j1 = j1+1
                else:
                    j2 = j2+1
    return rows

def getCommonData(docs, term1, term2, k):
    ans = {}
    for i in docs:
        docin = docindex[i]
        rows1 = docin[term1]
        rows2 = docin[term2]
        #print(i)
        #print(term1,rows1)
        #print(term2,rows2)
        if len(rows1.keys())<len(rows2.keys()):
            rows = getCommonRows(rows1, rows2, k)
        else:
            rows = getCommonRows(rows2, rows1, -k)
        if len(rows):
            ans[i] = rows
    return ans

def createDict(results, data):
    for i in data.keys():
        for j in data[i]:
            temp = str(i)+"$"+str(j)
            if temp in results:
                results[temp] += 1
            else:
                results[temp] = 1
                
                
                
def pqprocess(row):
    data = numpy.char.lower(row)
    for i in range(len(symbols)):
        data = numpy.char.replace(data, symbols[i], '')
    data = numpy.char.replace(data, ',', '')
    data = numpy.char.replace(data, "'", "")
    words = nltk.tokenize.word_tokenize(str(data))
    new_data = ""
    for w in words:
        st = stemmer.stem(w)
        new_data = new_data + " " + st
    data = numpy.char.strip(new_data)
    return data

def phraseQuery(pquery):
    pcleaned = str(pqprocess(pquery)).split()
    results = dict()
    for i in range(len(pcleaned)):
        j = i+1
        dind1 = getDocs(pcleaned[i])
        if len(dind1)==0:
            continue
        while j<len(pcleaned):
            dind2 = getDocs(pcleaned[j]) 
            if len(dind2)==0:
                j = j+1
                continue
            if len(dind1)<=len(dind2):
                docs = getCommon(dind1, dind2)

                data = getCommonData(docs, pcleaned[i], pcleaned[j], j-i)

            else:
                docs = getCommon(dind2, dind1)
                data = getCommonData(docs, pcleaned[j], pcleaned[i], i-j)
            #print(data)
            createDict(results, data)
            j = j+1

    occs = dict()
    #print(results)
    for i in results.keys():
        #print(i, occs)
        if results[i] in occs:
            occs[results[i]].append(i)
        else:
            occs[results[i]] = [i]
    #print(occs)
    final = dict()
    for i in occs:
        for j in occs[i]:
            d, r = j.split('$')
            d = int(d)
            r = int(r)
            if d in final:
                final[d].add(r)
            else:
                final[d] = set()
                final[d].add(r)
    
    if len(occs)==0:
        for i in pcleaned:
            res = singleWordQuery(i)
            if res is None:
                continue
            for j in res.keys():
                if j in final:
                    final[j].update(res[j])
                else:
                    final[j] = set()
                    final[j].update(res[j])
    
    return final




######WILCARD QUERIES

def wildcardQuery(words):
    ws = set()
    for w in words:
        for i in range(len(w)-1):
            bi = w[i:i+2]
            if bi not in bigrams.keys():
                return None
            elif len(ws)==0:
                ws = bigrams[bi]
                continue
            else:
                ws = set.intersection(set(bigrams[bi]), ws)
    result = set()
    for i in words:
        e, s = i.split('$')
        for i in ws:
            if i.startswith(s) and i.endswith(e):
                result.add(i)
    final = dict()
    
    for i in result:
        res = singleWordQuery(i)
        if res is None:
            continue
        for j in res.keys():
            if j in final:
                final[j].update(res[j])
            else:
                final[j] = set()
                final[j].update(res[j])
    return final


######## RANKING #########

#Processing queries prior to ranking
def processQueryRanking(row):
    data = numpy.char.lower(row)
    for i in range(len(symbols)):
        data = numpy.char.replace(data, symbols[i], '')
    data = numpy.char.replace(data, ',', '')
    data = numpy.char.replace(data, "'", "")
    words = nltk.tokenize.word_tokenize(str(data))
    new_data = ""
    for w in words:
          new_data = new_data + " " + stemmer.stem(w)
    data = numpy.char.strip(new_data)
    return data

#Checks query length and calls the functions accordingly
def handleQuery(query):
    if '*' in query:
        parts = query.split('*')
        if '' in parts:
            if parts[0] == '':
                parts = [parts[1]+"$"]
            elif parts[1] == '':
                parts = ["$"+parts[0]]
        else:
            parts[0] = "$"+parts[0]
            parts[1] = parts[1]+"$"
        return wildcardQuery(parts)      
    elif len(query.split())==1: #single word
        return singleWordQuery(query)
    else:
        return phraseQuery(query)
    
    
#Creates DF using candidate docs(row)
def corpusdf(ans):
    ensuing_df_data=[]

    for file in ans:
        with open(path+"/"+documents[file]) as csv_file:
            csv_reader = csv.reader(csv_file)
            rows = list(csv_reader)
    
            for each_row in ans[file]:
                mod_row = rows[each_row+1] + [file, each_row+1]
                ensuing_df_data.append(mod_row)       
    ensuing_df = pandas.DataFrame(ensuing_df_data, columns = ['URL', 'MatchDateTime', 'Station', 'Show', 'IAShowID', 'IAPreviewThumb', 'Snippet', 'DocID', 'RowID'])

    return ensuing_df

#Creates df of the query and concatenates this with corpus_df
def querydf(corpus_df, query):
    data_query = [['filler', 'values', 'for', 'the', 'query','data',query, 0, 0]] 
    querydf = pandas.DataFrame(data_query, columns = ['URL', 'MatchDateTime', 'Station', 'Show', 'IAShowID', 'IAPreviewThumb', 'Snippet', 'DocID', 'RowID']) 
    to_concatenate = [corpus_df, querydf]
    final_df = pandas.concat(to_concatenate)
    return final_df


#Creates tf-idf vector space using concatenated df
def vectorSpaceModel(final_df):   
    tfidfv = TfidfVectorizer(min_df = 1, max_features=None, strip_accents='unicode', analyzer='word', token_pattern=r'\w{1,}', ngram_range={1,3}, use_idf=1, smooth_idf=1, sublinear_tf=1, stop_words='english')
    query_tfv_mat=tfidfv.fit_transform(final_df['Snippet'])
    return query_tfv_mat

#Finds similarity scores (cosine), sorts the docs based on sim scores and returns top 22 results
def rankingFunc(query_tfv_mat, final_df, k):
    sim_scores = linear_kernel(query_tfv_mat, query_tfv_mat[len(final_df)-1]).flatten()
    relevant_docs_indices = sim_scores.argsort()[:-k-2:-1]
    return (relevant_docs_indices, len(sim_scores)-1)

#Displays the results in a given format
def displayRanked(final_df, ranked_docs):
    rank = 1
    rank_list = numpy.delete(ranked_docs,0)
    for i in rank_list:
        print('Rank: ',rank)
        print(final_df.iloc[i])
        print()
        print('\n\n')
        rank+=1
    print(rank-1,' results found.')

def getRanked(final_df, ranked_docs):
    results = []
    rank_list = numpy.delete(ranked_docs,0)
    for i in rank_list:
        temp = final_df.iloc[i].to_dict()
        results.append(temp)
    return results
    
index, documents, docindex, bigrams = load_data('.')

def run_query(query, num_queries):
    #query = "major report released"
    ans = handleQuery(query)
    if ans is None:
        return []
    corpus_df = corpusdf(ans)
    final_df = querydf(corpus_df, query)
    query_tfv_mat = vectorSpaceModel(final_df)
    ranked_docs, num_relevant = rankingFunc(query_tfv_mat, final_df, num_queries)
    results = getRanked(final_df, ranked_docs)
    #displayRanked(final_df,ranked_docs)
    return results, num_relevant
    