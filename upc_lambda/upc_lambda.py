import json
import os
import requests
import time
import boto3

# Access the secrets / api keys stored in github secrets

def findProductUsingUPC(upc, api_key):
    # Define the API endpoint URL
    
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={api_key}&query={upc}"

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
            exit(-1)
        name = data["foods"][0]["description"].lstrip().capitalize()
        category = data["foods"][0]["foodCategory"].lstrip().capitalize()
        calories = next((block["value"] for block in data["foods"][0]["foodNutrients"] if block["nutrientId"] == 1008), 0)
        return name, category, calories
    except Exception as e:
        print(f"ERROR: Failed to parse JSON data: {str(e)}")
        exit(-1)
    
def insert_item(uid, upc, response_info):
    try:
        db_client = boto3.client('dynamodb')
        response = db_client.put_item(
            TableName='fridgebase',
            Item={
                "pk": {'S': uid },
                "sk": {'S': 'IT' + str(int(time.time() * 1000)) },
                "UPC":{'S': upc },
                "name":{'S': response_info['name'] },
                "quantity": {'N': '0' },
                "exp_date": {'N': '0' },
                "calories": {'S': str(response_info['calories']) },
                "img_url": {'S': '' },
                "category": {'S': response_info['category']}
            }
        )
    except Exception as e:
        print("ERROR: Failed to insert into DynamoDB:", e)
        exit(1)

def lambda_handler(event, context):
    # Define the url to send the request to
    upc = event['upc']
    uid = event['uid']
    api_key = "DEMO_KEY"
    response_json = findProductUsingUPC(upc, api_key)
    name, category, cal = getInfoFromJSON(response_json)
    response_info = {
        "name" : name,
        "category" : category,
        "calories" : cal
    }
    insert_item(uid, upc, response_info)

    return {
        'statusCode': 200,
        'body': response_info
    }