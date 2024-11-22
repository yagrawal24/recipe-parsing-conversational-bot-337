# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

from typing import Dict, Text, Any, List
from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher
from googlesearch import search
import urllib.parse
from .url import fetch_page_from_url, print_ingredients_list, extract_tools, extract_cooking_methods

# Global dictionary to store recipe data
RECIPE_CACHE = {}

class ActionFetchRecipe(Action):
    def name(self) -> Text:
        return "action_fetch_recipe"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text")

        # Validate the URL
        if "https://www.allrecipes.com/" not in user_message:
            dispatcher.utter_message(text="That doesn't look like a valid AllRecipes.com URL. Please try again.")
            return []

        # Fetch recipe data using url.py
        try:
            ingredients, instructions = fetch_page_from_url(user_message)
        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred while fetching the recipe: {str(e)}")
            return []

        # Validate fetched data
        if not ingredients or not instructions:
            dispatcher.utter_message(text="I couldn't retrieve the recipe. Please check the URL and try again.")
            return []

        # Save to global cache
        RECIPE_CACHE["latest"] = {
            "url": user_message,
            "ingredients": print_ingredients_list(ingredients),
            "instructions": instructions,
        }

        # Format the ingredients and instructions
        formatted_ingredients = RECIPE_CACHE["latest"]["ingredients"]
        ingredients_text = "\n".join(formatted_ingredients)
        instructions_text = " ".join(RECIPE_CACHE["latest"]["instructions"])

        # Respond to the user
        dispatcher.utter_message(text="Here is the recipe:")
        dispatcher.utter_message(text=f"Ingredients:\n{ingredients_text}")
        dispatcher.utter_message(text=f"Instructions:\n{instructions_text}")

        return []


class ActionListIngredients(Action):
    def name(self) -> Text:
        return "action_list_ingredients"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Check if there is a cached recipe
        if "latest" not in RECIPE_CACHE or "ingredients" not in RECIPE_CACHE["latest"]:
            dispatcher.utter_message(text="I don't have the ingredients yet. Please provide a recipe URL first.")
            return []

        # Retrieve and respond with the cached ingredients
        formatted_ingredients = RECIPE_CACHE["latest"]["ingredients"]
        ingredients_text = "\n".join(formatted_ingredients)
        dispatcher.utter_message(text=f"The ingredients are:\n{ingredients_text}")

        return []


class ActionListTools(Action):
    def name(self) -> Text:
        return "action_list_tools"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Check if there is a cached recipe
        if "latest" not in RECIPE_CACHE or "instructions" not in RECIPE_CACHE["latest"]:
            dispatcher.utter_message(text="I don't have the instructions yet. Please provide a recipe URL first.")
            return []

        # Retrieve instructions and extract tools
        instructions = RECIPE_CACHE["latest"]["instructions"]
        tools = extract_tools(instructions)

        if not tools:
            dispatcher.utter_message(text="I couldn't find any tools in the recipe instructions.")
        else:
            tools_text = ", ".join(tools)
            dispatcher.utter_message(text=f"The tools needed are:\n{tools_text}")

        return []
    
class ActionListCookingMethods(Action):
    def name(self) -> Text:
        return "action_list_cooking_methods"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Check if there is a cached recipe
        if "latest" not in RECIPE_CACHE or "instructions" not in RECIPE_CACHE["latest"]:
            dispatcher.utter_message(text="I don't have the instructions yet. Please provide a recipe URL first.")
            return []

        # Retrieve instructions and extract cooking methods
        instructions = RECIPE_CACHE["latest"]["instructions"]
        methods = extract_cooking_methods(instructions)

        if not methods:
            dispatcher.utter_message(text="I couldn't find any cooking methods in the recipe.")
        else:
            methods_text = ", ".join(methods)
            dispatcher.utter_message(text=f"The cooking methods are:\n{methods_text}")

        return []
    
class ActionHowTo(Action):
    def name(self) -> Text:
        return "action_how_to"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text")

        # Extract query from the user's message
        query = user_message.replace("How to", "").strip("?").strip()
        if not query:
            dispatcher.utter_message(text="Could you clarify what you need help with?")
            return []

        # Search for YouTube and Google resources
        youtube_query = f"https://www.youtube.com/results?search_query=How+to+{urllib.parse.quote(query)}"
        try:
            google_results = [result for result in search(f"How to {query}", stop=3)]
        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred while searching: {str(e)}")
            return []

        # Construct the response
        response = f"No worries! Here's a YouTube video that might help: {youtube_query}\n"
        if google_results:
            response += "\nHere are other resources I found:\n"
            for link in google_results:
                response += f"- {link}\n"

        dispatcher.utter_message(text=response)
        return []


class ActionWhatIs(Action):
    def name(self) -> Text:
        return "action_what_is"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text")

        # Extract keyword from the user's message
        keyword = user_message.replace("What is", "").strip("?").strip().lower()
        if not keyword:
            dispatcher.utter_message(text="Could you clarify what you're asking about?")
            return []

        # Check if the keyword matches an ingredient in the cached recipe
        if "latest" in RECIPE_CACHE and "ingredients" in RECIPE_CACHE["latest"]:
            ingredients = RECIPE_CACHE["latest"]["ingredients"]
            for ingredient in ingredients:
                if keyword in ingredient.lower():
                    dispatcher.utter_message(text=f"{keyword.capitalize()} is one of the ingredients in the recipe.")
                    return []

        # Search for YouTube and Google resources
        youtube_query = f"https://www.youtube.com/results?search_query=What+is+{urllib.parse.quote(keyword)}"
        try:
            google_results = [result for result in search(f"What is {keyword}", stop=3)]
        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred while searching: {str(e)}")
            return []

        # Construct the response
        response = f"No worries! Here's a YouTube video that might help: {youtube_query}\n"
        if google_results:
            response += "\nHere are other resources I found:\n"
            for link in google_results:
                response += f"- {link}\n"

        dispatcher.utter_message(text=response)
        return []