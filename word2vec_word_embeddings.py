# -*- coding: utf-8 -*-
"""
Created on Sun Mar 13 22:09:41 2022

@author: bejob
"""
from gensim.models import Word2Vec
from gensim.models.callbacks import CallbackAny2Vec
import re
from os import listdir
from legal_concept_resources import abbreviations


from datetime import datetime

#%%

def clean_text(text, stopwords):
    
    tag_raw_text = text.lower()
    # "."-exceptions
    exceptions_list = abbreviations
    
    month_list = ["januar", "februar", "marts", "april", "maj", "juni",
             "juli", "august", "september", "oktober", "november", "december"]
    
    for i in range(0,10):
        for month in month_list:
            date = f"{i}. {month}"
            replacement = f"{i} {month}"
            tag_raw_text = tag_raw_text.replace(date,replacement)
    
    for exception in exceptions_list:
        tag_raw_text = tag_raw_text.replace(exception[0],"")
    
    tag_raw_text = re.sub(r"[^a-zæøå ]","", tag_raw_text)    
    
    #stemmer = DanishStemmer()
    
    new_text = ""
    for word in tag_raw_text.split():
        #word = stemmer.stem(word)
        if word in stopwords:
            continue
        else:
            new_text = new_text + " " + word 
    
    return new_text[1:]


def data_cleaner(directory, stopwords):
    in_raw_text = listdir(directory)
    in_clean_text = listdir("clean text")
    
    
    
    percent_step = 100/len(in_raw_text)
    
    percent = 0
    for filename in in_raw_text:
        if "LICENSE" not in filename and ".json" not in filename:
            if filename not in in_clean_text:
                cleaned_lines = []
                d = f"{directory}/{filename}"
                for line in open(d, "r", encoding="UTF-8"):
                    cleaned_lines.append(clean_text(line, stopwords))
                
                with open("clean text/"+filename, "w", encoding="UTF-8") as f:
                    for line in cleaned_lines:
                        if len(line) > 0:
                            f.write(line)
                            f.write("\n")
                        else:
                            continue
                 
                percent += percent_step
                print(f"{percent} % done")

#%% taken from https://stackoverflow.com/q/60852962
class training_corpus():
    def __init__(self):
        self.files = listdir("C:/Users/bejob/Documents/legal concept data/clean text")
        self.run = 0
        
    def __iter__(self):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"Starting data-iteration {self.run} at {now}")
        print("---")
        for file in self.files:
            for line in open("C:/Users/bejob/Documents/legal concept data/clean text/"+file, encoding="UTF-8"):
                words = line.split()
                yield words
        self.run += 1

#%% callback taken from https://stackoverflow.com/a/54891714
class callback(CallbackAny2Vec):

    def __init__(self):
        self.epoch = 0

    def on_epoch_end(self, model):
        loss = model.get_latest_training_loss()
        epoch_end_time = datetime.now().strftime("%H:%M:%S")
        print(f"End epoch at {epoch_end_time}")
        print('Loss after epoch {}: {}'.format(self.epoch, loss))
        self.epoch += 1


if __name__ == "__main__":        
    #%% Data cleaning
    # I have added retsinformationdk + skat + retspraksis + tv2r + wiki + adl + danavis 
    #               + dannet + depbank + ep + ft + gutenberg + hest + opensub + relig + wikibooks
    
    with open("stopord.txt","r", encoding="UTF-8") as sw_file:
        stopwords = [line.strip() for line in sw_file]
    
    start = datetime.now().strftime("%H:%M:%S")
    print(f"Started at {start}")
    
    
    data_cleaner("dagw/sektioner/wikibooks", stopwords)
    
    
    print(f"Started at {start}")
    end = datetime.now().strftime("%H:%M:%S")
    print(f"Finished at {end}")
    
    
    #%% Model train 
    sentences = training_corpus()
    print("Skipgram training started at:")
    print(datetime.now().strftime("%H:%M:%S"))
    model = Word2Vec(sentences, size=100, window=5, min_count=2, workers=18, sg=1, 
                     compute_loss=True, callbacks=[callback()])
    
    model.save("models/word2vec_100_skipgram_w5_mc2_version7.model")
    
    print("Skipgram training finnished at:")
    print(datetime.now().strftime("%H:%M:%S"))
    
    print("----------------------------------------------------")
    
    print("CBOW training started at:")
    print(datetime.now().strftime("%H:%M:%S"))
    model = Word2Vec(sentences, size=100, window=5, min_count=2, workers=18, sg=0, 
                     compute_loss=True, callbacks=[callback()])
    
    model.save("models/word2vec_100_CBOW_w5_mc2_version8.model")
    
    print("CBOW training finnished at:")
    print(datetime.now().strftime("%H:%M:%S"))
    
    #version2 only trained on retsinformationdk
    #version3 trained on retsinformationdk + skat + retspraksis + tv2r + wiki -> trainingstid ca. 29min
    #version4 trained on retsinformationdk + skat + retspraksis + tv2r + wiki -> trainingstid ca. 30min
    
    #version 5 & 6 are trained on:
        # retsinformationdk + skat + retspraksis + tv2r + wiki + adl + danavis
        # 
    
    #%% Model test
    
    test_model = Word2Vec.load("models/word2vec_300_CBOW_w5_mc2_version6.model")
    
    test_model.wv.vectors.shape
    
    test_model.wv["funktionær"]

