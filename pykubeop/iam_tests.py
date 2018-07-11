import datetime
import os
import unittest
import unittest.mock

from botocore.stub import Stubber
import op.iam
import op.fixtures

os.environ['AWS_REGION'] = 'test-region'

class TestIAMRole(unittest.TestCase):
    maxDiff = None

    @unittest.mock.patch('boto3.client')
    def test_init_calls_validate(self, mock_client):
        with unittest.mock.patch('op.iam.IAMRole.validate') as mock_validate:
            op.iam.IAMRole(op.fixtures.TEST_CUSTOM_RESOURCE)
            self.assertTrue(mock_validate.called)
    
    @unittest.mock.patch('boto3.client')
    def test_validate_fails_with_unset_variables(self, mock_client):
        with self.assertRaises(op.errors.InvalidSpecException):
            cr = op.fixtures.TEST_CUSTOM_RESOURCE
            del(cr['spec']['roleName'])
            op.iam.IAMRole(cr)

        with self.assertRaises(op.errors.InvalidSpecException):
            cr = op.fixtures.TEST_CUSTOM_RESOURCE
            del(cr['spec']['assumeRolePolicy'])
            op.iam.IAMRole(cr)
        with self.assertRaises(op.errors.InvalidSpecException):
            cr = op.fixtures.TEST_CUSTOM_RESOURCE
            del(cr['spec']['policies'])
            op.iam.IAMRole(cr)

    @unittest.mock.patch('boto3.client')
    def test_ensure_calls_correct_function_depending_on_state(self, mock_client):
        instance = op.iam.IAMRole(op.fixtures.TEST_CUSTOM_RESOURCE)
        with unittest.mock.patch('op.iam.IAMRole.ensure_created') as mock_create:
            instance.ensure('CREATED')
            self.assertTrue(mock_create.called)
        with unittest.mock.patch('op.iam.IAMRole.ensure_modified') as mock_modified:
            instance.ensure('MODIFIED')
            self.assertTrue(mock_modified.called)
        with unittest.mock.patch('op.iam.IAMRole.ensure_deleted') as mock_deleted:
            instance.ensure('DELETED')
            self.assertTrue(mock_deleted.called)

    def test_ensure_created_raises_when_role_exists(self):
        instance = op.iam.IAMRole(op.fixtures.TEST_CUSTOM_RESOURCE)
        stubber = Stubber(instance.__dict__['_IAMRole__iamcli'])
        stubber.add_response(
            'get_role',
            {
                'Role': {
                    'Path': '/',
                    'RoleName': 'test-role',
                    'Arn': 'arn:aws:iam::123456789012:role/S3Access',
                    'RoleId': '12345678900987654321',
                    'CreateDate': datetime.datetime.now()
                }
            }
        )
        with stubber:
            with unittest.mock.patch('kubernetes.client.CustomObjectsApi.patch_namespaced_custom_object') as mock_patch:
                with self.assertRaises(Exception):
                    instance.ensure_created()
                    stubber.assert_no_pending_responses()

    def test_ensure_created_makes_required_calls_with_valid_spec(self):
        instance = op.iam.IAMRole(op.fixtures.TEST_CUSTOM_RESOURCE)
        stubber = Stubber(instance.__dict__['_IAMRole__iamcli'])
        stubber.add_client_error('get_role', 'NoSuchEntityException')
        stubber.add_response(
            'create_role',
            {
                'Role': {
                    'Path': '/',
                    'RoleName': 'test-role',
                    'Arn': 'arn:aws:iam:12345678012:role/S3Access',
                    'RoleId': '12345678900987654321',
                    'CreateDate': datetime.datetime.now()
                }
            },
            {
                'RoleName': 'test-role.namespace.k8s.testing.clearscore.io',
                'AssumeRolePolicyDocument': op.fixtures.ASSUME_ROLE_POLICY_JSON
            }
        )
        stubber.add_response(
            'put_role_policy',
            {},
            {
                'RoleName': 'test-role',
                'PolicyName': 'Policy1',
                'PolicyDocument': op.fixtures.ROLE_POLICY_JSON
            }
        )
        with stubber:
            instance.ensure_created()
            stubber.assert_no_pending_responses()

    def test_ensure_deleted_makes_required_called(self):
        instance = op.iam.IAMRole(op.fixtures.TEST_CUSTOM_RESOURCE)
        stubber = Stubber(instance.__dict__['_IAMRole__iamcli'])
        stubber.add_response('delete_role', {}, {'RoleName': 'test-role'})
