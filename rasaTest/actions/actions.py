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
import time
import requests

RECIPE_CACHE = {}
SEARCH_CACHE = {}

# Action for fetching a recipe
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

        # Fetch recipe data
        try:
            ingredients, instructions = fetch_page_from_url(user_message)
        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred while fetching the recipe: {str(e)}")
            return []

        if not instructions:
            dispatcher.utter_message(text="I couldn't retrieve the instructions. Please check the URL and try again.")
            return []

        # Save recipe and reset step tracker
        RECIPE_CACHE["latest"] = {
            "url": user_message,
            "ingredients": print_ingredients_list(ingredients),
            "instructions": instructions,
            "current_step": 0,  # Start at the first step
        }

        dispatcher.utter_message(text="The recipe has been loaded. You can now ask for steps like 'next step', 'current step', or 'previous step'.")
        return []

# Action for listing ingredients
class ActionListIngredients(Action):
    def name(self) -> Text:
        return "action_list_ingredients"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        if "latest" not in RECIPE_CACHE or "ingredients" not in RECIPE_CACHE["latest"]:
            dispatcher.utter_message(text="I don't have the ingredients yet. Please provide a recipe URL first.")
            return []

        ingredients_text = "\n".join(RECIPE_CACHE["latest"]["ingredients"])
        dispatcher.utter_message(text=f"The ingredients are:\n{ingredients_text}")

        return []

# Action for listing tools
class ActionListTools(Action):
    def name(self) -> Text:
        return "action_list_tools"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        if "latest" not in RECIPE_CACHE or "instructions" not in RECIPE_CACHE["latest"]:
            dispatcher.utter_message(text="I don't have the instructions yet. Please provide a recipe URL first.")
            return []

        tools = extract_tools(RECIPE_CACHE["latest"]["instructions"])
        if tools:
            dispatcher.utter_message(text=f"The tools needed are:\n{', '.join(tools)}")
        else:
            dispatcher.utter_message(text="I couldn't find any tools in the recipe instructions.")

        return []

# Action for listing cooking methods
class ActionListCookingMethods(Action):
    def name(self) -> Text:
        return "action_list_cooking_methods"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        if "latest" not in RECIPE_CACHE or "instructions" not in RECIPE_CACHE["latest"]:
            dispatcher.utter_message(text="I don't have the instructions yet. Please provide a recipe URL first.")
            return []

        methods = extract_cooking_methods(RECIPE_CACHE["latest"]["instructions"])
        if methods:
            dispatcher.utter_message(text=f"The cooking methods are:\n{', '.join(methods)}")
        else:
            dispatcher.utter_message(text="I couldn't find any cooking methods in the recipe.")

        return []
    
class ActionPrintFullRecipe(Action):
    def name(self) -> Text:
        return "action_print_full_recipe"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        if "latest" not in RECIPE_CACHE:
            dispatcher.utter_message(text="I don't have a recipe loaded. Please provide a recipe URL first.")
            return []

        recipe = RECIPE_CACHE["latest"]
        ingredients = "\n".join(recipe["ingredients"])
        instructions = "\n".join(
            [f"Step {idx + 1}: {step}" for idx, step in enumerate(recipe["instructions"])]
        )

        full_recipe = f"Ingredients:\n{ingredients}\n\nInstructions:\n{instructions}"
        dispatcher.utter_message(text=full_recipe)

        return []

# Action for handling "how to" questions
class ActionHowTo(Action):
    def name(self) -> Text:
        return "action_how_to"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text")
        query = user_message.replace("How to", "").strip("?").strip()

        if not query:
            dispatcher.utter_message(text="Could you clarify what you need help with?")
            return []

        if query in SEARCH_CACHE:
            response = SEARCH_CACHE[query]
        else:
            youtube_query = f"https://www.youtube.com/results?search_query=How+to+{urllib.parse.quote(query)}"
            try:
                time.sleep(2)
                google_results = [result for result in search(f"How to {query}", stop=3)]
                response = f"No worries! Here's a YouTube video that might help: {youtube_query}\n"
                response += "\nHere are other resources I found:\n" + "\n".join(f"- {link}" for link in google_results)
            except Exception as e:
                response = "I'm being rate-limited by the search provider. Please wait a moment and try again." if "429" in str(e) else f"An error occurred: {str(e)}"
            SEARCH_CACHE[query] = response

        dispatcher.utter_message(text=response)
        return []

