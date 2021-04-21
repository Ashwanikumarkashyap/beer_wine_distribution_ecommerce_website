from flask import Flask, session, g, render_template, request, make_response
import pymongo
import urllib.parse
from bson.json_util import dumps
from bson.objectid import ObjectId
import math
import json
import bcrypt

app = Flask(__name__)

username = urllib.parse.quote("admin")
password = urllib.parse.quote("admin")
url = "mongodb+srv://" + username + ":" + password + "@cluster0.riul3.mongodb.net/beer_wine_website?retryWrites=true&w=majority"
cluster = pymongo.MongoClient(url)
db = cluster["beer_wine_website"]

# PAGE RENDERS

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/sign_up")
def sign_up():
    return render_template('signup.html')

@app.route("/sign_in")
def sign_in():
    return render_template('signin.html')

# POST FUNCTIONS

# completed
@app.route("/val_sign_up", methods=["POST"])
def val_sign_up():
    
    user_name = request.args.get("user_name")
    full_name = request.args.get("full_name")
    email_id = request.args.get("email_id")
    password = request.args.get("password")
    address = request.args.get("address")
    contact_no = request.args.get("contact_no")
    govt_id = request.args.get("govt_id")

    collection = db["customer_details"]

    if collection.find_one({"user_name": user_name}):
        return json.dumps({"status": "failed", "message": "username already exists"})
    if collection.find_one({"email_id": email_id}):
        return json.dumps({"status": "failed", "message": "email address already exists"})
    if collection.find_one({"contact_no": contact_no}):
        return json.dumps({"status": "failed", "message": "contact no already exists"})
    if collection.find_one({"govt_id": govt_id}):
        return json.dumps({"status": "failed", "message": "govt_id already exists"})

    try:

        collection.insert_one({
            "user_name": user_name,
            "full_name": full_name,
            "email_id": email_id,
            "password": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()),
            "address": address,
            "contact_no": contact_no,
            "govt_id": govt_id,
            "isAdmin": False
        })
        res = make_response(json.dumps({"status": "success"}))
        res.set_cookie(
            "data",
            max_age=3600,
            expires=None,
            path=request.path,
            domain=None,
            secure=False
        )
        return res

    except:
        return json.dumps({"status": "failed"})

# completed
@app.route("/val_sign_in", methods=["POST"])
def val_sign_in():

    user_name = request.args.get("user_name")
    password = request.args.get("password")

    collection = db["customer_details"]

    db_check = collection.find_one({"user_name": user_name})

    if db_check and bcrypt.checkpw(password.encode("utf-8"), db_check["password"]):
        res = make_response(json.dumps({
            "status": "success",
        }))
        res.set_cookie(
            "data",
            max_age=3600,
            expires=None,
            path=request.path,
            domain=None,
            secure=False
        )
        return res
    
    return json.dumps({"status": "failed"})

# completed
@app.route("/add_to_products", methods=["POST"])
def add_to_products():

    brand = request.args.get("brand")
    description = request.args.get("description")
    stock = request.args.get("stock")
    category = request.args.get("category")
    price = request.args.get("price")
    images = request.args.getlist("images")

    collection = db["product_details"]

    try:

        collection.insert_one({
            "brand": brand,
            "description": description,
            "stock": int(stock),
            "category": category,
            "price": float(price),
            "images": images
        })

        return json.dumps({"status": "success"})

    except:
        return json.dumps({"status": "failed"})

# POST/PUT FUNCTIONS

# completed
@app.route("/add_to_wishlist", methods=["POST", "PUT"])
def add_to_wishlist():

    customer_id = request.args.get("customer_id")
    product_id = request.args.get("product_id")

    collection = db["wishlist"]

    db_check = collection.find_one({"customer_id": customer_id})

    try:

        if db_check:
            collection.update_one({"customer_id": customer_id}, 
            {"$set": {"product_ids": list(set(db_check["product_ids"] + [product_id]))}})
        else:
            collection.insert_one({
                "customer_id": customer_id,
                "product_ids": [product_id]
            })

        return json.dumps({"status": "success"})
    
    except:
        return json.dumps({"status": "failed"})

