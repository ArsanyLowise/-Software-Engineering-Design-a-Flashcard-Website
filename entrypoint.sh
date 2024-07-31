

# Start the Flask application
flask run &

# Wait for MongoDB to start
sleep 10

# Add data to MongoDB
mongoimport --host mongo --db flashcard_db --collection flashcards --file /app/flashcard_db.flashcards.json --jsonArray

# Export data from MongoDB
mongoexport --host mongo --db flashcard_db --collection flashcards --out /app/exported_flashcards.json

# Keep the container running
tail -f /dev/null