from flask import Flask, request, render_template, jsonify
import os
import re
import nltk
import requests
import math

nltk.download('punkt')
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize


  
SELECT_DOCUMENT_NUMBER = 3

# path
stopword_file_path = r'./data/input/stopword.txt'
leetcode_file_path = r'./data/input/leetcode.txt'
leetcode_solutions_file_path = r'./data/input/leetcode_solutions.txt'
output_path = r'./data/output'


def read_solutions():
    file = open(leetcode_solutions_file_path, 'r', encoding="utf-8")
    file_contents = file.read()
    titles = re.findall(r'<name (.*?) name>', file_contents, re.DOTALL) 
    codes = re.findall(r'<doc(.*?)doc>', file_contents, re.DOTALL) 
    return titles, codes

def split_code_by_language(code_text):
    languages = {
        'C++': ['include', 'nullptr', '::', '->','struct','vector'],
        'Java': ['java', 'public class','public'],
        'Python': ['def ', 'class '],
        'JavaScript': ['function ', 'this.']
    }
    lines = code_text.split('\n')
    code_by_language = {lang: [] for lang in languages}
    current_language = 'C++'
    for line in lines:
        for lang, keywords in languages.items():
            if any(keyword in line for keyword in keywords):
                current_language = lang
                break
        if current_language:
            code_by_language[current_language].append(line)
    return code_by_language

def read_stop_word():
    with open(stopword_file_path, 'r') as f:
        stop_words = [word.strip() for word in f.readlines()]
    return stop_words

def read_document():
    file = open(leetcode_file_path, 'r', encoding="utf-8")
    file_contents = file.read()
    titles = re.findall(r'<div id="title">(.*?)</div>', file_contents)
    contents = re.findall(r'<div id="title">(.*?)Example', file_contents, re.DOTALL) 
    questions = re.findall(r'<div id="title">(.*?)<br>', file_contents, re.DOTALL)
    return contents, questions, titles

def tokenization(content):
    content = re.sub(r'[^a-zA-Z\s]', ' ', content)
    tokenized_content = word_tokenize(content)
    return tokenized_content

def save_indexing_file(dictionary_term, posting):
    # save dictionary_term file
    dictionary_term_file_path = os.path.join(output_path, 'dictionary_term.txt')
    if os.path.exists(dictionary_term_file_path):
        os.remove(dictionary_term_file_path)
    with open(dictionary_term_file_path, 'w', encoding="utf-8") as dictionary_term_file:
        for k in dictionary_term.keys():
            dictionary_term_file.write(str(dictionary_term[k]) + ' ' + str(k)+'\n')

    # save posting file
    posting_file_path = os.path.join(output_path, 'posting.txt')
    with open(posting_file_path, 'w', encoding="utf-8") as posting_file:
        for item in posting:
            posting_file.write(str(item)+'\n')

def save_questions(questions):
    # save questions file
    questions_file_path = os.path.join(output_path, 'questions.txt')
    if os.path.exists(questions_file_path):
        os.remove(questions_file_path)
    with open(questions_file_path, 'w', encoding="utf-8") as questions_file:
        for question in questions:
            questions_file.write(str(question)+'\n')

def create_indexing():
    # read stop words
    stop_words = read_stop_word()

    # read file
    contents, questions = read_document()

    # save questions
    save_questions(questions)

    # init stemmer
    stemmer = PorterStemmer()
    # create indexing file
    dictionary_term = {} # {word:wordID}
    posting = [] # [{docId:occur times, ...}, ...]
    docId = 0
    for content in contents:
        # remove html tags
        tag = re.compile(r'<[^>]+>', re.S)
        tag = re.compile(r'</?.*?>', re.S|re.M) 
        content = tag.sub('', content)

        # tokenization
        tokenized_content = tokenization(content)

        # word preprocess
        for word in tokenized_content:
            if word not in stop_words: # remove stop words
                # normalization
                word.lower()
                # stemming
                word = stemmer.stem(word)
                # indexing
                # if the word hasn't occur in any document, add the word to dictionary_term, add a new dictionary to posting
                if word not in dictionary_term.keys():
                    cur_idx = len(dictionary_term)
                    dictionary_term[word] = cur_idx
                    posting.append({})
                cur_word_idx = dictionary_term[word]
                # record file index in posting[cur_word_idx] with docId as key and count + 1
                if docId not in posting[cur_word_idx].keys():
                    posting[cur_word_idx][docId] = 0
                posting[cur_word_idx][docId] += 1
        # next document
        docId += 1

    # save indexing files
    # save_indexing_file(dictionary_term, posting)
    # return contents, questions
    return dictionary_term, posting

