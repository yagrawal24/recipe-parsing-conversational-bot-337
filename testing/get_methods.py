import spacy
from typing import List
from url import *

# url = "https://www.allrecipes.com/recipe/218091/classic-and-simple-meat-lasagna/"
url = "https://www.allrecipes.com/one-pot-chicken-pomodoro-recipe-8730087/"

ingredients, instructions = fetch_page_from_url(url)

# print(instructions)

# ['serve', 'bubble', 'brown', 'stir', 'cook', 'melt', 'add', 'sprinkle', 'salt']
# def extract_cooking_methods(sentences):
#     # Load spaCy's medium English model for word vectors
#     nlp = spacy.load('en_core_web_md')
#     extracted_methods = set()
#     cook_token = nlp('cook')[0]
#     for sentence in sentences:
#         doc = nlp(sentence)
#         for token in doc:
#             if token.pos_ == 'VERB':
#                 lemma = token.lemma_.lower()
#                 # Compute similarity to 'cook'
#                 similarity = token.similarity(cook_token)
#                 if similarity > 0.3:
#                     extracted_methods.add(lemma)
#     return list(extracted_methods)

# ['cook', 'allow', 'cover', 'add', 'stand', 'remove', 'preheat', 'bring', 'mix', 'begin', 'melt', 'bake', 'serve', 'bubble', 'brown', 'combine', 'stir', 'salt', 'end', 'sprinkle']
# def extract_cooking_methods(sentences):
#     # Load spaCy's small English model    
#     nlp = spacy.load('en_core_web_sm')
#     extracted_methods = set()
#     for sentence in sentences:
#         doc = nlp(sentence)
#         for token in doc:
#             # Check if the token is a verb (excluding auxiliary verbs)
#             if token.pos_ == 'VERB' and token.dep_ not in ('aux', 'auxpass'):
#                 lemma = token.lemma_.lower()
#                 extracted_methods.add(lemma)
#     return list(extracted_methods)

# ['Add', 'Bake', 'Bring', 'Cook', 'Cover', 'Ending', 'Lay', 'Mix', 'Place', 'Preheat', 'Remove', 'Sprinkle', 'Stir']
def extract_cooking_methods(instructions: List[str]) -> List[str]:
    nlp = spacy.load("en_core_web_sm")
    cooking_methods = set()
    
    for instruction in instructions:
        doc = nlp(instruction.lower().strip())
        
        for i, token in enumerate(doc):
            if token.pos_ == "VERB":
                is_start = i == 0 or doc[i-1].text in {"then", "and", ",", ";"}
                has_object = any(child.dep_ in {"dobj", "pobj"} for child in token.children)
                
                if is_start or has_object:
                    cooking_methods.add(token.text.capitalize())
    
    return sorted(list(cooking_methods))

methods = extract_cooking_methods(instructions)
print(methods)
