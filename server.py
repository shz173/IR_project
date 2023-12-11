from flask import Flask, request, render_template, jsonify
import os
import re
import nltk
import requests
import math
import searchmethod1
import searchmethod2


nltk.download('punkt')
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
# app = Flask(__name__)

# Support for gomix's 'front-end' and 'back-end' UI.
app = Flask(__name__, static_folder='public', template_folder='views')

# Set the app secret key from the secret environment variables.
app.secret = os.environ.get('SECRET')


@app.route('/')
def homepage():
    """Displays the homepage."""
    return render_template('index.html')

  
@app.route('/process', methods=['POST'])
def process_form():
    input_text = request.form['input_text']
    output_text = input_text
    return render_template('index.html', output_text=output_text)


@app.route("/test", methods=['POST'])
def test():   
    # input
    query = request.form['input_text']
    language = request.form['languages']
    topk = int(request.form['topk'])
    # method = request.form['methods']

    
    # output
    final_result = ''

    head = '<head> \
        <meta charset="UTF-8"> \
        <meta name="viewport" content="width=device-width, initial-scale=1.0"> \
        <title>Toggle Documents</title> \
        <style> \
        #documentContainer { \
            display: none; /* Initially hide the document container */ \
        } \
        </style> \
    </head> \n'
    
    final_result += head

    num = 0
    result, num1 = searchmethod2.get_results(query, language, topk)
    final_result+=result
    num += num1
    if(num1 < topk):
        result, num2 = searchmethod1.get_results(query, language, topk, num1)
        num += num2
        final_result+=result
  
    final_result += '<a href="/">return to main page</a>'
    
    script = "<script>"
    for i in range(num):
        command = f"document.addEventListener('DOMContentLoaded', function(){{ \
                        var button = document.getElementById('toggleButton{i+1}'); \
                        var documentContainer = document.getElementById('documentContainer{i+1}'); \
                        documentContainer.style.display = 'none'; \
                        button.addEventListener('click', function() {{ \
                            if (documentContainer.style.display === 'none'){{ \
                                documentContainer.style.display = 'block'; \
                            }} \
                            else {{ \
                                documentContainer.style.display = 'none'; \
                            }} \
                        }}); \
                    }}); "
        script += command
    script += "</script>"

    final_result += script
  
  
    return final_result
  
  
if __name__ == '__main__':
    app.run(debug=True)