def preprocess_query(query):
    preprocessed_query = []
    # tokenization
    tokenized_query = tokenization(query)
    # init stemmer
    stemmer = PorterStemmer()
    for word in tokenized_query:
        # normalization
        word.lower()
        # stemming
        word = stemmer.stem(word)
        preprocessed_query.append(word)
    return preprocessed_query

def compute_match_score(preprocessed_query, dictionary_term, posting):
    docId_score = {} # {docId:score}
    for word in preprocessed_query:
        if word not in dictionary_term.keys():
            return {}
        posting_idx = dictionary_term[word]
        occur_dic = posting[int(posting_idx)]
        for docId in occur_dic.keys():
            if docId not in docId_score.keys():
                docId_score[docId] = 0
            docId_score[docId] += 1
    return docId_score

def rank_documents(docId_score):
    ranked_documents = sorted(docId_score.items(), key=(lambda x:x[1]), reverse=True)
    return ranked_documents[:min(SELECT_DOCUMENT_NUMBER, len(ranked_documents))]

def read_indexing():
    dictionary_term_file_path = "data/output/dictionary_term.txt"
    posting_file_path = "data/output/posting.txt"
    # open files
    dictionary_term_file = open(dictionary_term_file_path, 'r', encoding="utf-8")
    posting_file = open(posting_file_path, 'r', encoding="utf-8")


    # read dictionary_term_file
    dictionary_term = {}
    while True:
        line = dictionary_term_file.readline().strip()
        if not line: # end reading, break
            break
        tmp = line.split(' ')
        if len(tmp) == 1: # if the word is empty, it will not be split into two elements
            idx, word = tmp[0], ' '
        else:
            idx, word = tmp
        dictionary_term[word] = idx
    # read posting_file
    posting = []
    while True:
        line = posting_file.readline().strip()
        if not line: # end reading, break
            break
        posting.append(eval(line))
    # print("finish reading the index")
    return dictionary_term, posting
  
#   def get_api():
#     # Sending GET request to the API
#     response = requests.get('https://dashing-petal-lynx.glitch.me/')
#     # if response.status_code == 200:
#     data = response.json()
#     return data
    
    
def get_results(query, language, topk, num1):
    # process
    dictionary_term, posting = read_indexing()
    preprocessed_query = preprocess_query(query)
    docId_score = compute_match_score(preprocessed_query, dictionary_term, posting)
    ranked_documents = rank_documents(docId_score)
    contents, questions, titles_use = read_document()
    titles_solution, codes = read_solutions()
    
    # output
    final_result = ''
    topk = topk - num1
    topk = min(topk, len(list(dict(ranked_documents).keys())))
    for i in range(topk):
        result = str(questions[list(dict(ranked_documents).keys())[i]])
        title = str(titles_use[list(dict(ranked_documents).keys())[i]])
        title = title.split('.')[-1][1:]
        try:
            title_id = titles_solution.index(title)
            code_by_language = split_code_by_language(codes[title_id])

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
        button = f'<br><button id="toggleButton{i+1+num1}">Show Answer</button><div id="documentContainer{i+1+num1}"><p>{context}</p></div><br>' 
        result = star_count * '*' + '<div id="title">' + result + button + '<hr><br>'
        final_result += result
    return final_result, topk

  
if __name__ == '__main__':
    query = 'two sum'
    language = 'All'
    topk = 5
    num1 = 2
    print(get_results(query, language, topk, num1))
