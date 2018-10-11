from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.generics import ListCreateAPIView, CreateAPIView, ListAPIView
from rest_framework.validators import ValidationError
#-----------------------------------
# Import Librarys
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.stem.lancaster import LancasterStemmer
import pandas as pd
import pymysql
from chat.models import Questions, Answer
#-----------------------------------
# Create your views here.

#--------------------Training--------------#
stemmer = LancasterStemmer()

stopWords = set(stopwords.words('english'))
other_stop_words = ["?","'s"]
for stop_word in other_stop_words:
    stopWords.add(stop_word)
#---------------------------------------------------
questions = Questions.objects.all().values()
data = pd.DataFrame(list(questions))
answer = pd.DataFrame(list(Answer.objects.all().values()))
#---------------------------------------------------
data_class_count = {}
for class_name in data['class_name']:
    if class_name not in data_class_count:
        data_class_count[class_name] = 1
    else:
        data_class_count[class_name] += 1
#-------------------connection with mysql-----------------------#

def chat_bot_training(request):
#--------------------------------------------------------------
    for class_name in data_class_count.keys():
        data_class_count[class_name] = data_class_count[class_name] / len(data_class_count)
    #----------------------------------------------------------------
    data_class_name = data['class_name'].unique()
    data_class_name_with_word = list(data_class_name)
    data_class_name_with_word.insert(0, 'word')

    # -------------------------------------------#
    result_data_frame = pd.DataFrame(columns=data_class_name_with_word)
    # -------------------------------------------#
    corpus_words = []
    for sentence in data['sentence']:
        for word in nltk.word_tokenize(sentence):
            if word not in stopWords:
                stemmed_word = stemmer.stem(word.lower())

                if stemmed_word not in corpus_words:
                    corpus_words.append(stemmed_word)
                else:
                    pass
    # -------------------------------------------#
    word_list = pd.Series(corpus_words)
    result_data_frame['word'] = word_list.values
    result_data_frame = result_data_frame.fillna(0)
    # -------------------------------------------#
    word_list = list(result_data_frame['word'])
    # -------------------------------------------#
    for i in range(len(data)):
        for word in nltk.word_tokenize(data['sentence'][i]):
            if word not in stopWords:

                stemmed_word = stemmer.stem(word.lower())

                if stemmed_word in word_list:
                    word_position = word_list.index(stemmed_word)
                    # print(word_position)
                    match_class = data['class_name'][i]
                    previous_value = result_data_frame.loc[word_position, match_class]
                    result_data_frame.loc[word_position, match_class] = previous_value + 1

    # -------------------------------------------#
    number_of_unique_word = len(result_data_frame)
    # -------------------------------------------#
    for i in range(number_of_unique_word):
        for class_name_position in range(1, len(data_class_name_with_word)):
            result_data_frame.iloc[i, class_name_position] = ((result_data_frame.iloc[i, class_name_position] + 1) / (
                        number_of_unique_word + result_data_frame[
                    data_class_name_with_word[class_name_position]].sum()))
    # -------------------------------------------#
    result_data_frame.to_csv('training_data.csv', index=False)

    # -----------------------End Of Training Process-------------------------#

    return JsonResponse({'message': 'success', 'status_code': '200'})


# --------------------- Classification---------------------------------#

training_data = pd.read_csv('training_data.csv')

training_data_word_list = training_data['word']
training_data_classes = training_data.drop(['word'], axis=1)
word_list = list(training_data_word_list)

# -------------------------------------------#
# answer = pd.read_csv('answer.csv')
def feedback_answer(class_name):
    class_name_list = list(answer['class_name'])
    index_number_of_class_name = class_name_list.index(class_name)
    return answer.loc[index_number_of_class_name, 'answer']


# -------------------------------------------#
def class_name_of_max_score(result):
    return max(result.keys(), key=(lambda k: result[k]))


# -------------------------------------------#



def classify_sentence(sentence):
    classification_result = {}
    for word in nltk.word_tokenize(sentence):
        if word not in stopWords:
            stemmed_word = stemmer.stem(word.lower())
            if stemmed_word in word_list:
                # print(word_list.index(stemmed_word))

                for class_name in training_data_classes.keys():
                    if class_name not in classification_result:
                        classification_result[class_name] = training_data_classes.loc[
                            word_list.index(stemmed_word), class_name]
                    else:
                        classification_result[class_name] *= training_data_classes.loc[
                            word_list.index(stemmed_word), class_name]

    if len(classification_result) > 0:
        for class_name in training_data_classes.keys():
            classification_result[class_name] = classification_result[class_name] * data_class_count[class_name]
        match_class = class_name_of_max_score(classification_result)
        match_score = classification_result[match_class]
    else:
        match_class = 'no_match'
        match_score = 0
    return (match_class, match_score, feedback_answer(match_class))


# -------------------------------------------#
class chat_bot_chatting(CreateAPIView):

    def post(self, request, *args, **kwargs):

        if 'question' not in request.POST or request.POST['question'] is '':
            raise ValidationError({'message': 'User ID is needed', 'status_code': '400'})

        question = request.POST['question']
        result, a, b = classify_sentence(question)

        return JsonResponse({'message': 'success', 'status_code': '200','class':result, 'answer':b})