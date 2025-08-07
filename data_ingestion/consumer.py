import boto3
import json
import base64
import uuid
import csv
import io
from datetime import datetime

s3 = boto3.client("s3")
bucket_name = "raw-financial-transaction-fraud-detection-using-aws"
final_prefix = "fraud_data/batch_"
buffer_cache = []

def lambda_handler(event, context):
    # Decode and parse incoming Kinesis records
    records = []
    for record in event["Records"]:
        payload = base64.b64decode(record["kinesis"]["data"])
        try:
            records.append(json.loads(payload))
        except Exception as e:
            print(f"Invalid JSON payload: {e}")
    
    print(f"Received {len(records)} records")

    # Add to buffer
    buffer_cache.extend(records)
    print(f"Buffer now has {len(buffer_cache)} records")

    # Process batches of 5000 records
    while len(buffer_cache) >= 5000:
        batch = buffer_cache[:5000]
        
        # Convert to CSV format
        csv_content = convert_to_csv(batch)
        
        # Generate unique S3 key
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        uid = uuid.uuid4().hex[:8]
        s3_key = f"{final_prefix}{timestamp}_{uid}.csv"

        # Upload to S3
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=csv_content,
            ContentType='text/csv'
        )
        print(f"Uploaded 5000-record CSV batch to {s3_key}")

        # Remove processed records efficiently
        del buffer_cache[:5000]
        print(f"Buffer now has {len(buffer_cache)} remaining records")

    return {"statusCode": 200}

def convert_to_csv(records):
    """Convert JSON records to CSV format"""
    if not records:
        return ""
    
    # Create CSV in memory
    output = io.StringIO()
    
    # Get field names from first record
    fieldnames = records[0].keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    # Write header and data
    writer.writeheader()
    writer.writerows(records)
    
    return output.getvalue()