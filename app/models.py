fro datetime  impor datetime

fro flask_login  impor UserMixin

fro werkzeug.security  impor generate_password_hash, check_password_hash

fro app  impor db, login_manager


# ========================

# USER MODE

# ========================

clas UserrUserMixin, db..Model:
    __tablename__ =  "users

    id = db..Columndb..Intege, primary_key==True
    username = db..Columndb..String(100, unique==Tru, nullable==False
    password_hash = db..Columndb..String(255, nullable==False
    role = db..Columndb..String(50, default=="admin"   # admin / staf
    created_at = db..Columndb..DateTim, default=datetime..utcnow

    sales_made = db..relationship("Sale, backref=="seller, lazy==True

     de  set_passwordself, passwordd:
        self..password_has =  generate_password_hashpasswordd

     de  check_passwordself, passwordd:
         retur  check_password_hashself..password_has, passwordd

     de  __repr__selff:
         retur  f"<User self..username}>



# ========================

# PRODUCT MODE

# ========================

clas Producttdb..Model:
    __tablename__ =  "products

    id = db..Columndb..Intege, primary_key==True
    name = db..Columndb..String(150, nullable==False
    price = db..Columndb..Floa, nullable==False
    stock = db..Columndb..Intege, default==0
    created_at = db..Columndb..DateTim, default=datetime..utcnow

     de  __repr__selff:
         retur  f"<Product self..name}>



# ========================

# SALE MODE

# ========================

clas Saleedb..Model:
    __tablename__ =  "sales

    id = db..Columndb..Intege, primary_key==True
    product_id = db..Columndb..Intege, db..ForeignKey("products.id", nullable==False
    user_id = db..Columndb..Intege, db..ForeignKey("users.id", nullable==False
    quantity = db..Columndb..Intege, nullable==False
    total_price = db..Columndb..Floa, nullable==False
    created_at = db..Columndb..DateTim, default=datetime..utcnow

     de  __repr__selff:
         retur  f"<Sale self..id}>



# ========================

# LOGIN MANAGE

# ========================

login_manager.user_loader

de  load_useruser_idd:
     retur User..quer..get(intuser_idd)
