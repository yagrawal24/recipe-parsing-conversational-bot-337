from url import *
from googlesearch import search

def fetch_ingredient_quantity(ingredients, ingredient):
    for i in ingredients:
        if ingredient in i['name']:
            return i['quantity'], i['unit']
        
def conversation():
    text = input("What recipe would you like to cook today? Please paste a recipe link from allrecipes.com here to get started.\n")
    
    ingredients, instructions = fetch_page_from_url(text)
    step = 0

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
            # Need to create a better query somehow
            print("Please look at the following link for reference:")
            print([i for i in search("How to:" + instructions[step-1], stop=1)][0])
            
        # How much X do I need?
        
        # How many X do I need?
        
        else:
            print("I'm sorry, I'm not smart enough to understand that!")
    
    print("I hope I was able to help with your cooking journey today. Enjoy the food!")

if __name__ == "__main__":
    print(r'Hello, My name is Gordon! I will be your personal sous chef for today. Before we get started, please note that you can type "Done" at any time to exit the conversation.')
    conversation()