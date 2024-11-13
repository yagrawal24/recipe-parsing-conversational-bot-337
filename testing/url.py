import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import inflection
import re

def extract_quantity(ingredient_line):
    quantity_pattern = r'(\b\d+\s?\d*\/?\d*\
        b|\b\d+\.\d+\b)'
    match = re.search(quantity_pattern, ingredient_line)
    return match.group(0) if match else None

def extract_ingredient_name(ingredient_line, quantity):
    if quantity:
        ingredient_name = ingredient_line.replace(quantity, "").strip()
    else:
        ingredient_name = ingredient_line.strip()
    return ingredient_name

def fetch_page_from_url(url):
    if "allrecipes.com" not in url:
        return "Please provide a URL from AllRecipes.com."

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        title_element = soup.find("h1", class_="headline")
        if title_element:
            title = title_element.text.strip()
        else:
            parsed_url = urlparse(url)
            url_title = parsed_url.path.split('/')[-2]
            title = inflection.titleize(url_title.replace('-', ' '))

        ingredients_data = []
        ingredients = soup.find_all("span", class_="ingredients-item-name")

        for ingredient in ingredients:
            ingredient_text = ingredient.text.strip()
            quantity = extract_quantity(ingredient_text)
            ingredient_name = extract_ingredient_name(ingredient_text, quantity)
            ingredients_data.append(f"{ingredient_name} (Quantity: {quantity})" if quantity else ingredient_name)

        instructions = [step.text.strip() for step in soup.find_all("div", class_="paragraph")]
        recipe_data = f"Title: {title}\n\nIngredients:\n" + "\n".join(ingredients_data) + "\n\nInstructions:\n" + "\n".join(instructions)

        with open("recipe_data.txt", "w") as file:
            file.write(recipe_data)

        return "Recipe data has been written to recipe_data.txt"

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"

url = "https://www.allrecipes.com/recipe/218091/classic-and-simple-meat-lasagna/"
fetch_page_from_url(url)