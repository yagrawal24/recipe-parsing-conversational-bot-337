
### Downloads:
- "conda env create -f environment.yml"
- "conda activate recipe"
- "python -m spacy download en_core_web_md"

### Rasa Instructions:

#### You will need to keep 3 terminals open to avoid errors that different systems experience
 1. First Terminal: rasa train (may need to delete models in the /models)
 2. Second Terminal: rasa run actions
 3. Third Terminal: rasa shell

#### Inside of "rasa shell"
- Say "Hello"
- Copy and paste recipes
- Ask how to and what questions
- Can ask any questions listed in rasaTest/data/nlu.yml
    - What are the ingredients?
    - Tell me the ingredients.
    - Can you list the ingredients?
    - Ingredients please.
    - I want to know the ingredients.
    - What tools do I need?
    - List the tools for this recipe.