# Action for handling "what is" questions
class ActionWhatIs(Action):
    def name(self) -> Text:
        return "action_what_is"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text")
        keyword = user_message.replace("What is", "").strip("?").strip().lower()

        if not keyword:
            dispatcher.utter_message(text="Could you clarify what you're asking about?")
            return []

        if keyword in SEARCH_CACHE:
            response = SEARCH_CACHE[keyword]
        else:
            youtube_query = f"https://www.youtube.com/results?search_query=What+is+{urllib.parse.quote(keyword)}"
            try:
                time.sleep(2)
                google_results = [result for result in search(f"What is {keyword}", stop=3)]
                response = f"No worries! Here's a YouTube video that might help: {youtube_query}\n"
                response += "\nHere are other resources I found:\n" + "\n".join(f"- {link}" for link in google_results)
            except Exception as e:
                response = "I'm being rate-limited by the search provider. Please wait a moment and try again." if "429" in str(e) else f"An error occurred: {str(e)}"
            SEARCH_CACHE[keyword] = response

        dispatcher.utter_message(text=response)
        return []

# Action for showing the current step
class ActionCurrentStep(Action):
    def name(self) -> Text:
        return "action_current_step"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if "latest" not in RECIPE_CACHE:
            dispatcher.utter_message(text="I don't have a recipe loaded. Please provide a recipe URL first.")
            return []

        recipe = RECIPE_CACHE["latest"]
        current_step = recipe["current_step"]
        instructions = recipe["instructions"]

        if current_step < len(instructions):
            dispatcher.utter_message(text=f"Step {current_step + 1}: {instructions[current_step]}")
        else:
            dispatcher.utter_message(text="You are at the end of the recipe. There are no more steps.")

        return []

# Action for showing the next step
class ActionNextStep(Action):
    def name(self) -> Text:
        return "action_next_step"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if "latest" not in RECIPE_CACHE:
            dispatcher.utter_message(text="I don't have a recipe loaded. Please provide a recipe URL first.")
            return []

        recipe = RECIPE_CACHE["latest"]
        current_step = recipe["current_step"]
        instructions = recipe["instructions"]

        if current_step + 1 < len(instructions):
            current_step += 1
            recipe["current_step"] = current_step
            dispatcher.utter_message(text=f"Step {current_step + 1}: {instructions[current_step]}")
        else:
            dispatcher.utter_message(text="You are at the last step of the recipe.")

        return []

# Action for showing the previous step
class ActionPreviousStep(Action):
    def name(self) -> Text:
        return "action_previous_step"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if "latest" not in RECIPE_CACHE:
            dispatcher.utter_message(text="I don't have a recipe loaded. Please provide a recipe URL first.")
            return []

        recipe = RECIPE_CACHE["latest"]
        current_step = recipe["current_step"]
        instructions = recipe["instructions"]

        if current_step > 0:
            current_step -= 1
            recipe["current_step"] = current_step
            dispatcher.utter_message(text=f"Step {current_step + 1}: {instructions[current_step]}")
        else:
            dispatcher.utter_message(text="You are already at the first step of the recipe.")

        return []
    
def get_step_index(step_type: str, current_step: int, total_steps: int) -> int:
    if step_type == "current":
        return current_step
    elif step_type == "next":
        return current_step + 1 if current_step + 1 < total_steps else current_step
    elif step_type == "previous":
        return current_step - 1 if current_step > 0 else current_step
    return current_step

# # Action for tools at a specific step
# class ActionToolsAtStep(Action):
#     def name(self) -> Text:
#         return "action_tools_at_step"

#     def run(
#         self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
#     ) -> List[Dict[Text, Any]]:
#         step_type = tracker.get_slot("step_type")
#         if "latest" not in RECIPE_CACHE:
#             dispatcher.utter_message(text="I don't have a recipe loaded. Please provide a recipe URL first.")
#             return []

#         recipe = RECIPE_CACHE["latest"]
#         current_step = recipe["current_step"]
#         total_steps = len(recipe["instructions"])
#         step_index = get_step_index(step_type, current_step, total_steps)

#         tools = extract_tools([recipe["instructions"][step_index]])
#         if tools:
#             dispatcher.utter_message(text=f"Tools for {step_type} step:\n{', '.join(tools)}")
#         else:
#             dispatcher.utter_message(text=f"No tools are required for the {step_type} step.")
#         return []

# # Action for methods at a specific step
# class ActionMethodsAtStep(Action):
#     def name(self) -> Text:
#         return "action_methods_at_step"

