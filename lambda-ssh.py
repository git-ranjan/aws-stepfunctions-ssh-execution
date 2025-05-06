import paramiko
import os
import json
import boto3
from botocore.exceptions import ClientError
import io

def get_secret_dict(secret_name, region_name):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret_string = get_secret_value_response['SecretString']
        if secret_string:
            return json.loads(secret_string)
    except ClientError as e:
        raise Exception(f"Unable to retrieve secret: {e}")

def lambda_handler(event, context):
    hostname = event['host']
    secret_name = event['secret_name']
    region_name = event.get('region_name', 'us-east-1')
    command = event.get('command', 'uptime')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        secret = get_secret_dict(secret_name, region_name)
        username = secret['username']
        password = secret['password']
        client.connect(hostname=hostname, username=username, password=password)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        errors = stderr.read().decode()

        return {
            'statusCode': 200,
            'output': output,
            'errors': errors
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'error': str(e)
        }
    
    finally:
        if 'client' in locals():
            client.close() 