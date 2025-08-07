import boto3
import csv
import json
import time

# --- CONFIG ---
CSV_FILE = "data/dataset.csv"
KINESIS_STREAM_NAME = "financial-transaction-fraud-detection-using-aws-stream"
REGION = "us-east-1"
RECORDS_PER_SECOND = 300
BATCH_SIZE = 25

# --- KINESIS CLIENT ---
kinesis = boto3.client("kinesis", region_name=REGION)

def stream_csv_to_kinesis():
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        
        batch = []
        records_sent = 0
        start_time = time.time()
        
        for i, row in enumerate(reader):
            # Add record to batch
            record = {
                'Data': json.dumps(row),
                'PartitionKey': row.get("trans_num", str(i))
            }
            batch.append(record)
            
            # Send batch when full
            if len(batch) >= BATCH_SIZE:
                # Send the batch
                try:
                    kinesis.put_records(Records=batch, StreamName=KINESIS_STREAM_NAME)
                    records_sent += len(batch)
                except Exception as e:
                    print(f"Batch failed: {e}")
                
                batch = []
                
                # Rate control: ensure we don't exceed 300 records/sec
                elapsed_time = time.time() - start_time
                expected_time = records_sent / RECORDS_PER_SECOND
                
                if elapsed_time < expected_time:
                    time.sleep(expected_time - elapsed_time)
                
                # Progress update
                actual_rate = records_sent / elapsed_time if elapsed_time > 0 else 0
                print(f"Sent {records_sent} records | Rate: {actual_rate:.1f}/sec")
        
        # Send remaining records
        if batch:
            try:
                kinesis.put_records(Records=batch, StreamName=KINESIS_STREAM_NAME)
                records_sent += len(batch)
            except Exception as e:
                print(f"Final batch failed: {e}")
        
        total_time = time.time() - start_time
        final_rate = records_sent / total_time
        print(f"Completed: {records_sent} records in {total_time:.1f}s at {final_rate:.1f} records/sec")

if __name__ == "__main__":
    stream_csv_to_kinesis()