import unittest
from app import app, serialize_mongo_document
from bson import ObjectId
import json

class FlashcardAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_serialize_mongo_document(self):
        # Test serializing an ObjectId
        obj_id = ObjectId()
        serialized = serialize_mongo_document(obj_id)
        self.assertEqual(serialized, str(obj_id))

        # Test serializing a list
        obj_id_list = [ObjectId(), ObjectId()]
        serialized_list = serialize_mongo_document(obj_id_list)
        self.assertEqual(serialized_list, [str(obj_id_list[0]), str(obj_id_list[1])])

        # Test serializing a dict
        obj_id_dict = {"_id": ObjectId(), "value": "test"}
        serialized_dict = serialize_mongo_document(obj_id_dict)
        self.assertEqual(serialized_dict["_id"], str(obj_id_dict["_id"]))
        self.assertEqual(serialized_dict["value"], "test")

    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'flashcards', response.data)

    def test_add_flashcard_get(self):
        response = self.app.get('/add_flashcard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Flashcard', response.data)

    def test_add_flashcard_post(self): 
        response = self.app.post('/add_flashcard', data=dict(question='Test Question', answer='Test Answer'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Question', response.data)

    def test_add_flashcard_post_missing_data(self):
        response = self.app.post('/add_flashcard', data=dict(question='', answer=''), follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Missing question or answer', response.data)

    def test_get_flashcards(self):
        response = self.app.get('/api/flashcards')
        self.assertEqual(response.status_code, 200)
        flashcards = json.loads(response.data)
        self.assertIsInstance(flashcards, list)

if __name__ == '__main__':
    unittest.main()
 