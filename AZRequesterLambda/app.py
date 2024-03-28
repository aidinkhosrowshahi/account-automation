import boto3
import os

# Fetching environment variables
ReferenceAccount = os.environ['ReferenceAccount']
regions = "eu-west-1, sa-east-1, us-east-1, us-west-1, us-west-2, ap-northeast-1, ap-southeast-1, ap-southeast-2"
case_cc_emails = os.environ['ccEmailAddresses']


def create_case(account_id, reference_account, regions):
    """
    Create a support case to align AZs for the given account.
    
    :param account_id: str, AWS account ID
    :param reference_account: str, reference AWS account for AZ mapping
    :param regions: str, list of AWS regions
    :return: dict, response from Support API
    """
    
    # Assume role for the target account
    sts = boto3.client('sts')
    response = sts.assume_role(
        RoleArn=f'arn:aws:iam::{account_id}:role/OrganizationAccountAccessRole',
        RoleSessionName='newsession'
    )
    
    # Initialize Support client with the assumed credentials
    support = boto3.client(
        'support',
        region_name='us-east-1',
        aws_access_key_id=response["Credentials"]["AccessKeyId"],
        aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
        aws_session_token=response["Credentials"]["SessionToken"]
    )
    
    # Create support case
    response_support = support.create_case(
        subject=f'Please align account {account_id} to match the alignment of AZs in account {reference_account}',
        serviceCode='account-management',
        severityCode='low',
        categoryCode='billing',
        communicationBody=f'Please align account {account_id} to match the alignment of AZs in account {reference_account} in regions {regions}.',
        ccEmailAddresses=[case_cc_emails],
        language='en',
        issueType='technical'
    )

    return response_support


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    :param event: dict, AWS Lambda event
    :param context: object, AWS Lambda context
    """
    
    print(event)
    
    # Extract account details from the event
    state = event['detail']['serviceEventDetails']['createAccountStatus']['state']
    account_id = event['detail']['serviceEventDetails']['createAccountStatus']['accountId']
    
    if state == "SUCCEEDED":
        print(f"Creating AZ alignment support case for account {account_id} to match the alignment of AZs in account {ReferenceAccount} in regions {regions}")
        
        # Create a support case for the new account
        create_case(account_id, ReferenceAccount, regions)
