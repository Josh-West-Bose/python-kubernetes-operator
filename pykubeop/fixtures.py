import json

TEST_CUSTOM_RESOURCE = {
    'apiVersion': 'iam.clearscore.io/v1alpha1',
    'kind': 'IAMRole',
    'metadata': {
        'name': 'test-role',
        'namespace': 'testing',
    },
    'spec': {
        'roleName': 'test-role.namespace.k8s.testing.clearscore.io',
        'assumeRolePolicy': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Sid': '',
                    'Effect': 'Allow',
                    'Principal': {
                        'Service': 'ec2.amazonaws.com'
                    },
                    'Action': 'sts:AssumeRole'
                },
                {
                    'Sid': '',
                    'Effect': 'Allow',
                    'Principal': {
                        'AWS': 'arn:aws:iam:11111111111111:role/some.other.role'
                    },
                    'Action': 'sts:AssumeRole'
                }
            ]
        },
        'policies': {
            'Policy1': {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Sid': '',
                        'Effect': 'Allow',
                        'Action': 'kms:Encrypt',
                        'Resource': 'arn:aws:kms:eu-west-2:11111111111111:alias/my-key'
                    }
                ]
            }
        }
    },
    'status': {}
}

ASSUME_ROLE_POLICY_JSON = json.dumps(TEST_CUSTOM_RESOURCE['spec']['assumeRolePolicy'])
ROLE_POLICY_JSON = json.dumps(TEST_CUSTOM_RESOURCE['spec']['policies']['Policy1'])