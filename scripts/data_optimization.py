import json
import boto3
import uuid 
import time
def lambda_handler(event, context):
    # Retrieve S3 object details from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    unique_ingestion_id = str(uuid.uuid4())

    # Generate a unique dataset ID
    unique_dataset_id = str(uuid.uuid4())

    # Generate a unique data source ID
    unique_data_source_id = str(uuid.uuid4())
    sns_topic_arn = "arn:aws:sns:us-west-2:093985745052:CSVReportSavedTopic"

    # Fetch JSON content from S3
    s3_client = boto3.client('s3')
    quicksight_client = boto3.client('quicksight', region_name='us-west-2')  # Update region as needed
    try:
      
        json_obj = s3_client.get_object(Bucket=bucket, Key=key)
        json_content = json_obj['Body'].read().decode('utf-8')

        # Convert JSON to CSV
        data = json.loads(json_content)
        csv_content = ""
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            csv_content += ",".join(data[0].keys()) + "\n"  # Assuming first element contains keys
            for item in data:
                csv_content += ",".join(str(item.get(key, "")) for key in data[0].keys()) + "\n"


            # Upload CSV to the same bucket
            csv_bucket = bucket
            csv_key = key.replace(".json", ".csv")
            s3_client.put_object(Bucket=csv_bucket, Key=csv_key, Body=csv_content)
            # Generate JSON manifest content
            manifest = {
                "fileLocations": [{"URIs": ["s3://{}/{}".format(bucket, csv_key)]}]
            }

            # Upload JSON manifest to S3
            manifest_key = key.replace(".json", "_manifest.json")

            s3_client.put_object(Bucket=csv_bucket, Key=manifest_key, Body=json.dumps(manifest))

            response = quicksight_client.create_data_source(
            AwsAccountId='093985745052',
            DataSourceId=unique_data_source_id,  # Provide a unique ID for the data source
            Name='DataSourceName1',
            Type='S3',
            DataSourceParameters={
                'S3Parameters': {
                    'ManifestFileLocation': {
                        'Bucket': bucket,
                        'Key': manifest_key
                    }
                }
            }
        )   
 


            dataset_response = quicksight_client.create_data_set(
            AwsAccountId='093985745052',
            DataSetId=unique_dataset_id,  # Provide a unique ID for the dataset
            Name='DatasetName1',
            ImportMode='SPICE',
            PhysicalTableMap={
                'YourTableName': {
                    'S3Source': {
                        'DataSourceArn': response['Arn'],
                        'UploadSettings': {
                            'Format': 'CSV',
                            'StartFromRow': 1,
                            'ContainsHeader': True
                        },
                        'InputColumns': [  # Specify the columns in your CSV
                            {
                                'Name': 'id',
                                'Type': 'STRING'
                            },
                            {
                                'Name': 'name',
                                'Type': 'STRING'
                            },
                            {
                                'Name': 'age',
                                'Type': 'STRING'
                            },
                            {
                                'Name': 'city',
                                'Type': 'STRING'
                            }
                        ]
                    }
                }
            }
                        
        )    

            dataset_id = dataset_response['Arn'].split('/')[-1]  # Extracting the dataset ID

            # Trigger ingestion for the dataset
            ingestion_response = quicksight_client.create_ingestion(
                AwsAccountId='093985745052',
                DataSetId=dataset_id,  # Use the dataset ID
                IngestionId=unique_ingestion_id,  # Provide a unique ID for the ingestion
                IngestionType='FULL_REFRESH',  # Change as needed
            )    



            sns_client = boto3.client('sns', region_name='us-west-2')  # Update the region as needed

            # Publish a message to the SNS topic
            sns_message = {
                'default': json.dumps('CSV report saved successfully'),
                'lambda': json.dumps('CSV report saved successfully')
            }

            sns_client.publish(
                TargetArn=sns_topic_arn,
                Message=json.dumps(sns_message),
                MessageStructure='json'
            )
  

        
            
            
            return {
                'statusCode': 200,
                'body': 'CSV conversion and upload successful',
                'response': response,
                'data_set_response' :dataset_response,
                'ingestion_response': ingestion_response
            }
        else:
            return {
                'statusCode': 400,
                'body': 'Invalid JSON structure'
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }

 



