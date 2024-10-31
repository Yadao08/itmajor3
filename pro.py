from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pymysql
import datetime

app = FastAPI()

def connect_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="grobuddy_db"
    )

class CreateAccount(BaseModel):
    username: str
    password: str

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

@app.get("/")
def main():
    return {"message": "Welcome to Grobuddy"}

@app.post("/register/")
def register(user: CreateAccount):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                       (user.username, user.password))
        conn.commit()
    conn.close()
    return {"message": f"User {user.username} registered successfully"}

@app.post("/login/")
def login(user: CreateAccount):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT password FROM users WHERE username=%s", (user.username,))
        result = cursor.fetchone()
    conn.close()
    if not result or user.password != result[0]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful"}

@app.post("/add/")
def add_item(item: GroceryItem):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO grocery_items (name, quantity, unit, price, category_id) VALUES (%s, %s, %s, %s, %s)", 
                       (item.name, item.quantity, item.unit, item.price, item.category_id))
        conn.commit()
    conn.close()
    return {"message": f"Added {item.name} to the list"}

@app.get("/items/")
def get_items():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM grocery_items")
        items = cursor.fetchall()
    conn.close()
    return [{"id": item[0], "name": item[1], "quantity": item[2], "unit": item[3], "price": item[4], "category_id": item[5]} for item in items]

@app.get("/search/")
def search_item(name: str):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM grocery_items WHERE name LIKE %s", (f"%{name}%",))
        items = cursor.fetchall()
    conn.close()
    if not items:
        raise HTTPException(status_code=404, detail="Item not found")
    return [{"id": item[0], "name": item[1], "quantity": item[2], "unit": item[3], "price": item[4], "category_id": item[5]} for item in items]

@app.patch("/update-item/{item_id}/")
def update_item(item_id: int, item: GroceryItem):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE grocery_items SET name=%s, quantity=%s, unit=%s, price=%s, category_id=%s WHERE id=%s", 
                       (item.name, item.quantity, item.unit, item.price, item.category_id, item_id))
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

@app.patch("/mark/{item_id}/") # marking items as purchased
def mark_purchased(item_id: int):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE grocery_items SET purchased=1, purchased_at=%s WHERE id=%s",
                       (datetime.datetime.utcnow(), item_id))
        conn.commit()
    conn.close()
    return {"message": f"Marked item {item_id} as purchased"}

@app.get("/recent_pur/")
def recent_purchases():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM grocery_items WHERE purchased=1 ORDER BY purchased_at DESC")
        items = cursor.fetchall()
    conn.close()
    return [{"id": item[0], "name": item[1], "quantity": item[2], "unit": item[3], "price": item[4], "purchased_at": item[5]} 
            for item in items]

@app.delete("/clear_purchased/")
def clear_purchased():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM grocery_items WHERE purchased=1")
        conn.commit()
    conn.close()
    return {"message": "Cleared all purchased items"}

@app.get("/prev_pur/")
def previous_purchases():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM grocery_items WHERE purchased=1")
        items = cursor.fetchall()
    conn.close()
    return [{"id": item[0], "name": item[1], "quantity": item[2], "unit": item[3], "price": item[4]} for item in items]

@app.patch("/edit_acc/")
def edit_account(username: str, new_password: str):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE users SET password=%s WHERE username=%s", (new_password, username))
        conn.commit()
    conn.close()
    return {"message": "Account updated"}

@app.delete("/delete_acc/{username}/")
def delete_account(username: str):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE username=%s", (username,))
        conn.commit()
    conn.close()
    return {"message": f"Account {username} deleted"}

@app.patch("/purchase_all/") # mark as purchased
def purchase_all():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE grocery_items SET purchased=1")
        conn.commit()
    conn.close()
    return {"message": "Marked all items as purchased"}

@app.get("/unpur_items/") # view unpurchased items
def unpurchased_items():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM grocery_items WHERE purchased=0")
        items = cursor.fetchall()
    conn.close()
    return [{"id": item[0], "name": item[1], "quantity": item[2], "unit": item[3], "price": item[4]} for item in items]

@app.patch("/update_qty/{item_id}/")
def update_quantity(item_id: int, quantity: int):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE grocery_items SET quantity=%s WHERE id=%s", (quantity, item_id))
        conn.commit()
    conn.close()
    return {"message": f"Updated item {item_id} quantity to {quantity}"}

@app.patch("/update_price/{item_id}/")
def update_price(item_id: int, price: float):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE grocery_items SET price=%s WHERE id=%s", (price, item_id))
        conn.commit()
    conn.close()
    return {"message": f"Updated item {item_id} price to {price}"}

@app.patch("/update_unit/{item_id}/")
def update_unit(item_id: int, unit: str):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE grocery_items SET unit=%s WHERE id=%s", (unit, item_id))
        conn.commit()
    conn.close()
    return {"message": f"Updated item {item_id} unit to {unit}"}

@app.get("/total_cost/")
def total_cost():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT SUM(price * quantity) FROM grocery_items WHERE purchased=1")
        total = cursor.fetchone()[0]
    conn.close()
    return {"total_cost": total}

@app.post("/new_cat/") #adding new categories
def create_category(category: Category):
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO categories (name) VALUES (%s)", (category.name,))
        conn.commit()
    conn.close()
    return {"message": f"Category '{category.name}' created"}

@app.get("/cat/")
def get_categories():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
    conn.close()
    return [{"id": cat[0], "name": cat[1]} for cat in categories]
