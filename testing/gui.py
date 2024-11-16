import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import inflection
import re
import spacy
from googlesearch import search

# Load SpaCy model
nlp = spacy.load("en_core_web_md")

def fetch_page_from_url(url):
    if "allrecipes.com" not in url:
        return "Please provide a URL from AllRecipes.com.", []

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

        ingredients_raw = [i.find_all('span') for i in soup.find_all("li", class_="mm-recipes-structured-ingredients__list-item")]
        ingredients = []
        for i in ingredients_raw:
            curr_dict = {}
            for j in i:
                key = list(j.attrs.keys())[0].split('-')[-1]
                curr_dict.update({key: j.string})
            ingredients.append(curr_dict)
        
        instructions = [s.text.replace("\n", "") for s in soup.find_all("p", class_="comp mntl-sc-block mntl-sc-block-html")]

        return ingredients, instructions
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        return [], []

def print_ingredients_list(ingredients_list):
    ingredients_print = []
    for i in ingredients_list:
        s = ""
        for j in i:
            if i[j] is not None:
                s += i[j] + " "
        ingredients_print.append(s.strip())
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

def google_search(query, num_results=1):
    try:
        results = list(search(query, num=num_results, stop=num_results, pause=2))
        return results[0] if results else "No results found."
    except Exception as e:
        return f"Error performing search: {e}"

# GUI Code
class RecipeChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Recipe Chatbot")
        self.ingredients = []
        self.instructions = []
        self.step = 0

        # URL Input
        self.url_label = tk.Label(root, text="Recipe URL:")
        self.url_label.pack()
        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.pack()
        self.fetch_button = tk.Button(root, text="Fetch Recipe", command=self.fetch_recipe)
        self.fetch_button.pack()

        # Chat Output
        self.output_box = scrolledtext.ScrolledText(root, width=70, height=20, wrap=tk.WORD)
        self.output_box.pack()
        self.output_box.insert(tk.END, "Hello! What recipe would you like to cook today? Please paste the link here to get started.\n")

        # User Input
        self.user_input = tk.Entry(root, width=50)
        self.user_input.pack()
        self.ask_button = tk.Button(root, text="Ask", command=self.handle_user_input)
        self.ask_button.pack()

    def fetch_recipe(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please enter a recipe URL.")
            return
        self.ingredients, self.instructions = fetch_page_from_url(url)
        self.step = 0
        self.output_box.insert(tk.END, "Recipe fetched successfully!\n")

    def handle_user_input(self):
        user_text = self.user_input.get().strip()
        if not user_text:
            messagebox.showwarning("Input Required", "Please enter a question.")
            return

        if user_text == "What are the ingredients?":
            if not self.ingredients:
                self.output_box.insert(tk.END, "No ingredients found.\n")
            else:
                for ingredient in print_ingredients_list(self.ingredients):
                    self.output_box.insert(tk.END, ingredient + "\n")

        elif user_text == "What is the next step?":
            if not self.instructions:
                self.output_box.insert(tk.END, "No instructions found.\n")
            elif self.step >= len(self.instructions):
                self.output_box.insert(tk.END, "That was the last step!\n")
            else:
                self.output_box.insert(tk.END, self.instructions[self.step] + "\n")
                self.step += 1

        elif user_text == "What tools do I need?":
            if not self.instructions:
                self.output_box.insert(tk.END, "No instructions found to extract tools.\n")
            else:
                tools = extract_tools(self.instructions)
                self.output_box.insert(tk.END, "Tools: " + ", ".join(tools) + "\n")

        elif user_text.startswith("What is"):
            query = user_text
            search_result = google_search(query)
            self.output_box.insert(tk.END, f"Here's a helpful link: {search_result}\n")

        else:
            self.output_box.insert(tk.END, "I'm sorry, I don't understand that command.\n")

        self.user_input.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = RecipeChatbotGUI(root)
    root.mainloop()
