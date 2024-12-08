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
import copy
from fractions import Fraction

###
### Parsing
###

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

###
### Ingredient Replacement
###

# Find ingredients that should be changed and what they should change to
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

# Actually replace ingredients in new ingredients list
def replace_ingredients(ingredients, alternatives):
    updated_ingredients = copy.deepcopy(ingredients)

    for ingredient in updated_ingredients:
        ingredient_name = ingredient.get('name', '').strip().lower()

        for to_replace, replacers in alternatives.items():
            if to_replace.lower() in ingredient_name:
                ingredient['name'] = replacers[0]
                break

    return updated_ingredients

###
### Adjust the instructions
###

# Adjust instructions with ingredient changes
def transform_instructions(instructions, ingredient_map={}, technique_map={}):
    transformed_instructions = []

    for line in instructions:
        line_lower = line.lower()

        for old_ing, new_ing in ingredient_map.items():
            if old_ing in line_lower:
                line_lower = line_lower.replace(old_ing, ' or '.join(new_ing))

        for old_tech, new_tech in technique_map.items():
            if old_tech in line_lower:
                line_lower = line_lower.replace(old_tech, ' or '.join(new_tech))

        transformed_instructions.append(line_lower)

    return transformed_instructions

# Adjust the instructions based on a new primary cooking method [doesn't fully work]
def transform_cooking_methods(instructions, to_method):
    cooking_methods_list = [
        "bake", "fry", "grill", "steam", "simmer", "roast", "saute", "broil",
        "stir", "poach", "boil", "sear", "braise", "toast", "pressure cook"
    ]

    transformed_instructions = []

    for instruction in instructions:
        doc = nlp(instruction.lower())
        methods_in_instruction = set()
        for token in doc:
            if (
                token.pos_ == "VERB" 
                and token.lemma_ in cooking_methods_list
                and any(child.dep_ in {"dobj", "prep", "advmod"} for child in token.children)
            ):
                methods_in_instruction.add(token.text)
        transformed_instruction = instruction.lower()
        for method in methods_in_instruction:
            transformed_instruction = re.sub(
                r"\b" + re.escape(method) + r"\b",
                to_method.lower(),
                transformed_instruction,
                flags=re.IGNORECASE
            )
        transformed_instructions.append(transformed_instruction.capitalize())

    return transformed_instructions


###
### Replace quantities in ingredients and instructions
###

### Handles fractions in instructions
def parse_fraction(quantity_str):
    parts = quantity_str.split()
    if len(parts) == 1:
        if '/' in parts[0]:
            numerator, denominator = parts[0].split('/')
            return Fraction(int(numerator), int(denominator))
        else:
            return Fraction(str(float(parts[0])))
    else:
        whole = int(parts[0])
        frac_part = parts[1]
        numerator, denominator = frac_part.split('/')
        return Fraction(whole * int(denominator) + int(numerator), int(denominator))

def format_fraction(frac):
    if frac.denominator == 1:
        return str(frac.numerator)
    else:
        whole = frac.numerator // frac.denominator
        remainder = frac.numerator % frac.denominator
        if whole == 0:
            return f"{remainder}/{frac.denominator}"
        else:
            return f"{whole} {remainder}/{frac.denominator}"
        
def substr(word, list):
    for i in list:
        if word in i or i in word:
            return True
    return False

# Handle scaling in ingredients list
def adjust_ingredient_amounts(ingredients, factor):
    sensitive_ingredients = {
        "salt": 1.5,
        "red pepper flakes": 1.5,
        "baking powder": 1.2,
        "baking soda": 1.2,
        "vinegar": 1.5,
        "alcohol": 1.5
    }
    
    non_scalable_ingredients = {"eggs", "vanilla extract", "yeast"}

    adjusted_ingredients = []

    for ingredient in ingredients:
        adjusted_ingredient = ingredient.copy()
        quantity = ingredient.get("quantity")
        name = ingredient.get("name", "").lower().strip()
        if quantity:
            try:
                if name in non_scalable_ingredients:
                    adjusted_ingredient["quantity"] = quantity
                else:
                    scale_factor = factor
                    for sensitive, max_scale in sensitive_ingredients.items():
                        if sensitive in name:
                            scale_factor = min(scale_factor, max_scale)
                            break
                    if "/" in quantity:
                        numerator, denominator = map(float, quantity.split("/"))
                        adjusted_quantity = scale_factor * (numerator / denominator)
                    elif " " in quantity:
                        whole, fraction = quantity.split()
                        numerator, denominator = map(float, fraction.split("/"))
                        adjusted_quantity = scale_factor * (float(whole) + numerator / denominator)
                    else:
                        adjusted_quantity = scale_factor * float(quantity)
                    adjusted_ingredient["quantity"] = str(round(adjusted_quantity, 2)).rstrip(".0")
            except ValueError:
                adjusted_ingredient["quantity"] = quantity

        adjusted_ingredients.append(adjusted_ingredient)

    return adjusted_ingredients

