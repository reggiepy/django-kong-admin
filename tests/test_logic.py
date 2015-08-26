from __future__ import unicode_literals, print_function

from django.test import TestCase

from kong_admin import models
from kong_admin.factory import get_kong_client, get_api_sync_engine, get_consumer_sync_engine
from kong_admin import logic

from .factories import APIReferenceFactory, ConsumerReferenceFactory
from .fake import fake


class APIReferenceLogicTestCase(TestCase):
    def setUp(self):
        self.client = get_kong_client()
        self._cleanup_api = []

    def tearDown(self):
        self.client.close()

        for api_ref in self._cleanup_api:
            self.assertTrue(isinstance(api_ref, models.APIReference))
            api_ref = models.APIReference.objects.get(id=api_ref.id)  # reloads!!
            get_api_sync_engine().withdraw(self.client, api_ref)

    def test_failed(self):
        # Create incomplete api_ref
        api_ref = APIReferenceFactory(target_url=fake.url())

        # Mark for auto cleanup
        self._cleanup_afterwards(api_ref)

        # Try to sync, expect an error
        with self.assertRaises(ValueError):
            logic.synchronize_api(self.client, api_ref)

        self.assertFalse(api_ref.synchronized)

        # Fix api_ref
        api_ref.public_dns = fake.domain_name()
        api_ref.save()

        # Sync again
        logic.synchronize_api(self.client, api_ref)
        self.assertTrue(api_ref.synchronized)

        # Check kong
        result = self.client.apis.retrieve(api_ref.kong_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['target_url'], api_ref.target_url)
        self.assertEqual(result['public_dns'], api_ref.public_dns)

    def test_sync_initial(self):
        # Create api_ref
        api_ref = APIReferenceFactory(target_url=fake.url(), public_dns=fake.domain_name())

        # Mark for auto cleanup
        self._cleanup_afterwards(api_ref)

        # Sync
        logic.synchronize_api(self.client, api_ref)
        self.assertTrue(api_ref.synchronized)

        # Check kong
        result = self.client.apis.retrieve(api_ref.kong_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['target_url'], api_ref.target_url)
        self.assertEqual(result['public_dns'], api_ref.public_dns)

    def test_sync_update(self):
        # Create api_ref
        api_ref = APIReferenceFactory(target_url=fake.url(), public_dns=fake.domain_name())

        # Mark for auto cleanup
        self._cleanup_afterwards(api_ref)

        # Publish
        logic.synchronize_api(self.client, api_ref)
        self.assertTrue(api_ref.synchronized)

        # Check kong
        result = self.client.apis.retrieve(api_ref.kong_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['target_url'], api_ref.target_url)
        self.assertEqual(result['public_dns'], api_ref.public_dns)
        self.assertEqual(result['name'], api_ref.public_dns)

        # Update
        new_name = fake.api_name()
        self.assertNotEqual(new_name, api_ref.name)
        api_ref.name = new_name
        api_ref.save()

        # Publish
        logic.synchronize_api(self.client, api_ref)
        self.assertTrue(api_ref.synchronized)

        # Check kong
        result = self.client.apis.retrieve(api_ref.kong_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['target_url'], api_ref.target_url)
        self.assertEqual(result['public_dns'], api_ref.public_dns)
        self.assertEqual(result['name'], new_name)

    def test_withdraw(self):
        # Create api_ref
        api_ref = APIReferenceFactory(target_url=fake.url(), public_dns=fake.domain_name())

        # Publish
        logic.synchronize_api(self.client, api_ref)
        self.assertTrue(api_ref.synchronized)

        # Check kong
        result = self.client.apis.retrieve(api_ref.kong_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['target_url'], api_ref.target_url)
        self.assertEqual(result['public_dns'], api_ref.public_dns)

        # Store kong_id
        kong_id = api_ref.kong_id

        # You can delete afterwards
        get_api_sync_engine().withdraw(self.client, api_ref)
        self.assertFalse(api_ref.synchronized)

        # Check kong
        with self.assertRaises(ValueError):
            result = self.client.apis.retrieve(kong_id)

    def _cleanup_afterwards(self, api_ref):
        self._cleanup_api.append(api_ref)
        return api_ref


class ConsumerReferenceLogicTestCase(TestCase):
    def setUp(self):
        self.client = get_kong_client()
        self._cleanup_consumers = []

    def tearDown(self):
        self.client.close()

        for consumer_ref in self._cleanup_consumers:
            self.assertTrue(isinstance(consumer_ref, models.ConsumerReference))
            consumer_ref = models.ConsumerReference.objects.get(id=consumer_ref.id)  # reloads!!
            get_consumer_sync_engine().withdraw(self.client, consumer_ref)

    def test_failed(self):
        # Create incomplete api_ref
        consumer_ref = ConsumerReferenceFactory()

        # Mark for auto cleanup
        self._cleanup_afterwards(consumer_ref)

        # Try to sync, expect an error
        with self.assertRaises(ValueError):
            logic.synchronize_consumer(self.client, consumer_ref)

        self.assertFalse(consumer_ref.synchronized)

        # Fix api_ref
        consumer_ref.username = fake.consumer_name()
        consumer_ref.save()

        # Sync again
        logic.synchronize_consumer(self.client, consumer_ref)
        self.assertTrue(consumer_ref.synchronized)

        # Check kong
        result = self.client.consumers.retrieve(consumer_ref.kong_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['username'], consumer_ref.username)

    def test_sync_initial(self):
        # Create api_ref
        consumer_ref = ConsumerReferenceFactory(username=fake.consumer_name())

        # Mark for auto cleanup
        self._cleanup_afterwards(consumer_ref)

        # Sync
        logic.synchronize_consumer(self.client, consumer_ref)
        self.assertTrue(consumer_ref.synchronized)

        # Check kong
        result = self.client.consumers.retrieve(consumer_ref.kong_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['username'], consumer_ref.username)

    def test_sync_update(self):
        # Create api_ref
        consumer_ref = ConsumerReferenceFactory(username=fake.consumer_name())

        # Mark for auto cleanup
        self._cleanup_afterwards(consumer_ref)

        # Publish
        logic.synchronize_consumer(self.client, consumer_ref)
        self.assertTrue(consumer_ref.synchronized)

        # Check kong
        result = self.client.consumers.retrieve(consumer_ref.kong_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['username'], consumer_ref.username)

        # Update
        new_name = fake.consumer_name()
        self.assertNotEqual(new_name, consumer_ref.username)
        consumer_ref.username = new_name
        consumer_ref.save()

        # Publish
        logic.synchronize_consumer(self.client, consumer_ref)
        self.assertTrue(consumer_ref.synchronized)

        # Check kong
        result = self.client.consumers.retrieve(consumer_ref.kong_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['username'], new_name)

    def test_withdraw(self):
        # Create api_ref
        consumer_ref = ConsumerReferenceFactory(username=fake.consumer_name())

        # Publish
        logic.synchronize_consumer(self.client, consumer_ref)
        self.assertTrue(consumer_ref.synchronized)

        # Check kong
        result = self.client.consumers.retrieve(consumer_ref.kong_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['username'], consumer_ref.username)

        # Store kong_id
        kong_id = consumer_ref.kong_id

        # You can delete afterwards
        get_consumer_sync_engine().withdraw(self.client, consumer_ref)
        self.assertFalse(consumer_ref.synchronized)

        # Check kong
        with self.assertRaises(ValueError):
            result = self.client.consumers.retrieve(kong_id)

    def _cleanup_afterwards(self, consumer_ref):
        self._cleanup_consumers.append(consumer_ref)
        return consumer_ref
