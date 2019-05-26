import json
import os

def tokenize(sentence):
    sentence = sentence.lower()
    sentence = sentence.replace(',', '').replace('?', '').replace('\'s', ' \'s')
    sentence = sentence.replace('\' ', ' ')
    sentence = sentence.replace('aren\'t', 'are not')
    sentence = sentence.replace('isn\'t', 'is not')
    sentence = sentence.replace('-', ' ')
    words = sentence.split()
    return words

dataroot = '/home/qing/Desktop/Datasets/GQA/'
try:
    question_vocab = json.load(open('data/question_vocab.json'))
    operation_vocab = json.load(open('data/operation_vocab.json'))
    argument_vocab = json.load(open('data/argument_vocab.json'))
    answer_vocab = json.load(open('data/answer_vocab.json'))

    word2vocab_id = dict(zip(question_vocab, range(len(question_vocab))))
    operation2id = dict(zip(operation_vocab, range(len(operation_vocab))))
    argument2id = dict(zip(argument_vocab, range(len(argument_vocab))))
    answer2id = dict(zip(answer_vocab, range(len(answer_vocab))))
except IOError as err:
    print(err)

img_feat_path = os.path.join(dataroot, 'allImages/gqa_objects.h5')
img_feat_info_path = os.path.join(dataroot, 'allImages/gqa_objects_merged_info.json')
