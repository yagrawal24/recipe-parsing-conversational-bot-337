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
    step = -1
    current_context = ""  # Store the current context (usually the last instruction)
    
    pattern_step = r"What is the (current|next|previous|\d+(?:st|nd|rd|th)?) step"
    pattern_how = r"(?i)^how\s+(to|do)\b"
    pattern_how_much = r"(?i)how\s+(much|many) (\w+)"
    pattern_ingredients_step =  r"(?i)what (ingredients|tools) do i need for the (current|next|previous|\d+(?:st|nd|rd|th)?) step"
    pattern_what = r"(?i)^what\s+is\b"
    pattern_how_do_vague = r"(?i)how\s+(?:do|to)\s+(?:i|we)?\s*(?:do|make)?\s*(this|that|it)\??$"

    while text != "Done":
        text = input("\nWhat would you like to do next?\n")
        
        # Basic Requests
        if text == "What step is this?":
            if step+1 == 0:
                print("The recipe has not started yet")
            else:
                print("This is step ", step+1)
        elif text == "What are the ingredients?":
            for i in print_ingredients_list(ingredients):
                print(i)
        elif text == "What are the tools?":
            for i in extract_tools(instructions):
                print(i)
        elif text == "What cooking methods are used?":
            for i in extract_cooking_methods(instructions):
                print(i)
        
        #
        # Recipe Navigation
        #
        elif re.match(pattern_step, text):
            match = re.match(pattern_step, text)
            curr_step = match.group(1)  
            if curr_step == "current" and step > -1:
                if step > -1:
                    print(current_context)
                else:
                    print("We have not started the recipe yet!")
                    
            elif curr_step == "next":
                if step >= len(instructions):
                    print("That was the last step!")
                else:
                    step += 1
                    current_context = instructions[step]
                    print(current_context)
                    
            elif curr_step == "previous":
                if step <= 0:
                    print("There is no previous step!")
                else:
                    step -= 1
                    current_context = instructions[step]
                    print(current_context)
                    
            # nth step
            elif curr_step.endswith(("st", "nd", "rd", "th")):
                step_number = int(re.search(r"\d+", step).group())
                current_context = instructions[step_number-1] # include -1 for accurate index (i.e. step 1 is index 0)
                print(current_context)
                
                jump = input("\nWould you like to skip to this step?")
                if jump.lower() == "yes":
                    step = step_number - 1
            
            else:
                print("That step does not exist!")
                
        #
        # How-To
        #
        
        # Vague
        elif re.match(pattern_how_do_vague, text):
            if current_context:
                youtube_url = get_youtube_search_url(f"how to {current_context}")
                print(f"Here's a video that might help: {youtube_url}")
            else:
                print("I'm not sure what you're referring to. Could you be more specific?")
            
        # Specific
        elif re.match(pattern_how, text):
            youtube_url = get_youtube_search_url(text)
            print(f"No worries. I found a reference for you: {youtube_url}")
            
        #
        # In-step questions
        #
        
        # Handle "How much X do I need"
        elif re.match(pattern_how_much, text):
            match = re.match(pattern_how_much, text)
            ingredient = match.group(2).lower()
            quantity = fetch_ingredient_quantity(ingredients, ingredient)
            if quantity:
                # print(f"You need {quantity} of {ingredient}.")
                print(f"\t{quantity[0]} {'' if quantity[1] == None else quantity[1] + ' of'} {ingredient}")
            else:
                print(f"I couldn't find {ingredient} in the recipe. Please check again.")
        
        # Handle "what ingredients and/or tools do I need for X step"
        elif re.match(pattern_ingredients_step, text):
            match = re.match(pattern_ingredients_step, text)
            ingredient = match.group(1).lower()
            if "current" in text.lower():
                step_number = step
            elif "next" in text.lower():
                step_number = step+1
            elif "previous" in text.lower():
                step_number = step-1
            else:
                step_match = re.search(r"step (\d+)", text, re.IGNORECASE)
                step_number = int(step_match.group(1)) if step_match else None
            
            if step_number is None or step_number < 0 or step_number > len(instructions):
                print("That step does not exist.")
            else:
                if "ingredients" in text.lower():
                    step_ingredients = get_step_information(instructions[step_number], ingredients, "ingredients")
                                
                    ingredient_quantities = {}   
                    for i in step_ingredients:
                        quantity = fetch_ingredient_quantity(ingredients, i)
                        ingredient_quantities.update({i:quantity})
                        
                    if ingredient_quantities:
                        print(f"You need the following for step {step_number}:")
                        for i in ingredient_quantities:
                            print(f"\t{ingredient_quantities[i][0]} {'' if ingredient_quantities[i][1] == None else ingredient_quantities[i][1] + ' of'} {i}")
                    else:
                        print(f"No ingredients are needed for this step.")
                if "tools" in text.lower():
                    tools = extract_tools([instructions[step_number]])
                        
                    if tools:
                        print(f"You need the following for step {step_number}:")
                        for i in tools:
                            print(f"\t{i}")
                    else:
                        print(f"No tools are needed for this step.")
        
        # How long
        
        # What temperature
        
        elif text != "Done":
            print("I'm sorry, I'm not smart enough to understand that!")
    
    print("I hope I was able to help with your cooking journey today. Enjoy the food!")

if __name__ == "__main__":
    print(r'Hello, My name is Gordon! I will be your personal sous chef for today. Before we get started, please note that you can type "Done" at any time to exit the conversation.')
    conversation()