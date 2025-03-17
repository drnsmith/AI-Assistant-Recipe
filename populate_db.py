import sqlite3
import csv

# Database connection
DB_FILE = "recipes.db"

def create_database():
    """Creates the SQLite database and recipes table if not exists."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            instructions TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print(" Database and table created successfully.")

def insert_recipe(title, ingredients, instructions):
    """Inserts a single recipe into the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO recipes (title, ingredients, instructions) VALUES (?, ?, ?)", 
                   (title, ingredients, instructions))

    conn.commit()
    conn.close()
    print(f" Recipe '{title}' added successfully.")

def populate_sample_recipes():
    """Adds some sample recipes into the database."""
    sample_recipes = [
        ("Spaghetti Bolognese", 
         "spaghetti, minced beef, tomato sauce, onion, garlic, olive oil, salt, pepper", 
         "1. Cook the spaghetti. 2. Sauté onions and garlic. 3. Add minced beef and cook. 4. Pour tomato sauce and simmer. 5. Serve over spaghetti."),
        
        ("Chicken Curry", 
         "chicken breast, curry powder, coconut milk, onion, garlic, ginger, salt, pepper", 
         "1. Sauté onions, garlic, and ginger. 2. Add chicken and curry powder. 3. Pour coconut milk and simmer. 4. Serve hot with rice."),

        ("Vegetable Stir-Fry", 
         "broccoli, bell peppers, carrots, soy sauce, ginger, garlic, sesame oil", 
         "1. Heat oil in a pan. 2. Add garlic and ginger. 3. Stir-fry vegetables. 4. Add soy sauce and toss. 5. Serve immediately.")
    ]

    for title, ingredients, instructions in sample_recipes:
        insert_recipe(title, ingredients, instructions)

def import_from_csv(csv_file):
    """Imports recipes from a CSV file (format: title, ingredients, instructions)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    with open(csv_file, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            if len(row) != 3:
                continue
            cursor.execute("INSERT INTO recipes (title, ingredients, instructions) VALUES (?, ?, ?)", 
                           (row[0], row[1], row[2]))

    conn.commit()
    conn.close()
    print(f" Recipes imported successfully from {csv_file}.")

if __name__ == "__main__":
    create_database()
    populate_sample_recipes()
    # Uncomment the line below if you have a CSV file with recipes
    # import_from_csv("recipes.csv")
    print(" Database setup complete!")
