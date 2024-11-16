from url import *
from googlesearch import search
import re
import urllib.parse

def fetch_ingredient_quantity(ingredients, ingredient):
    for i in ingredients:
        if ingredient in i['name']:
            return i['quantity'], i['unit']
        
def conversation():
    text = input("What recipe would you like to cook today? Please paste a recipe link from allrecipes.com here to get started.\n")
    
    ingredients, instructions = fetch_page_from_url(text)
    step = 0
    pattern_how = r"(?i)^how\s+(to|do)\b"
    pattern_what = r"(?i)^what\s+is\b"

    while text != "Done":
        text = input("\nWhat would you like to do next?\n")
        
        if text == "What are the ingredients?":
            for i in print_ingredients_list(ingredients):
                print(i)
        
        elif text == "What is the next step?":
            if step >= len(instructions):
                print("That was the last step!")
            else:
                print(instructions[step])
                step += 1
        
        elif text == "What is the previous step?":
            print(instructions[step-1])
            
        elif text == "How do I do that?":
            print("Please look at the following link for reference:")
            print([i for i in search("How to:" + instructions[step-1], stop=1)][0])

        elif re.match(pattern_how, text):
            base_url = "https://www.youtube.com/results?search_query="
            encoded_query = urllib.parse.quote(text)
            final_url = f"{base_url}{encoded_query}"
            print(f"No worries. I found a reference for you: {final_url}")

        elif re.match(pattern_what, text):
            # https://www.geeksforgeeks.org/performing-google-search-using-python-code/
            query = text
            try:
                result = [i for i in search(query, num=1, stop=1, pause=2)][0]
                print(f"Here's a helpful link for your question: {result}")
            except Exception as e:
                print(f"Sorry, I couldn't find an answer for that. Error: {e}")
            
        # How much X do I need?
        
        # How many X do I need?
        
        else:
            print("I'm sorry, I'm not smart enough to understand that!")
    
    print("I hope I was able to help with your cooking journey today. Enjoy the food!")

if __name__ == "__main__":
    print(r'Hello, My name is Gordon! I will be your personal sous chef for today. Before we get started, please note that you can type "Done" at any time to exit the conversation.')
    conversation()
