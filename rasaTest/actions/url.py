import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import inflection
import re
import spacy
import json

# Load SpaCy model
nlp = spacy.load("en_core_web_md")

def fetch_page_from_url(url):
    if "allrecipes.com" not in url:
        return "Please provide a URL from AllRecipes.com."

    try:
        response = requests.get(url)
        response.raise_for_status()

        # old, worked for simple recipes (1 ingredients list) but not more complex ones (2+ ingredient lists)
        # soup = BeautifulSoup(response.content, 'html.parser')
        # title_element = soup.find("h1", class_="headline")
        
        soup = BeautifulSoup(response.content, 'html5lib')
        
        title_element = soup.find("h1", class_="article-heading text-headline-400")
        
        if title_element:
            title = title_element.text.strip()
        else:
            parsed_url = urlparse(url)
            url_title = parsed_url.path.split('/')[-2]
            title = inflection.titleize(url_title.replace('-', ' '))

        # old
        # details = [item.text.strip() for item in soup.find_all("script", class_="comp allrecipes-schema mntl-schema-unified")]
        # details_json = json.loads(details[0])
        # ingredients = details_json[0]['recipeIngredient']
        # instructions = details_json[0]['recipeInstructions']

        # recipe_data = f"Title: {title}\n\nIngredients:\n" + "\n".join(ingredients) + "\n\nInstructions:\n" + "\n".join([i['text'] for i in instructions])
        
        
        # collect ingredients from html
        ingredients_raw = [i.find_all('span') for i in soup.find_all("li", class_="mm-recipes-structured-ingredients__list-item")]

        ingredients = []

        for i in ingredients_raw:
            curr_dict = {}
            for j in i:
                key = list(j.attrs.keys())[0].split('-')[-1]
                curr_dict.update({key:j.string})
            ingredients.append(curr_dict)
            
        # collect instructions from HTML
        instructions = [s.text.replace("\n", "") for s in soup.find_all("p", class_="comp mntl-sc-block mntl-sc-block-html")]
                
        recipe_data = f"Title: {title}\n\nIngredients:\n" + "\n".join(print_ingredients_list(ingredients)) + "\n\nInstructions:\n" + "\n".join(instructions)

        with open("recipe_data.txt", "w") as file:
            file.write(recipe_data)

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


if __name__ == "__main__":
    url = "https://www.allrecipes.com/recipe/218091/classic-and-simple-meat-lasagna/"
    # url = "https://www.allrecipes.com/one-pot-chicken-pomodoro-recipe-8730087/"
    fetch_page_from_url(url)