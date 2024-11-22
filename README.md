
### Downloads:
- "conda env create -f environment.yml"
- "conda activate recipe"
- "python -m spacy download en_core_web_md"

### Rasa Instructions:

#### You will need to keep two terminals open to avoid errors that different systems experience
 1. rasa validate
 2. rasa train
 3. rasa test
 4. First Terminal: rasa run actions
 5. Second Terminal: rasa shell

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
    - What are the cooking methods?
    - List the cooking methods
    - Tell me the methods of cooking
    - What are the techniques used?
    - What is the current step?
    - Tell me the current step.
    - What's the step I'm on?
    - What is the next step?
    - Tell me the next step.
    - What's after this step?
    - What is the previous step?
    - Tell me the previous step.
    - What's the step before this one?
    - What tools are needed for the current step?
    - What methods are used for the current step?
    - What ingredients are needed for the current step?