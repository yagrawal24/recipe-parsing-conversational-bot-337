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
from .url import fetch_page_from_url, print_ingredients_list, extract_tools

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

class ActionWhatIs(Action):
    def name(self) -> Text:
        return "action_what_is"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text")

        # Extract the keyword
        keyword = user_message.replace("What is ", "").strip("?").lower()

        if not keyword:
            dispatcher.utter_message(text="I didn't understand what you're asking about. Could you clarify?")
            return []

        # Check cached ingredients
        if "latest" in RECIPE_CACHE and "ingredients" in RECIPE_CACHE["latest"]:
            ingredients = RECIPE_CACHE["latest"]["ingredients"]
            for ingredient in ingredients:
                if keyword in ingredient.lower():
                    dispatcher.utter_message(text=f"{keyword.capitalize()} is one of the ingredients in the recipe.")
                    return []

        # Perform a Google search if the term is not found in the recipe
        try:
            search_results = [
                result for result in search(f"What is {keyword}?", stop=1)
            ]
            if search_results:
                dispatcher.utter_message(text=f"I couldn't find {keyword} in the recipe. Here's a resource that might help: {search_results[0]}")
            else:
                dispatcher.utter_message(text=f"Sorry, I couldn't find any information on {keyword}.")
        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred while searching: {str(e)}")

        return []


class ActionHowTo(Action):
    def name(self) -> Text:
        return "action_how_to"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text")

        # Extract the query
        query = user_message.replace("How to ", "").strip("?").lower()

        # Generate a YouTube search link
        base_url = "https://www.youtube.com/results?search_query="
        encoded_query = urllib.parse.quote(f"How to {query}")
        final_url = f"{base_url}{encoded_query}"

        dispatcher.utter_message(text=f"No worries! Here's a resource that might help: {final_url}")
        return []