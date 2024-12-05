import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import inflection
import re
import spacy
import json
from rapidfuzz import fuzz, process

# Load SpaCy model
nlp = spacy.load("en_core_web_md")

def fetch_page_from_url(url):
    if "allrecipes.com" not in url:
        return "Please provide a URL from AllRecipes.com."

    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html5lib')
        
        title_element = soup.find("h1", class_="article-heading text-headline-400")
        
        if title_element:
            title = title_element.text.strip()
        else:
            parsed_url = urlparse(url)
            url_title = parsed_url.path.split('/')[-2]
            title = inflection.titleize(url_title.replace('-', ' '))
        
        ingredients = extract_ingredients(soup)
            
        instructions = extract_instructions(soup)

        return ingredients, instructions

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"

# put ingredients and instructions in a .txt file for human readability
def print_ingredients_list(ingredients_list):
    ingredients_print = []
    for i in ingredients_list:
        s = ""
        for j in i:
            if i[j] != None:
                s += i[j] + " "
        ingredients_print.append(s)
    return ingredients_print

def extract_tools(instructions):
    tools_set = set()
    tool_patterns = r"\b(?:oven|pot|skillet|bowl|pan|foil|sheet|knife|dish|grater|plate|whisk|rack)\b"
    kitchen_tool_ref = nlp("kitchen tool")
    for instruction in instructions:
        doc = nlp(instruction)
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            if re.search(tool_patterns, chunk_text):
                tools_set.add(chunk_text)
            elif chunk.vector_norm and kitchen_tool_ref.vector_norm:
                similarity = chunk.similarity(kitchen_tool_ref)
                if similarity > 0.5:
                    tools_set.add(chunk_text)
    return list(tools_set)

def extract_cooking_methods(instructions):
    # nlp = spacy.load("en_core_web_sm")
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

def extract_cooking_methods_per_step(instructions):
    methods_per_step = []

    for instruction in instructions:
        sentences = re.split(r'[.?!]', instruction)
        methods = set()

        for sentence in sentences:
            if sentence.strip():
                doc = nlp(sentence.strip().lower())
                for i, token in enumerate(doc):
                    if token.pos_ == "VERB":
                        is_start = i == 0 or doc[i - 1].text in {"then", "and", ",", ";"}
                        has_object = any(child.dep_ in {"dobj", "pobj"} for child in token.children)

                        if is_start or has_object:
                            methods.add(token.text.capitalize())

        methods_per_step.append({"step": instruction, "methods": sorted(list(methods))})

    return methods_per_step

def extract_instructions(soup):
    header = soup.find('h2', string="Directions")

    if header:
        recipe_steps = []

        for sibling in header.find_all_next():
            if sibling.name == "h2":
                break

            if sibling.name == "p" and "compmntl-sc-blockmntl-sc-block-html" in ''.join(sibling.get("class", [])):
                step = sibling.get_text(strip=True)
                recipe_steps += step.split('. ')

        return recipe_steps
    else:
        print("No directions found!")

def classify(ingredient):
    '''
    Helper for extract_ingredients that separates information about an ingredient into components
    '''
    doc = nlp(ingredient)
    pairs = []
    for e in doc:
        if e.pos_ == "VERB" or e.pos_ == "ADV":
            pairs.append(["preparation", e.text])
        elif e.pos_ == "ADJ":
            pairs.append(["descriptor", e.text])
        elif e.pos_ == "NOUN" or e.pos_ == "PROPN":
            pairs.append(["name", e.text])
    
    return pairs

def extract_ingredients(soup):
    ingredients_html = [i for i in soup.find_all("li", class_="mm-recipes-structured-ingredients__list-item")]

    full_list = [i.find('p').text for i in ingredients_html]

    ingredients_lst = []
    for ingredient in ingredients_html:
        sub_dict = {}
        for child in ingredient.find('p').children:
            if child.text.strip() != "":
                if child.name == "span":
                    sub_dict.update({list(child.attrs.keys())[0].split('-')[-1]:child.text.strip()})
                else:
                    sub_dict.update({"other":child.strip()})
                    
        if "other" in list(sub_dict.keys()):
            sub_dict['name'] = sub_dict['other'] + " " + sub_dict['name']
            del sub_dict['other']
        
        if " or " in sub_dict['name']:
            splt = sub_dict['name'].split(" or ")
            sub_dict['name'] = splt[0]
            sub_dict.update({'alternative':splt[1]})
            
        ingredients_lst.append(sub_dict)
    
    for i in ingredients_lst:
        new_pairs = classify(i["name"])
        i["name"] = ''
        
        for key, word in new_pairs:
            if key not in i:
                i.update({key:word})
            else:
                i[key] += " " + word
                
    return ingredients_lst

def get_step_information(instruction, info_source, type, threshold=80):
    noun_chunks = [i.text for i in nlp(instruction).noun_chunks]
    
    if type == "ingredients":
        info = [i['name'] for i in info_source]
    elif type == "tools":
        info = info_source
        
    matches = []
    for chunk in noun_chunks:
        match = process.extractOne(chunk, info, scorer=fuzz.partial_ratio)
        if match and match[1] >= threshold:
            matches.append(match[0])
            
    return list(set(matches))

if __name__ == "__main__":
    url = "https://www.allrecipes.com/recipe/218091/classic-and-simple-meat-lasagna/"
    # url = "https://www.allrecipes.com/one-pot-chicken-pomodoro-recipe-8730087/"
    fetch_page_from_url(url)

    ### Test extract methods per step below ###

    # ingredients, instructions = fetch_page_from_url(url)

    # print("Extracted instructions:")
    # print(instructions)

    # methods_per_step = extract_cooking_methods_per_step(instructions)
    # print("\nCooking methods per step:")
    # for step_info in methods_per_step:
    #     print(f"Step: {step_info['step']}")
    #     print(f"Methods: {', '.join(step_info['methods'])}")
    #     print("-" * 50)