#     def run(
#         self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
#     ) -> List[Dict[Text, Any]]:
#         step_type = tracker.get_slot("step_type")
#         if "latest" not in RECIPE_CACHE:
#             dispatcher.utter_message(text="I don't have a recipe loaded. Please provide a recipe URL first.")
#             return []

#         recipe = RECIPE_CACHE["latest"]
#         current_step = recipe["current_step"]
#         total_steps = len(recipe["instructions"])
#         step_index = get_step_index(step_type, current_step, total_steps)

#         methods = extract_cooking_methods([recipe["instructions"][step_index]])
#         if methods:
#             dispatcher.utter_message(text=f"Methods for {step_type} step:\n{', '.join(methods)}")
#         else:
#             dispatcher.utter_message(text=f"No methods are mentioned for the {step_type} step.")
#         return []

# # Action for ingredients at a specific step
# class ActionIngredientsAtStep(Action):
#     def name(self) -> Text:
#         return "action_ingredients_at_step"

#     def run(
#         self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
#     ) -> List[Dict[Text, Any]]:
#         step_type = tracker.get_slot("step_type")
#         if "latest" not in RECIPE_CACHE:
#             dispatcher.utter_message(text="I don't have a recipe loaded. Please provide a recipe URL first.")
#             return []

#         recipe = RECIPE_CACHE["latest"]
#         current_step = recipe["current_step"]
#         total_steps = len(recipe["instructions"])
#         step_index = get_step_index(step_type, current_step, total_steps)

#         step_text = recipe["instructions"][step_index]
#         ingredients = extract_tools([step_text])  # Replace this with the actual ingredient extraction logic
#         if ingredients:
#             dispatcher.utter_message(text=f"Ingredients for {step_type} step:\n{', '.join(ingredients)}")
#         else:
#             dispatcher.utter_message(text=f"No ingredients are mentioned for the {step_type} step.")
#         return []

class ActionIngredientsAtStep(Action):
    def name(self) -> Text:
        return "action_ingredients_at_step"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        step_type = tracker.get_slot("step_type")
        if "latest" not in RECIPE_CACHE:
            dispatcher.utter_message(text="I don't have a recipe loaded. Please provide a recipe URL first.")
            return []

        recipe = RECIPE_CACHE["latest"]
        current_step = recipe["current_step"]
        total_steps = len(recipe["instructions"])
        step_index = get_step_index(step_type, current_step, total_steps)

        step_text = recipe["instructions"][step_index]
        # Example logic for extracting ingredients from a step's text
        ingredients = [
            ingredient for ingredient in recipe["ingredients"] if ingredient.lower() in step_text.lower()
        ]

        if ingredients:
            dispatcher.utter_message(
                text=f"Ingredients:\n{', '.join(ingredients)}"
            )
        else:
            dispatcher.utter_message(text=f"No ingredients are mentioned for this step.")
        return []

class ActionToolsAtStep(Action):
    def name(self) -> Text:
        return "action_tools_at_step"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        step_type = tracker.get_slot("step_type")
        if "latest" not in RECIPE_CACHE:
            dispatcher.utter_message(text="I don't have a recipe loaded. Please provide a recipe URL first.")
            return []

        recipe = RECIPE_CACHE["latest"]
        current_step = recipe["current_step"]
        total_steps = len(recipe["instructions"])
        step_index = get_step_index(step_type, current_step, total_steps)

        tools = extract_tools([recipe["instructions"][step_index]])

        if tools:
            dispatcher.utter_message(
                text=f"Tools:\n{', '.join(tools)}"
            )
        else:
            dispatcher.utter_message(text=f"No tools are required for the step.")
        return []

class ActionMethodsAtStep(Action):
    def name(self) -> Text:
        return "action_methods_at_step"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        step_type = tracker.get_slot("step_type")
        if "latest" not in RECIPE_CACHE:
            dispatcher.utter_message(text="I don't have a recipe loaded. Please provide a recipe URL first.")
            return []

        recipe = RECIPE_CACHE["latest"]
        current_step = recipe["current_step"]
        total_steps = len(recipe["instructions"])
        step_index = get_step_index(step_type, current_step, total_steps)

        methods = extract_cooking_methods([recipe["instructions"][step_index]])

        if methods:
            dispatcher.utter_message(
                text=f"Methods:\n{', '.join(methods)}"
            )
        else:
            dispatcher.utter_message(text=f"No methods are mentioned for the step.")
        return []
