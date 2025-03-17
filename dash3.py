import streamlit as st
import sqlite3
import ast
import re
from langchain_ollama import OllamaLLM

# Initialize Ollama Model
llm = OllamaLLM(model="llama3")

# Function to fetch recipes ensuring all ingredients are required
def get_recipes(ingredients, exclude_id=None, limit=10):
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()

    # Convert input string into a list of ingredients
    ingredient_list = [f"%{ing.strip()}%" for ing in ingredients.split(",")]

    # Construct SQL query to ensure ALL ingredients are present
    conditions = " AND ".join(["ingredients LIKE ?" for _ in ingredient_list])

    if exclude_id:
        query = f"SELECT id, title, ingredients, instructions FROM recipes WHERE {conditions} AND id != ? ORDER BY RANDOM() LIMIT {limit}"
        cursor.execute(query, (*ingredient_list, exclude_id))
    else:
        query = f"SELECT id, title, ingredients, instructions FROM recipes WHERE {conditions} ORDER BY RANDOM() LIMIT {limit}"
        cursor.execute(query, ingredient_list)

    recipes = cursor.fetchall()
    conn.close()
    
    return recipes  # Returns multiple recipes

# Function to format instructions
def format_instructions(instructions):
    try:
        instr_list = ast.literal_eval(instructions)
        clean_instructions = []
        for i, step in enumerate(instr_list, start=1):
            step_cleaned = re.sub(r"^\s*\d+[\.\)]*\s*", "", step).strip()
            clean_instructions.append(f"**Step {i}:** {step_cleaned}")
        return clean_instructions
    except:
        return ["Invalid instruction format"]

# Function to format ingredients
def format_ingredients(ingredients):
    try:
        ing_list = ast.literal_eval(ingredients)
        return [f"• {ing}" for ing in ing_list]
    except:
        return ["Invalid ingredient format"]

# Function to generate a recipe using AI
def generate_ai_recipe(ingredients):
    prompt = f"Create a detailed recipe using the following ingredients: {ingredients}. Format it as follows:\n\n" \
             "**[Recipe Title]**\n\n" \
             "Ingredients:\n" \
             "* [ingredient 1]\n" \
             "* [ingredient 2]\n" \
             "* [ingredient 3]\n\n" \
             "Instructions:\n" \
             "1. [Step 1]\n" \
             "2. [Step 2]\n" \
             "3. [Step 3]\n\n" \
             "Include tips if possible."

    ai_response = llm.invoke(prompt)
    
    if not ai_response:
        return None
    
    # Extract title, ingredients, and instructions
    lines = ai_response.split("\n")
    title = lines[0].replace("**", "").strip() if lines else "AI-Generated Recipe"
    
    ing_start = lines.index("Ingredients:") + 1 if "Ingredients:" in lines else None
    instr_start = lines.index("Instructions:") + 1 if "Instructions:" in lines else None

    ingredients_list = []
    instructions_list = []

    if ing_start and instr_start:
        ingredients_list = [line.replace("* ", "").strip() for line in lines[ing_start:instr_start-1] if line.strip()]
        instructions_list = [re.sub(r"^\d+[\.\)]*\s*", "", line).strip() for line in lines[instr_start:] if line.strip()]

    return {
        "title": title,
        "ingredients": ingredients_list,
        "instructions": instructions_list
    }

# Function to save a recipe into the database
def save_recipe(title, ingredients, instructions):
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    
    # Prevent duplicate saves
    cursor.execute("SELECT id FROM saved_recipes WHERE title = ?", (title,))
    if cursor.fetchone():
        st.warning(f"⚠️ Recipe '{title}' is already saved!")
    else:
        cursor.execute("INSERT INTO saved_recipes (title, ingredients, instructions) VALUES (?, ?, ?)",
                       (title, ingredients, instructions))
        conn.commit()
        st.success(f"✅ Recipe '{title}' saved!")
    
    conn.close()

# Function to fetch saved recipes
def get_saved_recipes():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, ingredients, instructions FROM saved_recipes ORDER BY id DESC")
    saved = cursor.fetchall()
    conn.close()
    return saved

# Function to delete a saved recipe
def delete_saved_recipe(recipe_id):
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()
    st.rerun()  # ✅ Correct method to refresh UI

# Streamlit UI
st.title("🍽️ AI Recipe Finder")
st.write("🔍 *Enter ingredients (e.g. 'chicken, garlic'):* ")
ingredient_input = st.text_input("", placeholder="e.g., chicken, garlic")

if 'recipes' not in st.session_state:
    st.session_state.recipes = []
if 'ai_recipe' not in st.session_state:
    st.session_state.ai_recipe = None

if st.button("Find Recipes"):
    if ingredient_input.strip():
        recipes = get_recipes(ingredient_input, limit=10)  # Get multiple recipes
        if recipes:
            st.session_state.recipes = recipes
        else:
            st.warning("No recipes found for that ingredient.")
    else:
        st.warning("Please enter an ingredient.")

# Display fetched recipes
if st.session_state.recipes:
    for recipe in st.session_state.recipes:
        recipe_id, title, ingredients, instructions = recipe
        
        st.markdown(f"### ✨ {title}")
        st.markdown("### 🥕 Ingredients:")
        st.markdown("\n".join(format_ingredients(ingredients)))
        
        st.markdown("### 🔍 Instructions:")
        st.markdown("\n".join(format_instructions(instructions)))

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"📌 Save {title}", key=f"save_{recipe_id}"):
                save_recipe(title, ingredients, instructions)
        with col2:
            if st.button(f"🔄 Find Another Recipe", key=f"find_another_{recipe_id}"):
                new_recipes = get_recipes(ingredient_input, exclude_id=recipe_id, limit=1)
                if new_recipes:
                    st.session_state.recipes.append(new_recipes[0])
                    st.rerun()
                else:
                    st.warning("No more recipes found for this ingredient.")

# AI-generated recipe section
if st.session_state.ai_recipe:
    ai_recipe = st.session_state.ai_recipe
    st.markdown("## 🤖 AI-Generated Recipe")
    st.markdown(f"### {ai_recipe['title']}")
    
    st.markdown("### 🥕 Ingredients:")
    st.markdown("\n".join(ai_recipe["ingredients"]))
    
    st.markdown("### 🔍 Instructions:")
    st.markdown("\n".join(ai_recipe["instructions"]))

# Saved recipes section
st.markdown("## ⭐ Saved Recipes")
saved_recipes = get_saved_recipes()

if saved_recipes:
    for recipe in saved_recipes:
        recipe_id, title, ingredients, instructions = recipe
        st.markdown(f"### {title}")
        st.write(f"**Ingredients:** {ingredients}")
        st.write(f"**Instructions:** {instructions}")

        if st.button(f"❌ Remove {title}", key=f"delete_{recipe_id}"):
            delete_saved_recipe(recipe_id)
else:
    st.write("No saved recipes yet.")
