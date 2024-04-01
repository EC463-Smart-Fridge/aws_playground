import json
import requests
import time
import boto3

# Access the secrets / api keys stored in github secrets

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
    
def insert_item(uid, upc, response_info):
    try:
        db_client = boto3.client('dynamodb')
        item_id = 'IT' + str(int(time.time() * 1000))
        item = {
            "pk": {'S': uid },
            "sk": {'S': item_id },
            "UPC":{'S': upc },
            "name":{'S': response_info['name'] },
            "quantity": {'N': '0' },
            "exp_date": {'N': '0' },
            "calories": {'S': str(response_info['calories']) },
            "img_url": {'S': '' },
            "category": {'S': response_info['category']}
        }
        response = db_client.put_item(
            TableName='fridgebase',
            Item=item 
        )
        return {
            "pk": uid,
            "sk": item_id,
            "UPC": upc,
            "name": response_info['name'],
            "quantity": 0,
            "exp_date": 0,
            "calories": str(response_info['calories']),
            "img_url": '',
            "category": response_info['category']
        }
    except Exception as e:
        print("ERROR: Failed to insert into DynamoDB:", e)
        return {}

def lambda_handler(event, context):
    # Define the url to send the request to
    upc = event['upc']
    uid = event['uid']
    api_key = "wn0aUcaBRdgzaIAXL9lzh69bEkskIAkPfolNO8RW"
    response_json = findProductUsingUPC(upc, api_key)
    response_info = getInfoFromJSON(response_json)

    # If unable to get response information, return a 404 status code
    if (response_info is None):
        return {
            'statusCode': 404,
            'body': "ERROR: Item not found"
        }
    
    response = insert_item(uid, upc, response_info)
    return response

lambda_handler({'upc' : "banana", 'uid' : 'UID1'}, None)