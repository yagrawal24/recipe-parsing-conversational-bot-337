# Vegetarian Transformations
to_vegetarian = {
    "chicken": ["tofu", "seitan"],
    "beef": ["tempeh", "jackfruit"],
    "pork": ["jackfruit", "seitan"],
    "ground": ["textured vegetable protein (TVP)", "soy crumbles"],
    "bacon": ["tempeh bacon", "coconut bacon"],
    "sausage": ["vegetarian sausages", "seitan sausages"],
    "fish": ["tofu", "seaweed-marinated tofu"],
    "shrimp": ["king oyster mushrooms", "tofu"],
    "egg": ["tofu scramble", "vegan egg replacer"],
    "chicken broth": ["vegetable broth", "mushroom broth"],
    "fish sauce": ["soy sauce", "seaweed broth"]
}

from_vegetarian = {
    "tofu": ["chicken", "fish"],
    "seitan": ["chicken", "pork"],
    "tempeh": ["beef", "ground meat"],
    "jackfruit": ["pork", "beef"],
    "mushrooms": ["chicken", "seafood"],
    "lentils": ["ground meat", "beef"],
    "vegetable broth": ["chicken broth", "beef broth"],
    "soy crumbles": ["ground beef", "ground chicken"],
    "textured vegetable protein": ["ground beef", "ground chicken"],
}

# Health Transformations
to_healthy = {
    "butter": ["olive oil", "avocado oil"],
    "oil": ["cooking spray", "olive oil"],
    "cream": ["greek yogurt", "coconut milk"],
    "sugar": ["stevia", "monk fruit sweetener"],
    "white rice": ["brown rice", "quinoa"],
    "pasta": ["whole grain pasta", "zucchini noodles"],
    "bread": ["whole grain bread", "lettuce wrap"],
    "mayo": ["mashed avocado", "hummus"],
    "salt": ["herbs", "spices"],
    "bacon": ["turkey bacon", "canadian bacon"]
}

from_healthy = {
    "quinoa": ["white rice", "pasta"],
    "brown rice": ["white rice", "pasta"],
    "turkey bacon": ["bacon", "pork belly"],
    "cooking spray": ["oil", "butter"],
    "stevia": ["sugar", "honey"],
    "greek yogurt": ["cream", "sour cream"]
}

# Cuisine Styles (base ingredients for transformation)
chinese_style = {
    "core_ingredients": ["soy sauce", "ginger", "garlic", "sesame oil", "rice vinegar"],
    "spices": ["five spice", "white pepper"],
    "cooking_methods": ["stir fry", "steam", "braise"],
    "replacements": {
        "olive oil": "sesame oil",
        "vinegar": "rice vinegar",
        "pasta": "noodles",
        "herbs": "green onions"
    }
}

mexican_style = {
    "core_ingredients": ["lime", "cilantro", "jalapeno", "tomatoes", "onions"],
    "spices": ["cumin", "chili powder", "oregano"],
    "cooking_methods": ["grill", "fry", "simmer"],
    "replacements": {
        "rice": "mexican rice",
        "cheese": "queso fresco",
        "cream": "mexican crema"
    }
}

italian_style = {
    "core_ingredients": ["olive oil", "garlic", "basil", "tomatoes", "parmesan"],
    "spices": ["oregano", "red pepper flakes", "rosemary"],
    "cooking_methods": ["saute", "simmer", "bake"],
    "replacements": {
        "vinegar": "balsamic vinegar",
        "oil": "olive oil",
        "cheese": "parmesan"
    }
}

cooking_method_transforms = {
    "bake": ["fry", "grill", "air fry"],
    "fry": ["bake", "grill", "air fry"],
    "grill": ["bake", "pan sear", "broil"],
    "steam": ["boil", "microwave", "pressure cook"],
    "saute": ["stir fry", "grill", "bake"],
    "roast": ["air fry", "grill", "pan sear"],
    "broil": ["grill", "bake", "pan sear"]
}

gluten_free = {
    "flour": ["almond flour", "rice flour", "cornstarch"],
    "pasta": ["rice noodles", "gluten-free pasta"],
    "bread": ["gluten-free bread", "corn tortilla"],
    "soy sauce": ["tamari", "coconut aminos"],
    "breadcrumbs": ["gluten-free breadcrumbs", "crushed corn flakes"]
}

lactose_free = {
    "milk": ["almond milk", "oat milk", "soy milk"],
    "cheese": ["dairy-free cheese"],
    "butter": ["dairy-free butter", "oil"],
    "cream": ["coconut cream", "cashew cream"],
    "yogurt": ["coconut yogurt", "soy yogurt"]
}