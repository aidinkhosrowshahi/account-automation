import boto3
import json
import os

sts = boto3.client('sts')
all_regions = list(os.environ['LimitRequestRegions'].split(","))

# Limit increase template
services = [
    {
        'service_code': 'vpc',
        'quota_code': 'L-0EA8095F',  # Inbound or outbound rules per security group
        'desired_value': 500
    },
    {
        'service_code': 'iam',
        'quota_code': 'L-FE177D64',  # The maximum number of IAM roles that you can create in this account
        'desired_value': 2000
    }
]


def get_existing_quota(service_code, quota_code, accountId, regions):
    """
    Retrieve the existing quota limit for a specific service and quota code.

    Args:
    - service_code: Service code (e.g., 'vpc', 'iam')
    - quota_code: Quota code for the service
    - accountId: AWS account ID
    - regions: AWS region

    Returns:
    - Existing quota limit or None if the quota is not found
    """
    try:
        # Assume role for linked account to make Service Quotas limit increase
        response = sts.assume_role(
            RoleArn=f'arn:aws:iam::{accountId}:role/OrganizationAccountAccessRole',
            RoleSessionName='newsession'
        )
        
        quotas = boto3.client(
            'service-quotas',
            region_name=regions,
            aws_access_key_id=response["Credentials"]["AccessKeyId"],
            aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
            aws_session_token=response["Credentials"]["SessionToken"]
        )

        # Get service quota
        response = quotas.get_service_quota(
            ServiceCode=service_code,
            QuotaCode=quota_code
        )

        # Extract and return the existing quota value
        quota_value = response['Quota']['Value']
        return quota_value

    except Exception as e:
        print(f"Error retrieving existing quota: {e}")
        return None


def request_service_quota_increase(service_code, quota_code, desired_value, accountId, regions):
    """
    Request a service quota increase for a specified service and quota code.

    Args:
    - service_code: Service code (e.g., 'vpc', 'iam')
    - quota_code: Quota code for the service
    - desired_value: Desired quota value
    - accountId: AWS account ID
    - regions: AWS region

    Returns:
    - Response from the Service Quotas API or None if the request is not made
    """
    try:
        # Check existing quota
        existing_quota = get_existing_quota(service_code, quota_code, accountId, regions)

        if existing_quota is not None:
            if existing_quota >= desired_value:
                print(f"Skipping - current limit: {existing_quota} is already greater than desired value: {desired_value}")
            else:
                # Assume role for linked account to make Service Quotas limit increase
                response = sts.assume_role(
                    RoleArn=f'arn:aws:iam::{accountId}:role/OrganizationAccountAccessRole',
                    RoleSessionName='newsession'
                )

                quotas = boto3.client(
                    'service-quotas',
                    region_name=regions,
                    aws_access_key_id=response["Credentials"]["AccessKeyId"],
                    aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
                    aws_session_token=response["Credentials"]["SessionToken"]
                )

                # Request service quota increase
                response = quotas.request_service_quota_increase(
                    ServiceCode=service_code,
                    QuotaCode=quota_code,
                    DesiredValue=desired_value
                )

                return response
        else:
            print("Error: Unable to retrieve existing quota.")
            return None

    except Exception as e:
        print(f"Error requesting service quota increase: {e}")
        return None


def lambda_handler(event, context):
    """
    Lambda handler function.

    Args:
    - event: AWS Lambda event
    - context: AWS Lambda context

    Returns:
    - None
    """
    try:
        # Get required information from event
        state = event['detail']['serviceEventDetails']['createAccountStatus']['state']
        accountId = event['detail']['serviceEventDetails']['createAccountStatus']['accountId']

        if state == "SUCCEEDED":
            for region in all_regions:
                for service in services:
                    print(f"Requesting service quotas: service={service['service_code']}, quota={service['quota_code']}, desired value={service['desired_value']}, account={accountId}, region={region}")
                    print(request_service_quota_increase(service['service_code'], service['quota_code'], service['desired_value'], accountId, region))

    except Exception as e:
        print(f"Error in lambda_handler: {e}")