# completed
@app.route("/add_to_cart", methods=["POST", "PUT"])
def add_to_cart():
    
    customer_id = request.args.get("customer_id")
    product_id = request.args.get("product_id")
    quantity = request.args.get("quantity")

    collection = db["cart"]

    db_check = collection.find_one({"customer_id": customer_id})

    try:

        if db_check:
            total_price = db_check["total_price"]
            total_price += float(db["product_details"].find_one({"_id": ObjectId(product_id)})["price"]) * float(quantity)
            collection.update_one({"customer_id": customer_id}, 
                                  {"$set": {"product_ids": list(db_check["product_ids"] + [{"product_id": product_id, "quantity": int(quantity)}]),
                                            "total_price": total_price}})
        else:
            collection.insert_one({
                "customer_id": customer_id,
                "product_ids": [{"product_id": product_id, "quantity": int(quantity)}],
                "total_price": float(db["product_details"].find_one({"_id": ObjectId(product_id)})["price"]) * float(quantity)
            })

        return json.dumps({"status": "success"})
    
    except:
        return json.dumps({"status": "failed"})

# completed
@app.route("/rem_from_wishlist", methods=["PUT"])
def rem_from_wishlist():

    customer_id = request.args.get("customer_id")
    product_id = request.args.get("product_id")

    collection = db["wishlist"]

    db_check = collection.find_one({"customer_id": customer_id})

    try:
        if db_check:
            if product_id in db_check["product_ids"]:
                temp_product_ids = db_check["product_ids"]
                temp_product_ids.remove(product_id)
                collection.update_one({"customer_id": customer_id}, 
                                      {"$set": {"product_ids": list(set(temp_product_ids))}})
            else:
                return json.dumps({"status": "failed"})
        else:
            return json.dumps({"status": "failed", "message": "customer id not found"})
        return json.dumps({"status": "success"})
    except:
        return json.dumps({"status": "failed"})

# completed
@app.route("/rem_from_cart", methods=["PUT"])
def rem_from_cart():

    customer_id = request.args.get("customer_id")
    product_id = request.args.get("product_id")

    collection = db["cart"]

    db_check = collection.find_one({"customer_id": customer_id})

    try:
        if db_check:
            current_total_price = float(db_check["total_price"])
            product_ids = [entry["product_id"] for entry in db_check["product_ids"]]
            if product_id in product_ids:
                temp_product_ids = db_check["product_ids"]
                price_of_removed_product, updated_product_ids = 0, []
                for entry in temp_product_ids:
                    if entry.get("product_id") == product_id:
                        price_of_removed_product = float(db["product_details"].find_one({"_id": ObjectId(product_id)})["price"]) * entry.get("quantity")
                    else:
                        updated_product_ids.append(entry)
                collection.update_one({"customer_id": customer_id}, 
                                      {"$set": {"product_ids": updated_product_ids,
                                                "total_price": current_total_price - price_of_removed_product}})
            else:
                return json.dumps({"status": "failed"})
        else:
            return json.dumps({"status": "failed", "message": "customer id not found"})
        return json.dumps({"status": "success"})
    except:
        return json.dumps({"status": "failed"})

# incomplete
@app.route("/proceed_to_checkout", methods=["POST"])
def proceed_to_checkout():

    customer_id = request.args.get("customer_id")

    pass

