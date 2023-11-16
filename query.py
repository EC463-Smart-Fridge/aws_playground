import boto3


def fetch_user_items(uid):
    # Initialize AWS DynamoDB Client
    db_client = boto3.client('dynamodb')

    try:
        # Query for if inputted UPC exists in the database already
        response = db_client.query(
            TableName="fridgebase",
            ExpressionAttributeValues= {
                ":pk": {
                    'S':uid
                }
            },
            ExpressionAttributeNames= {
                "#pk": "pk"
            },
            Select="ALL_ATTRIBUTES",
            ConsistentRead = True,
            KeyConditionExpression="#pk = :pk"
        )

        status = response['ResponseMetadata']
        items = response['Items']
    except Exception as e:
        print("ERROR: Failed to fetch user items:", str(e))

    print(status['HTTPStatusCode'])
    if (status['HTTPStatusCode'] != 200):
        print("Failed to fetch user items")
        exit(1)
    
    response_items = []
    for item in items:
        if (item.get('UPC')):
            response_items.append({
                "ItemID" : item["sk"],
                "name" : item["name"],
                "UPC" : item["UPC"],
                "category" : item["category"],
                "calories" : item["calories"]
            })
    

    print(response_items)
    return 0    



fetch_user_items("UID1")