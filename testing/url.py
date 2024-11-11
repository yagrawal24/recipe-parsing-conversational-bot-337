import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import inflection
import json

def fetch_page_from_url(url):
    if "allrecipes.com" not in url:
        return "Please provide a URL from AllRecipes.com."

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        # for i in soup:
        #     print(i, "\n\n--------------------------\n\n")
        #     for j in i:
        #         print(j, "\n-_-_-_-_-_-_-_-\n")
        title_element = soup.find("h1", class_="headline")
        if title_element:
            title = title_element.text.strip()
        else:
            parsed_url = urlparse(url)
            url_title = parsed_url.path.split('/')[-2]
            title = inflection.titleize(url_title.replace('-', ' '))

        # ingredients in <script class="comp allrecipes-schema mntl-schema-unified" id="allrecipes-schema_1-0" type="application/ld+json">
        details = [item.text.strip() for item in soup.find_all("script", class_="comp allrecipes-schema mntl-schema-unified")]
        details_json = json.loads(details[0])[0]
        ingredients = details_json['recipeIngredient']
        instructions = details_json['recipeInstructions']

        recipe_data = f"Title: {title}\n\nIngredients:\n" + "\n".join(ingredients) + "\n\nInstructions:\n" + "\n".join([i['text'] for i in instructions])

        with open("recipe_data.txt", "w") as file:
            file.write(recipe_data)

        return details_json, ingredients, instructions

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    url = "https://www.allrecipes.com/recipe/218091/classic-and-simple-meat-lasagna/"
    fetch_page_from_url(url)
