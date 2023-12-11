import re
# import Classes.Query as Query
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from whoosh.matching.mcore import Matcher
import whoosh.index as index
from whoosh.index import FileIndex
from whoosh.reading import IndexReader
from whoosh.searching import Searcher
from whoosh.query import *
from whoosh.qparser import QueryParser
from whoosh.analysis import RegexTokenizer
from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
import whoosh.index as index
from whoosh import scoring
import datetime
import searchmethod1

# Path
# uncompleted address of preprocessed corpus.
ResultHM1="data2//preprocessed_leetcode."
# address of generated Web index file.
IndexWebDir="data2//leetcode_indexing//"
# query path
QueryDir="data2//query.txt"
leetcode_file_path = r'./data2/leetcode.txt'
leetcode_solutions_file_path = "data/input/leetcode_solutions.txt"

# Query
class Query:
    def __init__(self):
        return

    queryContent = ""
    topicId = ""

    def getQueryContent(self):
        return self.queryContent

    def getTopicId(self):
        return self.topicId

    def setQueryContent(self, content):
        self.queryContent=content

    def setTopicId(self, id):
        self.topicId=id

# document
class Document:

    def __init__(self):
        return

    docid = ""
    docno = ""
    score = 0.0

    def getDocId(self):
        return self.docid

    def getDocNo(self):
        return self.docno

    def getScore(self):
        return self.score

    def setDocId(self, docid):
        self.docid = docid

    def setDocNo(self, no):
        self.docno = no

    def setScore(self, the_score):
        self.score = the_score

# MyIndexReader
class MyIndexReader:

    searcher = []

    def __init__(self, type):
        path_dir = IndexWebDir

        self.index = index.open_dir(path_dir)
        self.searcher = self.index.searcher()
        self.reader = self.index.reader()
        self.all_terms = list(self.reader.field_terms('doc_content'))

    # Return the integer DocumentID of input string DocumentNo.
    def getDocId(self, docNo):
        return self.searcher.document_number(doc_no=docNo)

    # Return the string DocumentNo of the input integer DocumentID.
    def getDocNo(self, docId):
        return self.searcher.stored_fields(docId)["doc_no"]

    # Return DF.
    def DocFreq(self, token):
        results = self.searcher.search(Term("doc_content", token))
        return len(results)
        
    # Return the frequency of the token in whole collection/corpus.
    def CollectionFreq(self, token):
        return self.reader.frequency('doc_content', token)

    # Return posting list in form of {documentID:frequency}.
    def getPostingList(self, token):
        results = self.searcher.search(Term("doc_content", token), limit=None)
        postList = {}
        for result in results:
            words = self.searcher.stored_fields(result.docnum)["doc_content"].split(" ")
            count = 0
            for word in words:
                if word == token:
                    count += 1
            postList[result.docnum] = count
        return postList

    # Return the length of the requested document.
    def getDocLength(self, docId):
        words = self.searcher.stored_fields(docId)["doc_content"].split(" ")
        return len(words)

def tokenization(content):
    content = re.sub(r'[^a-zA-Z\s]', ' ', content)
    tokenized_content = word_tokenize(content)
    return tokenized_content

# ExtractQuery
class ExtractQuery:
    def __init__(self, query):
        # 1. you should extract the 4 queries from the QueryDir
        # 2. the query content of each topic should be 1) tokenized, 2) to lowercase, 3) remove stop words, 4) stemming
        # 3. you can simply pick up title only for query.
        self.queries = []
        # init stemmer
        stemmer = PorterStemmer()
        # read stop words
        stopword_file_path = r'./data2/stopword.txt'
        with open(stopword_file_path, 'r', encoding='utf-8') as stopword_file:
            stop_words = [word.strip() for word in stopword_file.readlines()]

        self.queries = [query]

        # preprocess query
        preprocessed_queries = []
        for query in self.queries:
            # preprocess query
            preprocessed_query = ' '
            # remove html tags
            tag = re.compile(r'<[^>]+>', re.S)
            tag = re.compile(r'</?.*?>', re.S|re.M) 
            query = tag.sub('', query)

            # tokenization
            tokenized_query = tokenization(query)
            for word in tokenized_query:
                # if word not in stop_words: # remove stop words
                    # normalization
                    word.lower()
                    # stemming
                    word = stemmer.stem(word)
                    preprocessed_query += word
                    preprocessed_query += ' '
            preprocessed_queries.append(preprocessed_query[:-1])
        self.queries = preprocessed_queries.copy()
        return

    def getQuries(self):
        queries=[]
        query_idx = 1
        for query in self.queries:
            aQuery=Query()
            aQuery.setTopicId(str(query_idx))
            aQuery.setQueryContent(query)
            queries.append(aQuery)
            query_idx += 1

        return queries

