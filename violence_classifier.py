# Make sure you have trarnsformers  and torch installed
import sys

from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from sklearn.calibration import calibration_curve
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import matplotlib.pyplot as plt
#Loads the model from the folder 'best_model'
first_model = AutoModelForSequenceClassification.from_pretrained('best_model', num_labels=2)
tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
# Makes the model easy to use:
# Usage: nlp(string or strings to classify)
# Output = [{'labels': "LABEL_1", 'score': probability} for string in input]
# Violent Content = LABEL_1, Non-Violent = LABEL_0
nlp = pipeline("sentiment-analysis",model=first_model, tokenizer=tokenizer)

def classify(sentances):
    return nlp(sentances)  

if __name__=="__main__":
  print(classify(' '.join(sys.argv)))