# completed
@app.route("/update_product_details", methods=["PUT"])
def update_product_details():
    
    product_id = request.args.get("product_id")

    brand = request.args.get("brand")
    description = request.args.get("description")
    stock = request.args.get("stock")
    category = request.args.get("category")
    price = request.args.get("price")
    images = request.args.getlist("images")

    collection = db["product_details"]

    db_check = collection.find_one({"_id": ObjectId(product_id)})

    try:

        if db_check:

            if brand:
                collection.update_one({"_id": ObjectId(product_id)}, 
                                    {"$set": {"brand": brand}})
            if description:
                collection.update_one({"_id": ObjectId(product_id)}, 
                                    {"$set": {"description": description}})
            if stock:
                collection.update_one({"_id": ObjectId(product_id)}, 
                                    {"$set": {"stock": int(stock)}})
            if category:
                collection.update_one({"_id": ObjectId(product_id)}, 
                                    {"$set": {"category": category}})
            if images:
                collection.update_one({"_id": ObjectId(product_id)}, 
                                    {"$set": {"images": images}})
            if price:
                price_change = float(price) - float(db_check["price"])
                collection.update_one({"_id": ObjectId(product_id)}, 
                                    {"$set": {"price": float(price)}})

                # put the change in everyones cart who has the updated product_id 
                for entry in db["cart"].find():
                    for product_data in entry["product_ids"]:
                        if product_data["product_id"] == product_id:
                            db["cart"].update_one({"_id": ObjectId(entry["_id"])}, 
                                                {"$set": {"total_price": float(entry["total_price"]) + price_change * product_data["quantity"]}})

            return json.dumps({"status": "success"})

        else:
            return json.dumps({"status": "failed", "message": "product id not found"})
    
    except:
        return json.dumps({"status": "failed"})

# DELETE FUNCTIONS

# completed
@app.route("/clear_wishlist", methods=["DELETE"])
def empty_wishlist():

    customer_id = request.args.get("customer_id")

    collection = db["wishlist"]

    try:
        collection.delete_one({"customer_id": customer_id})
        return json.dumps({"status": "success"})
    except:
        return json.dumps({"status": "failed"})

# completed
@app.route("/clear_cart", methods=["DELETE"])
def empty_cart():
    
    customer_id = request.args.get("customer_id")

    collection = db["cart"]

    try:
        collection.delete_one({"customer_id": customer_id})
        return json.dumps({"status": "success"})
    except:
        return json.dumps({"status": "failed"})

# completed
@app.route("/rem_from_products", methods=["DELETE"])
def rem_from_products():
    
    product_id = request.args.get("product_id")

    collection = db["product_details"]

    db_check = collection.find_one({"_id": ObjectId(product_id)})

    try:

        if db_check:

            product_price = db_check["price"]
            collection.delete_one({"_id": ObjectId(product_id)})

            # put the change in everyones cart who has the updated product_id 
            for entry in db["cart"].find():
                updated_product_ids, product_id_found = [], False
                for product_data in entry["product_ids"]:
                    if product_data["product_id"] == product_id:   
                        product_id_found = True
                        db["cart"].update_one({"_id": ObjectId(entry["_id"])}, 
                                            {"$set": {"total_price": float(entry["total_price"]) - product_price * product_data["quantity"]}})
                    else:
                        updated_product_ids.append(product_data)
                if product_id_found:
                    db["cart"].update_one({"_id": ObjectId(entry["_id"])}, 
                                          {"$set": {"product_ids": updated_product_ids}})

            return json.dumps({"status": "success"})

        else:
            return json.dumps({"status": "failed", "message": "product id not found"})
    
    except:
        return json.dumps({"status": "failed"})

# GET FUNCTIONS

# completed (contains options to filter by category, min price, max price)
@app.route("/get_products", methods=["GET"])
def get_products():

    category = request.args.get("category")
    price_min = request.args.get("price_min")
    price_max = request.args.get("price_max")

    if not category:
        category = {"$exists": True}
    if not price_min:
        price_min = 0
    if not price_max:
        price_max = math.pow(10, 4)

    products = db["product_details"]
    return dumps(list(products.find({"category": category, "price": {"$gte": price_min, "$lte": price_max}})))

# completed
@app.route("/get_cart", methods=["GET"])
def get_cart():
    customer_id = request.args.get("customer_id")
    cart = db["cart"]
    return dumps(list(cart.find({"customer_id": customer_id})))

# completed
@app.route("/get_wishlist", methods=["GET"])
def get_wishlist():
    customer_id = request.args.get("customer_id")
    wishlist = db["wishlist"]
    return dumps(list(wishlist.find({"customer_id": customer_id})))

# completed
@app.route("/get_orders", methods=["GET"])
def get_orders():
    customer_id = request.args.get("customer_id")
    orders = db["orders"]
    return dumps(list(orders.find({"customer_id": customer_id})))

if __name__ == "__main__":
    app.run()   