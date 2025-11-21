import json
import os
import streamlit as st

# File paths
RECIPES_FILE = "recipes.json"
DELETED_FILE = "recipes_deleted.json"

# Function to save recipes to JSON
def save_recipes(recipes_list):
    with open(RECIPES_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes_list, f, ensure_ascii=False, indent=4)

def save_deleted(recipes_list):
    with open(DELETED_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes_list, f, ensure_ascii=False, indent=4)

# Load recipes
if os.path.exists(RECIPES_FILE):
    with open(RECIPES_FILE, "r", encoding="utf-8") as f:
        recipes = json.load(f)
else:
    recipes = []

if os.path.exists(DELETED_FILE):
    with open(DELETED_FILE, "r", encoding="utf-8") as f:
        deleted_recipes = json.load(f)
else:
    deleted_recipes = []

st.markdown("<h1>Delaney's Cookbook!</h1>", unsafe_allow_html=True)

# Sidebar search box
search_term = st.sidebar.text_input("Search recipes by title, ingredient, or tag")

# Filter recipes based on search
if search_term:
    filtered_recipes = [
        r for r in recipes
        if search_term.lower() in r.get("title", "").lower()
        or any(search_term.lower() in ing.lower() for ing in r.get("ingredients", []))
        or any(search_term.lower() in tag.lower() for tag in r.get("tags", []))
    ]
else:
    filtered_recipes = recipes

# Select recipe dropdown
recipe_titles = sorted([r.get("title", "Untitled") for r in filtered_recipes])
selected_title = st.sidebar.selectbox("Select a recipe", [""] + recipe_titles, key="recipe_select")

# ---------- Sidebar: Add New Recipe ----------

st.sidebar.header("+ Add New Recipe")
with st.sidebar.form("add_recipe_form", clear_on_submit=True):
    title = st.text_input("Recipe Title")
    ready_in = st.text_input("Ready in (e.g. 30 minutes)")
    servings = st.text_input("Servings (e.g. 2)")
    temp = st.text_input("Temperature (e.g. 375°F)")
    ingredients = st.text_area("Ingredients (one per line)")
    instructions = st.text_area("Instructions (one per line)")
    notes = st.text_area("Notes or Source")
    tags_input = st.text_input("Tags (comma-separated, e.g. Chicken, Main, Baked)")
    submitted = st.form_submit_button("Add Recipe")

    if submitted and title and ingredients and instructions:
        new_recipe = {
            "title": title,
            "ready_in": ready_in,
            "servings": servings,
            "temperature": temp,
            "ingredients": [i.strip() for i in ingredients.splitlines() if i.strip()],
            "instructions": [i.strip() for i in instructions.splitlines() if i.strip()],
            "notes": notes,
            "tags": [t.strip() for t in tags_input.split(",") if t.strip()]
        }
        recipes.append(new_recipe)
        save_recipes(recipes)
        st.success(f"✅ '{title}' added successfully!")
        st.rerun()

# ----------- Main Display -----------
if selected_title == "":
    # Welcome Page
    st.markdown("""
    ## Welcome
    Here you can:
    - Select an existing recipe
    - Search by title, ingredient, or tag  
    - Add new recipes 
    - Delete recipes and restore them later  

    """)
else:
    selected_recipe = next((r for r in filtered_recipes if r.get("title") == selected_title), None)

    if selected_recipe:
        st.header(selected_recipe.get("title", "Untitled"))

        # Display metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Ready In:** {selected_recipe.get('ready_in', 'N/A')}")
        with col2:
            st.write(f"**Yield:** {selected_recipe.get('servings', 'N/A')}")
        with col3:
            st.write(f"**Temperature:** {selected_recipe.get('temperature', 'N/A')}")

        # Ingredients
        st.subheader("Ingredients")
        ingredients = selected_recipe.get("ingredients", [])
        if ingredients:
            for item in ingredients:
                st.markdown(f"- {item}")
        else:
            st.markdown("_No ingredients listed._")

        # Instructions
        st.subheader("Preparation Steps")
        instructions = selected_recipe.get("instructions", [])
        if instructions:
            for i, step in enumerate(instructions, 1):
                st.markdown(f"{i}. {step}")
        else:
            st.markdown("_No instructions provided._")

        # Notes
        st.subheader("Notes")
        notes = selected_recipe.get("notes", "")
        if notes:
            if isinstance(notes, list):
                for note in notes:
                    st.markdown(f"- {note}")
            else:
                st.markdown(notes)
        else:
            st.markdown("_No notes provided._")

        # Tags
        tags = selected_recipe.get("tags", [])
        if tags:
            st.subheader("Tags")
            st.markdown(", ".join(tags))

        # Delete button (moves to recycle bin)
        if st.button("Delete Recipe", key="delete_recipe"):
            recipes = [r for r in recipes if r.get("title") != selected_title]
            deleted_recipes.append(selected_recipe)
            save_recipes(recipes)
            save_deleted(deleted_recipes)
            st.success(f"'{selected_title}' moved to Recycle Bin!")
            st.rerun()
    else:
        st.warning("Recipe not found.")

