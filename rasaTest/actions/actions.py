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