# Handle scaling in instructions
def scale_instructions(ingredients, instructions, factor=None):
    if not factor:
        return instructions

    measurements = set()
    ingredient_names = set()
    for ing in ingredients:
        if "unit" in ing and ing["unit"]:
            measurements.add(ing["unit"].lower())

        if "name" in ing and ing["name"]:
            ingredient_names.add(ing['descriptor'] +' ' + ing["name"] if 'descriptor' in ing.keys() else ing['name'])

    scaled_instructions = []

    for line in instructions:
        words = line.split()
        i = 0
        while i < len(words):
            word = words[i]
            
            # Handles mixed fractions (i.e. 1 1/2)
            if i + 1 < len(words):
                try:
                    whole_num = float(word)
                    next_token = words[i+1]
                    if '/' in next_token:
                        combined = f"{word} {next_token}"
                        del words[i+1]
                        word = combined
                except ValueError:
                    pass
            
            # look for fractions
            parsed_value = None
            try:
                parsed_value = parse_fraction(word)
            except:
                pass
            
            # check if next word is found in our ingredients list (i.e. teaspoon)
            if parsed_value is not None and i + 1 < len(words):
                next_word = words[i+1].lower()
                if next_word != "to" and next_word != "F" and (substr(next_word, measurements) or substr(next_word, ingredient_names)):
                    new_quantity = parsed_value * factor
                    if new_quantity.is_integer():
                        words[i] = str(int(new_quantity))
                    else:
                        words[i] = str(new_quantity)
             

            i += 1

        scaled_instructions.append(" ".join(words))

    return scaled_instructions

###
### Single function needed to make any recipe transformation (except for change in primary method)
###
def transform_recipe(ingredients, instructions, ingredient_map={}, technique_map={}, scale=None):
    ingredients_copy = copy.deepcopy(ingredients)
    instructions_copy = copy.deepcopy(instructions)

    alternatives = find_ingredients(ingredients_copy, ingredient_map)
    transformed_ingredients = replace_ingredients(ingredients_copy, alternatives) if ingredient_map else ingredients_copy
    transformed_instructions = transform_instructions(instructions_copy, ingredient_map, technique_map) if ingredient_map or technique_map else instructions_copy
    
    if scale != None:
        transformed_ingredients = adjust_ingredient_amounts(transformed_ingredients, scale)
        transformed_instructions = scale_instructions(transformed_ingredients, transformed_instructions, scale)

    return {
        "ingredients": transformed_ingredients,
        "instructions": transformed_instructions
    }



###
### Print to human-readable format
###
def write_to_file(input_ingredients, input_instructions, transformed_recipes, filename="recipe_transformations.txt"):
    with open(filename, "w") as file:
        file.write("Original Recipe:\n")
        file.write("Ingredients:\n")
        for ingredient in input_ingredients:
            file.write(f" - {ingredient['quantity']} {ingredient.get('unit', '')} {ingredient['name']}\n")
        
        file.write("\nInstructions:\n")
        for step in input_instructions:
            file.write(f" - {step}\n")

        file.write("\nTransformed Recipes:\n")
        for style, recipe in transformed_recipes.items():
            file.write(f"\n{style.title()} Transformation:\n")
            # if style in ["doubled", "halved"]:
            #     file.write("Ingredients:\n")
            #     for ingredient in recipe:
            #         file.write(f" - {ingredient['quantity']} {ingredient.get('unit', '')} {ingredient['name']}\n")
            #     file.write("\nInstructions:\n")
            #     for step in input_instructions:
            #         file.write(f" - {step}\n")
            # else:
            file.write("Ingredients:\n")
            for ingredient in recipe["ingredients"]:
                file.write(f" - {ingredient['quantity']} {ingredient.get('unit', '')} {ingredient['name']}\n")
            file.write("\nInstructions:\n")
            for step in recipe["instructions"]:
                file.write(f" - {step}\n")

        file.write("\n--- End of Transformations ---\n")

if __name__ == "__main__":
    # url = "https://www.allrecipes.com/recipe/218091/classic-and-simple-meat-lasagna/"
    url = "https://www.allrecipes.com/one-pot-chicken-pomodoro-recipe-8730087/"
    # url = "https://www.allrecipes.com/mediterranean-baked-cod-with-lemon-recipe-8576313"

    ingredients, instructions = fetch_page_from_url(url)

    doubled_ingredients = transform_recipe(ingredients, instructions, scale=2.0)

    halved_ingredients = transform_recipe(ingredients, instructions, scale=0.5)

    vegetarian = transform_recipe(ingredients, instructions, ingredient_map = to_vegetarian)
    healthy = transform_recipe(ingredients, instructions, ingredient_map = to_healthy)
    gluten_free = transform_recipe(ingredients, instructions, ingredient_map = gluten_free)
    lactose_free = transform_recipe(ingredients, instructions, ingredient_map = lactose_free)

    transformed_recipe_italian = transform_recipe(
        ingredients, 
        instructions, 
        ingredient_map=italian_style["ingredients"], 
        technique_map=italian_style["techniques"]
    )

    transformed_recipe_mexican = transform_recipe(
        ingredients, 
        instructions, 
        ingredient_map=mexican_style["ingredients"], 
        technique_map=mexican_style["techniques"]
    )

    transformed_recipe_chinese = transform_recipe(
        ingredients,
        instructions,
        ingredient_map=chinese_style["ingredients"],
        technique_map=chinese_style["techniques"]
    )

    transformed_recipes = {
        "gluten_free" : gluten_free,
        "lactose_free" : lactose_free,
        "vegetarian" : vegetarian,
        "healthy" : healthy,
        "doubled" : doubled_ingredients,
        "halved" : halved_ingredients,
        "italian": transformed_recipe_italian,
        "mexican": transformed_recipe_mexican,
        "chinese": transformed_recipe_chinese
    }

    write_to_file(ingredients, instructions, transformed_recipes)