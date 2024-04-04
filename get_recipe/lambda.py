import requests
import json

def getJsonFromGET(url): # Returns the JSON information in the dict format
    try:
        # Make a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON data from the response
            jsonData = response.json()

            # Return the parsed JSON data
            return jsonData
        else:
            # If the request was not successful, print an error message
            print(f"Error: {response.status_code}")
            return None
        
    except Exception as e:
        # Handle exceptions, if any
        print(f"An error occurred: {e}")
        return None
    
    
def booleanVariablesToString(boolean_variables):
    formatted_string = ""
    for variable, value in boolean_variables.items():
        formatted_string += f"&{variable}={'true' if value else 'false'}"
    return formatted_string
    
def urlPrser(request, API_KEY, parameterList):
    # This function contructs the URL needed to make the desired call
    
    url = "https://api.spoonacular.com/"
    api = "?apiKey=" + API_KEY
    subdirectory1 = ""
    parameters = ""

    if request == 1: # getRecipeByIngredients
            subdirectory1 = "recipes/findByIngredients"
            parameters = "&ingredients=" + parameterList[0] + "," + ",".join(["+" + ingredient for ingredient in parameterList[1:] if ingredient])
    if request == 2: # getRecipeInstructions
            subdirectory1 = "recipes/" + str(parameterList) + "/analyzedInstructions"
    if request == 3: # getCaloriesByRecipe
            subdirectory1 = "recipes/" + str(parameterList) + "/nutritionWidget.json"
    if request == 4: # getRecipeByName
            subdirectory1 = "recipes/complexSearch/"
            parameters = "&query=" + str(parameterList)
    if request == 5: # getIngredientAmounts
            subdirectory1 = "recipes/" + str(parameterList) + "/information"
            parameters = "&includeNutrition=false"

    url = url + subdirectory1 + api + parameters
    return url

def getRecipeByIngredients(API_KEY, parameterList): # parameterList should be a list of ingredients
    NUMTORETURN = 8 # Sets number of recipes to return
    RANKING = 2 # Set to 1 to maximize used ingredients, 2 to minimize missing ingredients

    url = urlPrser(1, API_KEY, parameterList)
    url = url + "&number=" + str(NUMTORETURN)
    url = url + "&ranking=" + str(RANKING)
    
    # Create a list to store tuples of recipe ID and name
    recipesData = getJsonFromGET(url)
    recipeResults = []
    # Iterate over each recipe
    for recipe in recipesData:
        # Extract recipe ID and name
        recipeID = recipe.get('id')
        recipeNAME = recipe.get('title')
        recipeIMAGE = recipe.get('image')
        # Append tuple to list
        recipeResults.append((recipeID, recipeNAME, recipeIMAGE))

    return recipeResults # returns a tuple with the recipe ID and name
    ''' For example:
    [(673463, 'Slow Cooker Apple Pork Tenderloin'), (633547, 'Baked Cinnamon Apple Slices'), (663748, 'Traditional Apple Tart'), (715381, 'Creamy Lime Pie Square Bites'), (639637, 'Classic scones'), (635315, 'Blood Orange Margarita'), (1155776, 'Easy Homemade Chocolate Truffles'), (652952, 'Napoleon - A Creamy Puff Pastry Cake'), (664089, 'Turkish Delight'), (635778, 'Boysenberry Syrup')]
    '''

def getRecipeByName(API_KEY, parameterList): #parameterList is name to search
    NUMTORETURN = 10 # Sets number of recipes to return

    url = urlPrser(4, API_KEY, parameterList)
    url = url + "&number=" + str(NUMTORETURN)
    
    # Create a list to store tuples of recipe ID and name
    recipesData = getJsonFromGET(url)
    recipeResults = []

    for recipe in recipesData['results']:
        try:
            # Extract recipe ID and name
            recipeID = recipe['id']
            recipeNAME = recipe['title']
            recipeIMAGE = recipe['image']
            # Append tuple to list
            recipeResults.append((recipeID, recipeNAME, recipeIMAGE))
        except:
            print(f"Error: key is missing for a recipe.")

    return recipeResults # returns a tuple with the recipe ID and name

def getRecipeInstructions(API_KEY, recipeID):
    booleanParameters = {"stepBreakdown": False}
    booleanParameters = booleanVariablesToString(booleanParameters)

    url = urlPrser(2, API_KEY, recipeID)
    url = url + booleanParameters

    # Load JSON data
    recipeData = getJsonFromGET(url)

    # Extract steps and ingredient names
    steps = []

    for recipe in recipeData:
        for step in recipe['steps']:
            steps.append(step['step'])

    return steps # returns two lists, one with the recipe steps and one with the recipe ingredients

def getCaloriesByRecipe(API_KEY, recipeID):
    url = urlPrser(3, API_KEY, recipeID)

    # Load JSON data
    recipeData = getJsonFromGET(url)

    # Extracting calories
    calories = None
    for nutrient in recipeData['nutrients']:
        if nutrient['name'] == 'Calories':
            calories = nutrient['amount']

    return calories

def getIngredientAmounts(API_KEY, recipeID):
    url = urlPrser(5, API_KEY, recipeID)

    # Load JSON data
    recipeData = getJsonFromGET(url)

    # Extracting calories
    ingredientInfo = []
    for ingredient in recipeData['extendedIngredients']:
        amt = str(ingredient['amount'])
        if (ingredient['unit']):
            amt += ' ' + ingredient['unit']
        ingredientInfo.append((ingredient['name'].title(), amt))

    return ingredientInfo

def lambda_handler(event, context):

    '''
    Only the first query parameter is prefixed with a ? (question mark), all subsequent ones will be prefixed with a & (ampersand). 
    That is how URLs work and nothing related to our API. Here's a full example with two parameters apiKey and includeNutrition: 
    https://api.spoonacular.com/recipes/716429/information?apiKey=YOUR-API-KEY&includeNutrition=true. 

    "https://api.spoonacular.com/recipes/complexSearch?apiKey=YOUR-API-KEY&query=pasta&maxFat=25&number=2"
    '''

    # Define use of API
    API_KEY = ""
    ingredients = event['ingredients']
    num_recipes = 5

    recipes = getRecipeByIngredients(API_KEY, ingredients)
    response_info = []

    for recipe in recipes:
        # Only loop while haven't gotten 5 recipes yet
        if (num_recipes <= 0):
            break
            
        recipe_info = {}
        recipe_info['name'] = recipe[1]
        recipe_info['img'] = recipe[2]
        
        recipe_steps = getRecipeInstructions(API_KEY, recipe[0])
        # Ignore recipe if it doesn't have any recipes or steps
        if (len(recipe_steps) <= 0):
             continue
        
        recipe_ingreds = getIngredientAmounts(API_KEY, recipe[0])
        if (len(recipe_ingreds) <= 0):
             continue

        ingreds = []
        for ingredient in recipe_ingreds:
             ingreds.append({
                  "name" : ingredient[0],
                  "amt" : ingredient[1]
             })

        recipe_info = {
             "name" : str(recipe[1]),
             "img" : str(recipe[2]),
             "steps" : recipe_steps,
             "ingredients" : ingreds,
             "calories" : getCaloriesByRecipe(API_KEY, recipe[0])
        }
        response_info.append(recipe_info)
        num_recipes -= 1

    # If unable to get response information, return a 404 status code
    if (response_info is None):
        return {
            'statusCode': 404,
            'body': "ERROR: Item not found"
        }
    
    return response_info

print(lambda_handler({'ingredients' : ["eggs", "FAIRLIFE milk" , "sargento string cheese"]}, None))
