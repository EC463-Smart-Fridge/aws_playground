import json
import requests
import time
import boto3
from datetime import datetime, timedelta

def findProductUsingUPC(upc, api_key):
    # Define the API endpoint URL
    
    url = f"""
    https://api.nal.usda.gov/fdc/v1/foods/search?api_key={api_key}&query="{upc}" +raw
"""

    try:
        # Send an HTTP GET request to the API endpoint
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            response_data = json.dumps(data, indent=4)
            return response_data

        else:
            print(f"ERROR: {response.status_code}: {response.text}")
            exit(-1)

    except Exception as e:
        print(f"ERROR: Failed to request UPC information: {str(e)}")
        exit(-1)

def getInfoFromJSON(response_json):
    try:
        data = json.loads(response_json)
        if (data["totalHits"] == 0):
            print("ERROR: No item information found for given UPC code")
            return {
                'statusCode': 404,
                'body': "ERROR: Item not found"
            }
        for i in range (20):
            name = data["foods"][i]["description"].lstrip().capitalize()
            category = data["foods"][i]["foodCategory"].lstrip().capitalize()
            calories = next((block["value"] for block in data["foods"][i]["foodNutrients"] if block["nutrientId"] == 1008), 0)
            print(name, category, calories)
        return {
            "name" : name,
            "category" : category,
            "calories" : calories
        }
    except Exception as e:
        print(f"ERROR: Failed to parse JSON data: {str(e)}")
        return None

def getGenericNames(item):
    # Define the endpoint
    API_KEY = ""
    api = "?apiKey=" + API_KEY
    url = "https://api.spoonacular.com/food/detect/" + api

    # Craft the POST request data
    payload = {
        'text': item,
    }

    try:
        # Make the POST request
        response = requests.post(url, data=payload)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract and work with the response data (if any)
            data = response.json()

            return data["annotations"][0]['annotation']

        else:
            # Handle errors
            print("Error:", response.status_code, response.text)
            return None
    except Exception as e:
        print("ERROR: Failed to get product name", e)
        return None

def predict_expiration(input_string):
    # Load the predicted expiration times dataset
    with open('expirationPredictions.json', 'r') as file:
        expiration_data = json.load(file)

    # Variables to keep track of the best match
    best_match = None
    best_score = 0

    # Search for a product that best matches the user input
    for product_id, product_info in expiration_data.items():
        keywords = product_info.get('Keywords', [])

        # Calculate match score for current product
        score = sum(1 for keyword in keywords if keyword in input_string)

        # Update best match if current product has higher score
        if score > best_score:
            best_match = product_info
            best_score = score

    # Output results
    if best_match:
        # Calculate predicted expiration date
        expiration_time_days = best_match['Expiration_time_DAYS']
        current_date = datetime.now().date()
        expiration_date = current_date + timedelta(days=expiration_time_days)

        # Convert to Unix timestamp format
        expiration_datetime = datetime.combine(expiration_date, datetime.min.time())
        expiration_timestamp = expiration_datetime.timestamp()
        return int(expiration_timestamp)
    else:
        return None

def insert_item(uid, upc, response_info, product_name):
    
    if (product_name):
        item_name = product_name.title()
        generic_name = product_name.title()
    else:
        item_name = response_info['name'].title()
        generic_name = getGenericNames(response_info['name']).title()
    
    exp_pred = predict_expiration(generic_name)
    if (exp_pred):
        exp_date = exp_pred
    else:
        exp_date = 0
    
    try:
        db_client = boto3.client('dynamodb')
        item_id = 'IT' + str(int(time.time() * 1000))
        item = {
            "pk": {'S': uid },
            "sk": {'S': item_id },
            "UPC":{'S': upc },
            "name":{'S': item_name},
            "quantity": {'N': '0' },
            "exp_date": {'N': str(exp_date) },
            "calories": {'S': str(response_info['calories']) },
            "img_url": {'S': '' },
            "category": {'S': response_info['category']},
            "prod_name" : {'S': generic_name}
        }
        response = db_client.put_item(
            TableName='fridgebase',
            Item=item 
        )
        return {
            "pk": uid,
            "sk": item_id,
            "UPC": upc,
            "name": item_name,
            "quantity": 0,
            "exp_date": exp_date,
            "calories": str(response_info['calories']),
            "img_url": '',
            "category": response_info['category'],
            "prod_name": generic_name
        }
    except Exception as e:
        print("ERROR: Failed to insert into DynamoDB:", e)
        return {}

def lambda_handler(event, context):
    # Define the url to send the request to
    upc = event['upc']
    uid = event['uid']
    product_name = event.get("name")
    
    api_key = ""
    
    # Get the item information using the upc code
    response_json = findProductUsingUPC(upc, api_key)
    response_info = getInfoFromJSON(response_json)

    # If unable to get response information, return a 404 status code
    if (response_info is None):
        return {
            'statusCode': 404,
            'body': "ERROR: Item not found"
        }
        
    response = insert_item(uid, upc, response_info, product_name)
    return response