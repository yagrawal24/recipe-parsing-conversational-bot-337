import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import inflection
import re
import spacy
import json
import urllib.parse
from rapidfuzz import fuzz, process
from mapping import *
from difflib import SequenceMatcher

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

def get_youtube_search_url(query):
    base_url = "https://www.youtube.com/results?search_query="
    encoded_query = urllib.parse.quote(query)
    return f"{base_url}{encoded_query}"

def get_how_to_query_url(text, current_context=None):
    pattern_how_do_vague = r"how do i .*"
    pattern_how = r"how to .*"

    if re.match(pattern_how_do_vague, text):
        if current_context:
            return get_youtube_search_url(f"how to {current_context}")
        else:
            return None 
    elif re.match(pattern_how, text):
        return get_youtube_search_url(text)
    return None

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
    noun_chunks = []
    
    for i in nlp(instruction).noun_chunks:
        all_ingredients = i.text.split(", ")
        if isinstance(all_ingredients, list):
            noun_chunks += all_ingredients
        else:
            noun_chunks.append(all_ingredients.strip())
    
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

def find_ingredients(ingredients, substitution_map):
    def singularize(word):
        if word.endswith('ies'):
            return word[:-3] + 'y'
        elif word.endswith('es'):
            return word[:-2]
        elif word.endswith('s') and not word.endswith('ss'):
            return word[:-1]
        return word
    
    def find_best_match(ingredient_dict):
        ingredient_name = ingredient_dict['name'].strip()
        ingredient_lower = ' '.join(singularize(word) for word in ingredient_name.lower().split())
        words = ingredient_lower.split()
        
        if 'ground' in words:
            next_word_index = words.index('ground') + 1
            if next_word_index < len(words) and words[next_word_index] in proteins:
                protein = words[next_word_index]
                return [
                    (ingredient_name, substitution_map_lower['ground']),
                    (protein, ['tvp', 'soy crumbles'])
                ]
            return None
        
        if ingredient_lower in substitution_map_lower:
            return {ingredient_name: substitution_map_lower[ingredient_lower]}
        
        for key in substitution_map_lower:
            if key in words:
                return {ingredient_name: substitution_map_lower[key]}
        return None
    
    replacements = {}    
    substitution_map_lower = {k.lower(): v for k, v in substitution_map.items()}
    proteins = {'chicken', 'beef', 'pork', 'turkey', 'lamb', 'veal', 'fish'}
    
    for ingredient in ingredients:
        matches = find_best_match(ingredient)
        if matches:
            replacements.update(matches)
    return replacements

def replace_ingredients(ingredients, alternatives):
    updated_ingredients = ingredients.copy()

    for ingredient in updated_ingredients:
        ingredient_name = ingredient.get('name', '').strip().lower()

        for to_replace, replacers in alternatives.items():
            if to_replace.lower() in ingredient_name:
                ingredient['name'] = replacers[0]
                break

    return updated_ingredients

# def transform_instructions(instructions, transformation_map):
#     transformed_instructions = []

#     for instruction in instructions:
#         transformed_instruction = instruction

#         for original, replacements in transformation_map.items():
#             # Join the replacements if they are a list
#             replacement = ", ".join(replacements) if isinstance(replacements, list) else replacements
#             transformed_instruction = re.sub(
#                 r"\b" + re.escape(original) + r"\b", 
#                 replacement, 
#                 transformed_instruction, 
#                 flags=re.IGNORECASE
#             )
        
#         transformed_instructions.append(transformed_instruction)

#     return transformed_instructions

def transform_cooking_methods_to_refined(instructions, to_method):
    cooking_methods_list = [
        "bake", "fry", "grill", "steam", "simmer", "roast", "saute", "broil",
        "stir", "poach", "boil", "sear", "braise", "toast", "pressure cook"
    ]  # Extend this list as needed

    transformed_instructions = []

    for instruction in instructions:
        doc = nlp(instruction.lower())
        methods_in_instruction = set()

        # Identify verbs that are cooking methods and have cooking-related contexts
        for token in doc:
            if (
                token.pos_ == "VERB" 
                and token.lemma_ in cooking_methods_list
                and any(child.dep_ in {"dobj", "prep", "advmod"} for child in token.children)
            ):  # Ensure the verb is likely part of a cooking action
                methods_in_instruction.add(token.text)

        # Replace each detected cooking method with `to_method`
        transformed_instruction = instruction.lower()
        for method in methods_in_instruction:
            transformed_instruction = re.sub(
                r"\b" + re.escape(method) + r"\b",  # Match whole word
                to_method.lower(),
                transformed_instruction,
                flags=re.IGNORECASE
            )

        # Capitalize the transformed instruction
        transformed_instructions.append(transformed_instruction.capitalize())

    return transformed_instructions

def transform_instructions(instructions, ingredient_map={}, technique_map={}):
    transformed_instructions = []
    for line in instructions:
        line_lower = line.lower()
        
        # Replace techniques
        for old_tech, new_tech in technique_map.items():
            if old_tech in line_lower:
                line = line.replace(old_tech, ' or '.join(new_tech))
                
        # Replace ingredients
        for old_ing, new_ing in ingredient_map.items():
            if old_ing in line.lower():
                line = line.replace(old_ing, ' or '.join(new_ing))
        
        transformed_instructions.append(line)
    return transformed_instructions


def transform_recipe(ingredients, instructions, ingredient_map={}, technique_map={}):
    alternatives = find_ingredients(ingredients, ingredient_map)
    new_recipe = {
        "ingredients": replace_ingredients(ingredients, alternatives) if ingredient_map != {} else ingredients,
        "instructions": transform_instructions(instructions, ingredient_map, technique_map) 
    }
    return new_recipe

if __name__ == "__main__":
    # url = "https://www.allrecipes.com/recipe/218091/classic-and-simple-meat-lasagna/"
    # url = "https://www.allrecipes.com/one-pot-chicken-pomodoro-recipe-8730087/"
    url = "https://www.allrecipes.com/mediterranean-baked-cod-with-lemon-recipe-8576313"
    # fetch_page_from_url(url)

    ### Test extract methods per step below ###

    ingredients, instructions = fetch_page_from_url(url)

    print(instructions)
    print('\n')
    
    vegan_transform = transform_recipe(ingredients, instructions, to_vegetarian)
    print(vegan_transform, '\n')
    
    healthy_transform = transform_recipe(ingredients, instructions, to_healthy)
    print(healthy_transform, '\n')
    
    mexican_transform = transform_recipe(ingredients, instructions, mexican_style['ingredients'], mexican_style['techniques'])
    print(mexican_transform, '\n')
    
    italian_transform = transform_recipe(ingredients, instructions, italian_style['ingredients'], italian_style['techniques'])
    print(italian_transform, '\n')

    # print(ingredients)
    # print('\n')

    # alternatives = find_ingredients(ingredients, to_vegetarian)

    # print(alternatives)

    # ingredients = replace_ingredients(ingredients, alternatives)

    # print(ingredients)
    # print('\n')

    # transformed_instructions = transform_instructions(instructions, ingredient_map=to_healthy)

    # print(transformed_instructions)
    # print('\n')

    # transformed_instructions = transform_cooking_methods_to_refined(instructions, "roast")

    # print(transformed_instructions)
    # print('\n')

    # methods_per_step = extract_cooking_methods_per_step(instructions)
    # print("\nCooking methods per step:")
    # for step_info in methods_per_step:
    #     print(f"Step: {step_info['step']}")
    #     print(f"Methods: {', '.join(step_info['methods'])}")
    #     print("-" * 50)