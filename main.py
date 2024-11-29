from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import pymysql
import datetime
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI()

# Add CORS middleware to allow cross-origin communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend's domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection function
def connect_db():
    """Connect to the MySQL database."""
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="grobuddy_db"
    )

# Data Models
class CreateAccount(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    user_id: int
    message: str

class UpdatePassword(BaseModel):
    password: str

class Category(BaseModel):
    name: str

class GroceryItem(BaseModel):
    name: str
    quantity: int
    unit: str
    price: float
    category_id: int
    purchased: Optional[bool] = False
    purchased_at: Optional[str] = None

class EditAccount(BaseModel):
    current_username: str
    new_username: Optional[str] = None
    new_password: Optional[str] = None

class MarkItem(BaseModel):
    purchased: bool

# Simulated Dependency for User Authentication
def get_current_user_id():
    """Simulated user authentication. Replace with JWT or session-based logic."""
    # Simulated user ID (should be replaced with actual authentication logic)
    return 1

# Routes
@app.get("/")
def main():
    """Welcome endpoint."""
    return {"message": "Welcome to Grobuddy"}

# User Management
@app.post("/register/")
def register(user: CreateAccount):
    """Register a new user."""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (user.username, user.password)
            )
            conn.commit()
        conn.close()
        return {"message": f"User {user.username} registered successfully"}
    except pymysql.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/login/", response_model=LoginResponse)
def login(user: CreateAccount):
    """Log in a user and return their user ID."""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, password FROM users WHERE username=%s", (user.username,))
            result = cursor.fetchone()
        conn.close()

        if not result or result[1] != user.password:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        return {"message": "Login successful", "user_id": result[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/profile/")
def get_user_profile(username: str):
    """Fetch user profile data."""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT username, email FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        conn.close()
        return {"username": user[0], "email": user[1]}
    except Exception as e:
        print(f"Error fetching profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

app = FastAPI()

@app.patch("/edit_acc/")
def edit_account(current_username: str, new_username: str = None, new_password: str = None):
    """Update a user's username and/or password."""
    try:
        conn = connect_db()
        try:
            with conn.cursor() as cursor:
                # Ensure the user exists
                cursor.execute("SELECT id FROM users WHERE username=%s", (current_username,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="User not found")

                # Update username if provided
                if new_username:
                    cursor.execute(
                        "UPDATE users SET username=%s WHERE username=%s",
                        (new_username, current_username),
                    )
                    current_username = new_username  # Update local variable

                # Update password if provided (hashed)
                if new_password:
                    hashed_password = bcrypt.hash(new_password)
                    cursor.execute(
                        "UPDATE users SET password=%s WHERE username=%s",
                        (hashed_password, current_username),
                    )

                conn.commit()

        finally:
            conn.close()  # Ensure the connection is closed

        return {"message": "Account updated successfully"}

    except Exception as e:
        print(f"Error updating account: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/delete_acc/{username}/")
def delete_account(username: str):
    """Delete a user's account."""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE username=%s", (username,))
            conn.commit()
        conn.close()
        return {"message": f"Account {username} deleted"}
    except Exception as e:
        print(f"Error deleting account: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/categories/")
def get_categories():
    """Retrieve all categories."""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM categories")
            categories = cursor.fetchall()
        conn.close()
        return [{"id": cat[0], "name": cat[1]} for cat in categories]
    except Exception as e:
        print(f"Error retrieving categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Grocery Item Management
@app.post("/add/")
def add_item(item: GroceryItem, user_id: int = Depends(get_current_user_id)):
    """Add a grocery item for the current user."""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM categories WHERE id = %s", (item.category_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Invalid category_id")

            cursor.execute(
                """
                INSERT INTO grocery_items (name, quantity, unit, price, category_id, purchased, purchased_at, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (item.name, item.quantity, item.unit, item.price, item.category_id, item.purchased, item.purchased_at, user_id)
            )
            conn.commit()
        conn.close()
        return {"message": f"Added {item.name} to the list"}
    except Exception as e:
        print(f"Error adding item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/items/")
def get_items(user_id: int = Depends(get_current_user_id)):
    """Retrieve all items added by the current user."""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT gi.id, gi.name, gi.quantity, gi.unit, gi.price, gi.category_id, 
                       gi.purchased, gi.purchased_at, gc.name as category_name
                FROM grocery_items gi
                JOIN categories gc ON gi.category_id = gc.id
                WHERE gi.user_id = %s
            """, (user_id,))
            items = cursor.fetchall()
        conn.close()
        return [
            {
                "id": item[0],
                "name": item[1],
                "quantity": item[2],
                "unit": item[3],
                "price": item[4],
                "category_id": item[5],
                "purchased": item[6],
                "purchased_at": item[7],
                "category_name": item[8],
            }
            for item in items
        ]
    except Exception as e:
        print(f"Error fetching items: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.patch("/update-item/{item_id}/")
def update_item(item_id: int, item: GroceryItem, user_id: int = Depends(get_current_user_id)):
    """Update an item if it belongs to the current user."""
    conn = connect_db()
    with conn.cursor() as cursor:
        # Check if the item exists and belongs to the user
        cursor.execute("SELECT id FROM grocery_items WHERE id=%s AND user_id=%s", (item_id, user_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Item not found or not authorized to update")

        # Update the item
        cursor.execute(
            "UPDATE grocery_items SET name=%s, quantity=%s, unit=%s, price=%s, category_id=%s WHERE id=%s",
            (item.name, item.quantity, item.unit, item.price, item.category_id, item_id)
        )
        conn.commit()
    conn.close()
    return {"message": f"Updated item {item_id}"}

@app.delete("/delete-item/{item_id}/")
def delete_item(item_id: int):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM grocery_items WHERE id=%s", (item_id,))
        conn.commit()
    conn.close()
    return {"message": f"Deleted item {item_id}"}

@app.patch("/mark/{item_id}/")
def toggle_mark_purchased(item_id: int, body: MarkItem):
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE grocery_items SET purchased=%s, purchased_at=%s WHERE id=%s",
                (body.purchased, datetime.datetime.utcnow() if body.purchased else None, item_id)
            )
            conn.commit()
        conn.close()
        return {"message": f"Item {item_id} marked as {'purchased' if body.purchased else 'not purchased'}"}
    except Exception as e:
        print(f"Error toggling mark purchased: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/recent_pur/")
def recent_purchases():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM grocery_items WHERE purchased=1 ORDER BY purchased_at DESC")
        items = cursor.fetchall()
    conn.close()
    return [
        {"id": item[0], "name": item[1], "quantity": item[2], "unit": item[3], "price": item[4], "purchased_at": item[5]}
        for item in items
    ]

@app.delete("/clear_purchased/")
def clear_purchased():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM grocery_items WHERE purchased=1")
        conn.commit()
    conn.close()
    return {"message": "Cleared all purchased items"}

@app.get("/total_cost/")
def total_cost():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT SUM(price * quantity) FROM grocery_items WHERE purchased=1")
        total = cursor.fetchone()[0]
    conn.close()
    return {"total_cost": total}
