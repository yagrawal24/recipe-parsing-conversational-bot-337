# Vegetarian Transformations
to_vegetarian = {
    "chicken": ["tofu", "seitan"],
    "beef": ["tempeh", "jackfruit"],
    "steak": ["tempeh", "jackfruit"],
    "pork": ["jackfruit", "seitan"],
    "ground": ["textured vegetable protein (TVP)", "soy crumbles"],
    "bacon": ["tempeh bacon", "coconut bacon"],
    "sausage": ["vegetarian sausages", "seitan sausages"],
    "fish": ["tofu", "seaweed-marinated tofu"],
    "salmon": ["tofu", "seaweed-marinated tofu"],
    "cod": ["tofu", "seaweed-marinated tofu"],
    "tuna": ["tofu", "seaweed-marinated tofu"],
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
    "mayo": ["avocado", "hummus"],
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
# chinese_style = {
#     "core_ingredients": ["soy sauce", "ginger", "garlic", "sesame oil", "rice vinegar"],
#     "spices": ["five spice", "white pepper"],
#     "cooking_methods": ["stir fry", "steam", "braise"],
#     "replacements": {
#         "olive oil": "sesame oil",
#         "vinegar": "rice vinegar",
#         "pasta": "noodles",
#         "herbs": "green onions"
#     }
# }

chinese_style = {
    'ingredients': {
        "butter": ["sesame oil", "peanut oil"],
        "olive oil": ["sesame oil", "peanut oil"],
        "corn oil": ["sesame oil", "peanut oil"],
        "vegetable oil": ["peanut oil"],
        "bread": ["bao buns", "scallion pancakes"],
        "rice": ["jasmine rice", "sticky rice"],
        "noodles": ["lo mein", "rice noodles"],
        "pasta": ["lo mein", "glass noodles"],
        "dumplings": ["potstickers", "dim sum dumplings"],
        "potatoes": ["taro", "lotus root"],
        "tofu": ["silken tofu", "fermented tofu"],
        "paneer": ["silken tofu"],
        "cream": ["coconut milk"],
        "sour cream": ["coconut cream"],
        "yogurt": ["soy milk", "coconut yogurt"],
        "lemon juice": ["lime juice"],
        "vinegar": ["rice vinegar", "black vinegar"],
        "balsamic vinegar": ["black vinegar"],
        "soy sauce": ["dark soy sauce", "light soy sauce"],
        "fish sauce": ["oyster sauce", "hoisin sauce"],
        "bell peppers": ["bok choy", "baby corn"],
        "jalapeños": ["Sichuan peppercorns", "red chili"],
        "okra": ["snow peas", "water chestnuts"],
        "bok choy": ["napa cabbage"],
        "cilantro": ["scallions"],
        "parsley": ["scallions"],
        "mint": ["Thai basil"],
        "pickled vegetables": ["pickled mustard greens"],
        "tortilla chips": ["fried wonton strips"],
        "chutney": ["plum sauce", "sweet chili sauce"],
        "cumin": ["five spice powder"],
        "garam masala": ["five spice powder"],
        "paprika": ["Sichuan chili flakes"],
        "chili powder": ["Sichuan chili flakes", "ground chili"],
        "red pepper flakes": ["Sichuan chili flakes"],
        "salt": ["soy sauce"],
        "lemon zest": ["lime zest"],
        "bay leaves": ["star anise"],
    },
    'techniques': {
        "stir-fry": ["wok toss"],
        "steam": ["double boil"],
        "deep fry": ["light fry"],
        "bake": ["steam bake"],
        "grill": ["char over flame"],
    }
}

mexican_style = {
    'ingredients': {
        "butter": ["lard"],
        "ghee": ["lard"],
        "olive oil": ["corn oil"],
        "sesame oil": ["corn oil"],
        "vegetable oil": ["corn oil"],
        "bread": ["corn tortilla"],
        "rice": ["Mexican rice"],
        "noodles": ["fideo (Mexican vermicelli)"],
        "couscous": ["Mexican rice"],
        "polenta": ["refried beans", "masa harina (corn dough)"],
        "flatbread": ["corn tortilla"],
        "dumplings": ["tamales"],
        "wraps": ["flour tortilla"],
        "potatoes": ["sweet potatoes", "yucca"],
        "tofu": ["seared panela cheese", "beans"],
        "paneer": ["queso fresco"],
        "ground meat": ["chorizo"],
        "chicken": ["shredded chicken"],
        "fish": ["fried fish"],
        "cheddar": ["cotija"],
        "parmesan": ["cotija", "queso añejo"],
        "feta": ["queso fresco"],
        "mozzarella": ["oaxaca cheese"],
        "cream": ["Mexican crema"],
        "sour cream": ["Mexican crema"],
        "yogurt": ["Mexican crema", "a light lime dressing"],
        "lemon juice": ["lime juice"],
        "vinegar": ["lime juice", "white vinegar"],
        "balsamic vinegar": ["lime juice"],
        "soy sauce": ["Maggi sauce"],
        "fish sauce": ["Worcestershire sauce", "anchovy paste"],
        "bell peppers": ["poblano peppers"],
        "jalapeños": ["jalapeños", "serrano peppers"],
        "okra": ["nopales (cactus paddles)"],
        "bok choy": ["Swiss chard with lime"],
        "scallions": ["green onions", "white onions"],
        "spinach": ["Swiss chard"],
        "cilantro": ["cilantro"],
        "mint": ["cilantro"],
        "pickled vegetables": ["escabeche (pickled jalapeños and carrots)"],
        "chutney": ["salsa", "guacamole"],
        "tortilla chips": ["totopos (fried tortilla chips)"],
        "croutons": ["fried tortilla strips"],
        "herbes de provence": ["cumin"],
        "italian seasoning": ["cumin"],
        "thyme": ["oregano"],
        "rosemary": ["oregano"],
        "basil": ["cilantro"],
        "parsley": ["cilantro"],
        "dill": ["epazote"],
        "sage": ["epazote"],
        "oregano": ["Mexican oregano"],
        "garam masala": ["cumin"],
        "cayenne pepper": ["chipotle powder"],
        "paprika": ["ancho chili powder", "smoked paprika"],
        "chili powder": ["guajillo chili powder", "chipotle powder"],
        "red pepper flakes": ["crushed dried arbol chiles"],
        "ground chili": ["ground guajillo chili"],
        "salt": ["Tajín"],
        "Worcestershire sauce": ["Salsa Inglesa"],
        "lemon zest": ["lime zest"],
        "bay leaves": ["Mexican bay leaves"],
    },
    'techniques': {
        "stir-fry": ["cook in a comal"]
    }
}

italian_style = {
    'ingredients': {
        "butter": ["olive oil"],
        "lard": ["olive oil"],
        "ghee": ["olive oil"],
        "corn oil": ["olive oil"],
        "sesame oil": ["olive oil"],
        "bread": ["ciabatta", "focaccia"],
        "rice": ["risotto", "arborio rice"],
        "tortilla": ["ciabatta", "focaccia"],
        "polenta": ["risotto", "gnocchi"],
        "dumplings": ["ravioli"],
        "tofu": ["ricotta", "mozzarella"],
        "paneer": ["ricotta"],
        "cheddar": ["parmesan"],
        "feta": ["ricotta", "mascarpone"],
        "cream": ["heavy cream"],
        "sour cream": ["mascarpone"],
        "yogurt": ["mascarpone", "ricotta"],
        "lime juice": ["lemon juice"],
        "soy sauce": ["balsamic vinegar", "Worcestershire sauce"],
        "fish sauce": ["anchovy paste"],
        "vinegar": ["red wine vinegar", "balsamic vinegar"],
        "miso paste": ["parmesan"],
        "tamarind": ["balsamic vinegar"],
        "jalapeños": ["roasted red peppers"],
        "bell peppers": ["roasted red peppers"],
        "okra": ["zucchini", "eggplant"],
        "bitter melon": ["radicchio"],
        "bok choy": ["Swiss chard"],
        "cilantro": ["parsley"],
        "scallions": ["leeks", "shallots"],
        "tortilla chips": ["breadsticks"],
        "pickled vegetables": ["giardiniera"],
        "chutney": ["tomato relish", "pesto"],
        "cumin": ["oregano", "thyme"],
        "garam masala": ["Italian seasoning", "herbes de Provence"],
        "Chinese five-spice": ["cinnamon, nutmeg, and fennel seeds"],
        "Mexican oregano": ["oregano"],
        "epazote": ["thyme", "sage"],
        "mint": ["basil"],
        "black pepper": ["black pepper"],
        "white pepper": ["white pepper"],
        "cayenne pepper": ["crushed red pepper flakes"],
        "paprika": ["smoked paprika", "regular paprika"],
        "chili powder": ["crushed red pepper flakes"],
        "ancho chili powder": ["paprika"],
        "red pepper flakes": ["crushed red pepper flakes"],
        "Tajín": ["salt"],
        "lime zest": ["lemon zest"],
        "bay leaves": ["Italian bay leaves"],
    },
    'techniques': {
        "deep fry": ["pan-fry"],
        "stir-fry": ["saute"],
        "steam": ["poach"]
    }
}

cooking_method_transforms = {
    "bake": ["fry", "grill", "air fry"],
    "fry": ["bake", "grill", "air fry"],
    "grill": ["bake", "pan sear", "broil"],
    "steam": ["boil", "microwave", "pressure cook"],
    "saute": ["stir fry", "grill", "bake"],
    "roast": ["air fry", "grill", "pan sear"],
    "broil": ["grill", "bake", "pan sear"],
    "stir fry": ["saute", "grill", "roast"],
    "poach": ["boil", "simmer", "steam"],
    "braise": ["roast", "simmer", "stew"],
    "toast": ["bake", "broil", "grill"],
    "boil": ["steam", "poach", "pressure cook"]
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