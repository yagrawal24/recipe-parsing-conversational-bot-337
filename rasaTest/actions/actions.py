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

from typing import Dict, Text, Any, List, Union

from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from .url import fetch_page_from_url, extract_tools, print_ingredients_list
import re

# class ActionFetchRecipe(Action):
#     def name(self) -> Text:
#         return "action_fetch_recipe"

#     def run(
#         self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
#     ) -> List[Dict[Text, Any]]:
#         user_message = tracker.latest_message.get("text")

#         # Validate the URL
#         if not user_message or "https://www.allrecipes.com/" not in user_message:
#             dispatcher.utter_message(response="utter_invalid_url")
#             return []

#         # Fetch recipe data using the helper function
#         try:
#             ingredients, instructions = fetch_page_from_url(user_message)
#         except Exception as e:
#             dispatcher.utter_message(text=f"An error occurred: {str(e)}")
#             return []

#         # Handle missing or malformed recipe data
#         if not ingredients or not instructions:
#             dispatcher.utter_message(
#                 text="I couldn't retrieve the recipe. Please check the URL and try again."
#             )
#             return []

#         # Format ingredients for the slot
#         formatted_ingredients = "\n".join(print_ingredients_list(ingredients))

#         # Respond with the recipe
#         dispatcher.utter_message(text="Here is the recipe:")
#         dispatcher.utter_message(text=f"Ingredients:\n{formatted_ingredients}")
#         dispatcher.utter_message(text=f"Instructions:\n{' '.join(instructions)}")

#         # Store ingredients in the slot
#         return [SlotSet("ingredients", formatted_ingredients)]


# class ActionListIngredients(Action):
#     def name(self) -> Text:
#         return "action_list_ingredients"

#     def run(
#         self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
#     ) -> List[Dict[Text, Any]]:
#         # Retrieve the ingredients slot
#         ingredients = tracker.get_slot("ingredients")

#         if not ingredients:
#             dispatcher.utter_message(response="utter_no_ingredients")
#         else:
#             # Directly use the formatted ingredients
#             dispatcher.utter_message(text=f"The ingredients are:\n{ingredients}")

#         return []

class ActionFetchRecipeAndIngredients(Action):
    def name(self) -> Text:
        return "action_fetch_recipe_and_ingredients"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text")

        # Check if the user provided a recipe URL
        if "https://www.allrecipes.com/" in user_message:
            try:
                ingredients, instructions = fetch_page_from_url(user_message)
            except Exception as e:
                dispatcher.utter_message(text=f"An error occurred while fetching the recipe: {str(e)}")
                return []

            # Validate fetched data
            if not ingredients or not instructions:
                dispatcher.utter_message(text="I couldn't retrieve the recipe. Please check the URL and try again.")
                return []

            # Format ingredients for output
            formatted_ingredients = "\n".join(f"- {ingredient}" for ingredient in ingredients)

            # Send recipe details
            dispatcher.utter_message(text="Here is the recipe:")
            dispatcher.utter_message(text=f"Ingredients:\n{formatted_ingredients}")
            dispatcher.utter_message(text=f"Instructions:\n{' '.join(instructions)}")

            # Save ingredients to the slot
            return [SlotSet("ingredients", formatted_ingredients)]

        # Handle direct queries for ingredients
        elif tracker.get_intent_of_latest_message() == "ask_ingredients":
            ingredients = tracker.get_slot("ingredients")
            if not ingredients:
                dispatcher.utter_message(text="I don't have any ingredients yet. Please provide a recipe URL first.")
            else:
                dispatcher.utter_message(text=f"The ingredients are:\n{ingredients}")
            return []

        dispatcher.utter_message(text="Please provide a recipe URL to get started.")
        return []
