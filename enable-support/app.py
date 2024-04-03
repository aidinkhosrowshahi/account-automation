import boto3
import json
import os


ccEmailAddresses = os.environ['ccEmailAddresses']
SupportPlan = os.environ['SupportPlan']


def create_case(account_ids):
    """
    Creates a support case requesting to enable Enterprise Support.

    :param account_ids: list of str
    :return: string
    """
    sts = boto3.client('sts')
    response = sts.assume_role(
        RoleArn='arn:aws:iam::{}:role/OrganizationAccountAccessRole'.format(account_ids),
        RoleSessionName='newsession'
    )

    support = boto3.client(
        'support',
        region_name='us-east-1',
        aws_access_key_id=response["Credentials"]["AccessKeyId"],
        aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
        aws_session_token=response["Credentials"]["SessionToken"]
    )


   
    case_subject = f'Enable Enterprise Support on new accounts'
    case_severity_code = 'low'
    case_category_code = 'other-account-issues'
    case_service_code = 'customer-account'
    accounts = str(account_ids).replace("'", "")
    case_communication_body = f'Hi AWS! Please enable {SupportPlan} on new account IDs {accounts} with the same ' \
        f'support plan as this Payer account. This case was created automatically - please resolve when done.'
    case_cc_emails = os.environ['ccEmailAddresses']
    case_issue_type = 'customer-service'

    response = support.create_case(
        subject=case_subject,
        severityCode=case_severity_code,
        categoryCode=case_category_code,
        serviceCode=case_service_code,
        communicationBody=case_communication_body,
        ccEmailAddresses=[case_cc_emails],
        language='en',
        issueType=case_issue_type
    )

    # Print Case ID to return.
    case_id = response['caseId']
    case = support.describe_cases(
        caseIdList=[case_id])
    display_id = case['cases'][0]['displayId']

    print(f'Case {display_id} opened for accounts {accounts}.')


def lambda_handler(event, context):
    accountId = ""
    print(event)
    # message_body = json.loads(event['Records'][0]['body'])
    state = event['detail']['serviceEventDetails']['createAccountStatus']['state']
    accountId = event['detail']['serviceEventDetails']['createAccountStatus']['accountId']
   
    
    if state == 'SUCCEEDED':
        print(f'DEBUG: Account creation succeeded - account id is {accountId}. Adding account ID to '
              f'parameter store for later processing.')
        create_case(accountId)


    else:
        print('DEBUG: Account creation failed - please check CloudTrail for details.')



