import json
import os
import streamlit as st
import requests
import base64

## Save new recipes permanently to recipes.json in github

def save_recipes(recipes_list):
    """
    Save the recipes list back to GitHub using the GitHub Contents API.
    Overwrites recipes.json with a new commit.
    """

    token = st.secrets["github_token"]
    repo = st.secrets["github_repo"]
    branch = st.secrets.get("github_branch", "main")
    path = st.secrets.get("recipes_file_path", "recipes.json")

    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"

    sha_resp = requests.get(api_url)
    if sha_resp.status_code == 200:
        sha = sha_resp.json()["sha"]
    else:
        st.error("⚠️ Could not fetch file SHA from GitHub.")
        return False

    new_content = json.dumps(recipes_list, indent=2).encode("utf-8")
    encoded = base64.b64encode(new_content).decode("utf-8")

    payload = {
        "message": "Update recipes.json from Streamlit app",
        "content": encoded,
        "sha": sha,
        "branch": branch
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    res = requests.put(api_url, headers=headers, json=payload)

    if res.status_code in (200, 201):
        return True
    else:
        st.error(f"❌ Failed saving recipes to GitHub: {res.text}")
        return False


def save_deleted(deleted_list):
    """
    Optional: save deleted recipes to deleted_recipes.json in GitHub.
    Creates file if missing.
    """
    token = st.secrets["github_token"]
    repo = st.secrets["github_repo"]
    branch = st.secrets.get("github_branch", "main")
    path = "deleted_recipes.json"

    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"

    sha = None
    sha_resp = requests.get(api_url)
    if sha_resp.status_code == 200:
        sha = sha_resp.json()["sha"]

    new_content = json.dumps(deleted_list, indent=2).encode("utf-8")
    encoded = base64.b64encode(new_content).decode("utf-8")

    payload = {
        "message": "Update deleted recipes",
        "content": encoded,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    res = requests.put(api_url, headers=headers, json=payload)

    return res.status_code in (200, 201)

##### Set Up #####

# GitHub secrets
GITHUB_TOKEN = st.secrets["github_token"]
GITHUB_REPO = st.secrets["github_repo"]
GITHUB_BRANCH = st.secrets.get("github_branch", "main")
RECIPES_FILE = st.secrets.get("recipes_file_path", "recipes.json")

# Load recipes from GitHub (force fresh fetch every rerun)
import time

timestamp = int(time.time())  # cache buster

raw_url = (
    f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{RECIPES_FILE}"
    f"?nocache={timestamp}"
)

try:
    response = requests.get(raw_url, headers={"Cache-Control": "no-cache"})
    response.raise_for_status()
    recipes = response.json()
except Exception as e:
    st.error(f"Failed to load recipes from GitHub: {e}")
    recipes = []

# Keep deleted_recipes in memory
deleted_recipes = []

st.markdown("<h1>Delaney's Cookbook!</h1>", unsafe_allow_html=True)


##### App Functions #####

# Search recipes (sidebar) 
search_term = st.sidebar.text_input("Search recipes by title, ingredient, or tag")

# Filter recipes based on search (sidebar)
if search_term:
    filtered_recipes = [
        r for r in recipes
        if search_term.lower() in r.get("title", "").lower()
        or any(search_term.lower() in ing.lower() for ing in r.get("ingredients", []))
        or any(search_term.lower() in tag.lower() for tag in r.get("tags", []))
    ]
else:
    filtered_recipes = recipes

# Recipe dropdown (sidebar)
recipe_titles = sorted([r.get("title", "Untitled") for r in filtered_recipes])
selected_title = st.sidebar.selectbox("Select a recipe", [""] + recipe_titles, key="recipe_select")

# Add new recipe (sidebar)
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

# Recycle bin (sidebar)
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

# Main display
if selected_title == "":
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

        # Display recipe details
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

        # Ratings
        st.subheader("Rate this recipe")
        rating = st.slider("Your rating", 1, 5, 3, key=f"rating_{selected_title}")
        if st.button("Submit rating", key=f"submit_rating_{selected_title}"):
            if "ratings" not in selected_recipe:
                selected_recipe["ratings"] = []
            selected_recipe["ratings"].append(rating)
            save_recipes(recipes)
            st.success(f"Thanks! You rated {selected_title} {rating} ⭐")
            st.rerun()

        if "ratings" in selected_recipe and selected_recipe["ratings"]:
            avg_rating = sum(selected_recipe["ratings"]) / len(selected_recipe["ratings"])
            stars = "⭐" * int(round(avg_rating))
            st.write(f"Average rating: {avg_rating:.1f} {stars}")
        else:
            st.write("No ratings yet.")

        # Delete button
        if st.button("Delete Recipe", key="delete_recipe"):
            # Remove from main recipes list
            recipes = [r for r in recipes if r.get("title") != selected_title]
        
            # Track deleted
            deleted_recipes.append(selected_recipe)
        
            # Save changes to GitHub
            save_recipes(recipes)
            save_deleted(deleted_recipes)
        
            # Clear selected title so dropdown resets
            st.session_state["recipe_select"] = ""
        
            st.success(f"'{selected_title}' moved to Recycle Bin!")
            st.rerun()


    else:
        st.warning("Recipe not found.")

##### Styling #####
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


print("app.py has been saved in the current folder!")
