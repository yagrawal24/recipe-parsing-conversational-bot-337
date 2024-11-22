from url import *
from googlesearch import search
import re
import urllib.parse
import spacy
from rapidfuzz import fuzz, process

nlp = spacy.load("en_core_web_md")

def fetch_ingredient_quantity(ingredients, curr_ingredient):
    for i in ingredients:
        if curr_ingredient in i['name']:
            return i['quantity'], i['unit']

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

def get_youtube_search_url(query):
    base_url = "https://www.youtube.com/results?search_query="
    encoded_query = urllib.parse.quote(query)
    return f"{base_url}{encoded_query}"
        
def conversation():
    text = input("What recipe would you like to cook today? Please paste a recipe link from allrecipes.com here to get started.\n")
    
    ingredients, instructions = fetch_page_from_url(text)
    step = 0
    current_context = ""  # Store the current context (usually the last instruction)
    
    pattern_how = r"(?i)^how\s+(to|do)\b"
    pattern_how_much = r"(?i)how much (\w+)"
    pattern_how_much_step = r"(?i)how much (\w+) (do|is|for) (this step|step \d+)"
    pattern_ingredients_step =  r"(?i)what (ingredients|tools) do i need for (this|next|previous|\d+(?:st|nd|rd|th)?) step"
    pattern_what = r"(?i)^what\s+is\b"
    pattern_how_do_vague = r"(?i)how\s+(?:do|to)\s+(?:i|we)?\s*(?:do|make)?\s*(this|that|it)\??$"

    while text != "Done":
        text = input("\nWhat would you like to do next?\n")
        
        if text == "What are the ingredients?":
            for i in print_ingredients_list(ingredients):
                print(i)
        elif text == "What are the tools?":
            for i in extract_tools(instructions):
                print(i)
        
        elif text == "What is the next step?":
            if step >= len(instructions):
                print("That was the last step!")
            else:
                current_context = instructions[step]  # Store the current step
                print(current_context)
                step += 1
        
        elif text == "What is the previous step?":
            current_context = instructions[step-1]  # Store the previous step
            print(current_context)
            
        # elif text == "How do I do that?":
        #     if current_context:
        #         search_query = "How to: " + current_context
        #         print("Please look at the following link for reference:")
        #         print([i for i in search(search_query, stop=1)][0])
        #     else:
        #         print("I'm not sure what you're referring to. Could you be more specific?")

        elif re.match(pattern_how_do_vague, text):
            if current_context:
                youtube_url = get_youtube_search_url(f"how to {current_context}")
                print(f"Here's a video that might help: {youtube_url}")
            else:
                print("I'm not sure what you're referring to. Could you be more specific?")
            
        elif re.match(pattern_how, text):
            youtube_url = get_youtube_search_url(text)
            print(f"No worries. I found a reference for you: {youtube_url}")
            
        # Handle "How much X do I need?"
        elif re.match(pattern_how_much, text):
            match = re.match(pattern_how_much, text)
            ingredient = match.group(1).lower()
            quantity = fetch_ingredient_quantity(ingredients, ingredient)
            if quantity:
                print(f"You need {quantity} of {ingredient}.")
            else:
                print(f"I couldn't find {ingredient} in the recipe. Please check again.")
        
        # Handle "How much X do I need for this step?" or "How much X do I need for step N?"
        elif re.match(pattern_how_much_step, text):
            match = re.match(pattern_how_much_step, text)
            ingredient = match.group(1).lower()
            if "this step" in text.lower():
                step_number = step  # Use the current step
            else:
                step_match = re.search(r"step (\d+)", text, re.IGNORECASE)
                step_number = int(step_match.group(1)) if step_match else None
            
            if step_number is None or step_number < 1 or step_number > len(instructions):
                print("I couldn't understand which step you're referring to.")
            else:
                quantity = fetch_ingredient_quantity(ingredients, ingredient)
                if quantity:
                    print(f"You need {quantity} of {ingredient} for step {step_number}.")
                else:
                    print(f"No {ingredient} is needed for step {step_number}.")
        
        # Handle "what ingredients and/or tools do I need for X step"
        elif re.match(pattern_ingredients_step, text):
            match = re.match(pattern_ingredients_step, text)
            ingredient = match.group(1).lower()
            if "this step" in text.lower():
                step_number = step
            elif "next step" in text.lower():
                step_number = step+1
            elif "previous step" in text.lower():
                step_number = step-1
            else:
                step_match = re.search(r"step (\d+)", text, re.IGNORECASE)
                step_number = int(step_match.group(1)) if step_match else None
            
            if step_number is None or step_number < 1 or step_number > len(instructions):
                print("That step does not exist.")
            else:
                if "ingredients" in text.lower():
                    step_ingredients = get_step_information(instructions[step_number-1], ingredients, "ingredients")
                                
                    ingredient_quantities = {}   
                    for i in step_ingredients:
                        quantity = fetch_ingredient_quantity(ingredients, i)
                        ingredient_quantities.update({i:quantity})
                        
                    if ingredient_quantities:
                        print(f"You need the following for step {step_number}:")
                        for i in ingredient_quantities:
                            print(f"\t{ingredient_quantities[i]} of {i}")
                    else:
                        print(f"No ingredients are needed for this step.")
                if "tools" in text.lower():
                    tools = extract_tools([instructions[step_number-1]])
                        
                    if tools:
                        print(f"You need the following for step {step_number}:")
                        for i in tools:
                            print(f"\t{i}")
                    else:
                        print(f"No tools are needed for this step.")
        
        elif text != "Done":
            print("I'm sorry, I'm not smart enough to understand that!")
    
    print("I hope I was able to help with your cooking journey today. Enjoy the food!")

if __name__ == "__main__":
    print(r'Hello, My name is Gordon! I will be your personal sous chef for today. Before we get started, please note that you can type "Done" at any time to exit the conversation.')
    conversation()