# QueryRetrievalModel
class QueryRetrievalModel:

    indexReader=[]
    query_parser=[]
    searcher=[]

    def __init__(self, ixReader):
        path_dir= IndexWebDir
        self.searcher = index.open_dir(path_dir).searcher(weighting=scoring.BM25F(B=0.75, content_B=1.0, K1=1.5))
        self.query_parser=QueryParser("doc_content", self.searcher.schema)
        return

    # query:  The query to be searched for.
    # topN: The maximum number of returned documents.
    # The returned results (retrieved documents) should be ranked by the score (from the most relevant to the least).
    # You will find our IndexingLucene.Myindexreader provides method: docLength().
    # Returned documents should be a list of Document.
    def retrieveQuery(self, query, topN):
        query_input=self.query_parser.parse(query.getQueryContent())
        search_results = self.searcher.search(query_input, limit=topN)
        return_docs=[]
        for result in search_results:
            # print(self.searcher.stored_fields(result.docnum))
            a_doc=Document()
            a_doc.setDocId(result.docnum)
            a_doc.setDocNo(self.searcher.stored_fields(result.docnum)["doc_no"])
            a_doc.setScore(result.score)
            return_docs.append(a_doc)
        return return_docs
    
def read_document():
    file = open(leetcode_file_path, 'r', encoding="utf-8")
    file_contents = file.read()
    titles = re.findall(r'<div id="title">(.*?)</div>', file_contents)
    contents = re.findall(r'<div id="title">(.*?)Example', file_contents, re.DOTALL) 
    questions = re.findall(r'<div id="title">(.*?)<br>', file_contents, re.DOTALL)
    return contents, questions, titles


def get_results(query, language, topk):
    contents, questions, titles_use = read_document()
    titles_solution, codes = searchmethod1.read_solutions()

    idx = MyIndexReader("txt")
    search = QueryRetrievalModel(idx)
    extractor = ExtractQuery(query)
    queries= extractor.getQuries()
    query = queries[0]
    results = search.retrieveQuery(query, topk)
    if(len(results)==0):
        return "", 0
    
    final_result = ''
    for i in range(len(results)):
        result = questions[int(results[i].getDocNo())]
        title = str(titles_use[int(results[i].getDocNo())])
        title = title.split('.')[-1][1:]
        try:
            title_id = titles_solution.index(title)
            code_by_language = searchmethod1.split_code_by_language(codes[title_id])

            all = ""
            for lang in code_by_language:
                code_by_language[lang] = '???'.join(code_by_language[lang])
                code_by_language[lang] = code_by_language[lang].replace('<', '&lt')
                code_by_language[lang] = code_by_language[lang].replace('>', '&gt')
                code_by_language[lang] = code_by_language[lang].split('???')
                code_by_language[lang] = '<br>'.join(code_by_language[lang])
                code_by_language[lang] = lang + ' code:<br>' + code_by_language[lang] + '<br><br>'
                all += code_by_language[lang]
            code_by_language['All'] = all
            context = code_by_language[language]
        except:
            context = "There is no code for this question."
        
        text = result.split('<div class="content__u3I1 question-content__JfgR">')[0]
        star_count = text.count('*')
        button = f'<br><button id="toggleButton{i+1}">Show Answer</button><div id="documentContainer{i+1}"><!-- Your document content goes here --><p>{context}</p></div><br>' #code_by_language[language]
        result = star_count * '*' + '<div id="title">' + result + button + '<hr><br>'
        final_result += result

    return final_result, len(results)

if __name__ == '__main__':
    query = 'do you know my name'
    language = 'All'
    topk = 5
    print(get_results(query, language, topk))