# ---------- Sidebar: Recycle Bin ----------
st.sidebar.header("🗑 Recycling Bin")
if deleted_recipes:
    deleted_titles = [r.get("title", "Untitled") for r in deleted_recipes]
    selected_deleted = st.sidebar.selectbox("Deleted recipes", deleted_titles, key="deleted_recipe")

    col1, col2 = st.sidebar.columns(2)
    if col1.button("♻ Restore"):
        recipe_to_restore = next((r for r in deleted_recipes if r.get("title") == selected_deleted), None)
        if recipe_to_restore:
            deleted_recipes = [r for r in deleted_recipes if r.get("title") != selected_deleted]
            recipes.append(recipe_to_restore)
            save_recipes(recipes)
            save_deleted(deleted_recipes)
            st.success(f"'{selected_deleted}' restored!")
            st.rerun()
    if col2.button("Permanent Delete"):
        deleted_recipes = [r for r in deleted_recipes if r.get("title") != selected_deleted]
        save_deleted(deleted_recipes)
        st.success(f"'{selected_deleted}' permanently deleted!")
        st.rerun()
else:
    st.sidebar.info("Recycle Bin is empty.")

# ---------- Style & Color ----------
st.markdown("""
<style>

        /* App background & font defaults */
    .stApp { background-color: #e2ebf3; }
    html, body, [class*="css"] { font-family: 'Helvetica', sans-serif; color: #556277; }
    .stMarkdown, .stMarkdown p, .stMarkdown li { font-family: 'Helvetica', sans-serif; color: #556277; }

    /* Headings */
    .stMarkdown h1 { color: #556277; }
    .stMarkdown h2, .stMarkdown h3 { color: #B15E6C; }
    
   

    /* Target markdown headings */
    .stMarkdown h1 { color: #556277; }  /* Main title color */
    .stMarkdown h2,
    h2 {
        color: #B15E6C !important;
        font-family: 'Helvetica', sans-serif !important;
    }
    .stMarkdown h3,
    h3 {
        color: #B15E6C !important;
        font-family: 'Helvetica', sans-serif !important;
    }

    /* Sidebar background */
    section[data-testid="stSidebar"] { 
        background-color: #E2EBF3; 
    }

    /* Button styling */
    button { 
        background-color: #b15e6c !important; 
        color: white !important; 
        border-radius: 8px !important; 
    }

    /* Sidebar body text */
    section[data-testid="stSidebar"] {
        color: #556277;        /* Default text color in sidebar */
        font-family: 'Helvetica', sans-serif;
}

    /* Sidebar headers (e.g., "Add New Recipe", "Recycling Bin") */
    section[data-testid="stSidebar"] h2 {
        color: #556277;        /* Match body text color */
        font-family: 'Helvetica', sans-serif;
}

    /* Buttons inside the sidebar */
    section[data-testid="stSidebar"] button {
        color: white !important;             /* Button text color */
        background-color: #b15e6c !important;  /* Button background */
        border-radius: 8px !important;
        font-family: 'Helvetica', sans-serif;
}

    /* Sidebar input boxes and textareas */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] select {
        background-color: white !important;  /* Force white background */
        color: #556277 !important;           /* Match body text color */
        font-family: 'Helvetica', sans-serif;
}

    /* Force sidebar selectboxes to have white background and dark text */
    section[data-testid="stSidebar"] div[role="combobox"] > div,
    section[data-testid="stSidebar"] div[role="combobox"] input {
        background-color: white !important;
        color: #556277 !important;
        font-family: 'Helvetica', sans-serif !important;
}


      
</style>
  
""", unsafe_allow_html=True)

