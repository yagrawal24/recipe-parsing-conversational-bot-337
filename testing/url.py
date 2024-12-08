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
    updated_ingredients = copy.deepcopy(ingredients)

    for ingredient in updated_ingredients:
        ingredient_name = ingredient.get('name', '').strip().lower()

        for to_replace, replacers in alternatives.items():
            if to_replace.lower() in ingredient_name:
                ingredient['name'] = replacers[0]
                break

    return updated_ingredients

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

def adjust_ingredient_amounts_with_rules(ingredients, factor):
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

def transform_instructions(instructions, ingredient_map={}, technique_map={}):
    transformed_instructions = []

    for line in instructions:
        line_lower = line.lower()

        for old_ing, new_ing in ingredient_map.items():
            if old_ing in line_lower:
                line = line.replace(old_ing, ' or '.join(new_ing))

        for old_tech, new_tech in technique_map.items():
            if old_tech in line_lower:
                line = line.replace(old_tech, ' or '.join(new_tech))

        transformed_instructions.append(line)

    return transformed_instructions

def transform_recipe(ingredients, instructions, ingredient_map={}, technique_map={}):
    ingredients_copy = copy.deepcopy(ingredients)
    instructions_copy = copy.deepcopy(instructions)

    alternatives = find_ingredients(ingredients_copy, ingredient_map)
    transformed_ingredients = replace_ingredients(ingredients_copy, alternatives) if ingredient_map else ingredients_copy
    transformed_instructions = transform_instructions(instructions_copy, ingredient_map, technique_map)

    return {
        "ingredients": transformed_ingredients,
        "instructions": transformed_instructions,
    }


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
            if style == "vegetarian":
                file.write("Ingredients:\n")
                for original, replacements in recipe.items():
                    file.write(f" - {original}: replaced with {', '.join(replacements)}\n")
                file.write("\nInstructions:\n")
                for step in input_instructions:
                    file.write(f" - {step}\n")
            elif style in ["doubled", "halved"]:
                file.write("Ingredients:\n")
                for ingredient in recipe:
                    file.write(f" - {ingredient['quantity']} {ingredient.get('unit', '')} {ingredient['name']}\n")
                file.write("\nInstructions:\n")
                for step in input_instructions:
                    file.write(f" - {step}\n")
            else:
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
    # fetch_page_from_url(url)

    ### Test extract methods per step below ###

    ingredients, instructions = fetch_page_from_url(url)

    # print(instructions)
    # print('\n')

    # print(ingredients)
    # print('\n')

    # print(ingredients)
    # print('\n')

    doubled_ingredients = adjust_ingredient_amounts_with_rules(ingredients, 2)
    # print(doubled_ingredients)
    # print('\n')

    halved_ingredients = adjust_ingredient_amounts_with_rules(ingredients, 0.5)
    # print(halved_ingredients)
    # print('\n')

    vegetarian = find_ingredients(ingredients, to_vegetarian)

    # print(alternatives)

    # ingredients = replace_ingredients(ingredients, alternatives)

    # print(ingredients)
    # print('\n')

    # transformed_instructions = transform_instructions(instructions, ingredient_map=to_healthy)

    # print(transformed_instructions)
    # print('\n')

    # transformed_instructions = transform_cooking_methods(instructions, "roast")

    # print(transformed_instructions)
    # print('\n')

    transformed_recipe_italian = transform_recipe(
        ingredients, 
        instructions, 
        ingredient_map=italian_style["ingredients"], 
        technique_map=italian_style["techniques"]
    )

    # print(transformed_recipe_italian["instructions"])
    # print('\n')

    transformed_recipe_mexican = transform_recipe(
        ingredients, 
        instructions, 
        ingredient_map=mexican_style["ingredients"], 
        technique_map=mexican_style["techniques"]
    )

    # print(transformed_recipe_mexican["instructions"])
    # print('\n')

    transformed_recipe_chinese = transform_recipe(
        ingredients,
        instructions,
        ingredient_map=chinese_style["ingredients"],
        technique_map=chinese_style["techniques"]
    )

    # print(transformed_recipe_chinese["instructions"])
    # print('\n')

    transformed_recipes = {
        "vegetarian" : vegetarian,
        "doubled" : doubled_ingredients,
        "halved" : halved_ingredients,
        "italian": transformed_recipe_italian,
        "mexican": transformed_recipe_mexican,
        "chinese": transformed_recipe_chinese
    }

    write_to_file(ingredients, instructions, transformed_recipes)

    # methods_per_step = extract_cooking_methods_per_step(instructions)
    # print("\nCooking methods per step:")
    # for step_info in methods_per_step:
    #     print(f"Step: {step_info['step']}")
    #     print(f"Methods: {', '.join(step_info['methods'])}")
    #     print("-" * 50)