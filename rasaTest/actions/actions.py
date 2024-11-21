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

class ActionFetchRecipe(Action):
    def name(self) -> Text:
        return "action_fetch_recipe"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text")

        # Validate the URL
        if not user_message or "https://www.allrecipes.com/" not in user_message:
            dispatcher.utter_message(response="utter_invalid_url")
            return []

        # Fetch recipe data using the helper function
        try:
            ingredients, instructions = fetch_page_from_url(user_message)
        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred: {str(e)}")
            return []

        # Handle missing or malformed recipe data
        if not ingredients or not instructions:
            dispatcher.utter_message(
                text="I couldn't retrieve the recipe. Please check the URL and try again."
            )
            return []

        # Format and send the response to the user
        dispatcher.utter_message(text="Here is the recipe:")
        dispatcher.utter_message(
            text=f"Ingredients:\n{', '.join(print_ingredients_list(ingredients))}"
        )
        dispatcher.utter_message(text=f"Instructions:\n{' '.join(instructions)}")

        return []
