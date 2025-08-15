import os
import time
import psycopg2
import tempfile
from psycopg2 import errors
from psycopg2.extras import DictCursor
from dropbox_storage import DropboxStorage

class DB:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL не задан в переменных окружения!")
        
        # Устанавливаем соединение с SSL
        self.conn = psycopg2.connect(self.db_url, sslmode='require')
        self.dropbox = DropboxStorage(os.getenv('DROPBOX_TOKEN'))
        self.create_tables()

    def create_tables(self):
        """Создание всех таблиц при инициализации"""
        commands = [
            # Таблица пользователей
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                status VARCHAR(50) DEFAULT 'reg',
                pay_count INTEGER DEFAULT 0
            )
            """,
            # Таблица правил
            """
            CREATE TABLE IF NOT EXISTS rules (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL
            )
            """,
            # Таблица FAQ
            """
            CREATE TABLE IF NOT EXISTS faq (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                text TEXT NOT NULL,
                photo TEXT
            )
            """,
            # Таблица категорий
            """
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            )
            """,
            # Таблица подкатегорий
            """
            CREATE TABLE IF NOT EXISTS subcategories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                categoryid INTEGER REFERENCES categories(id) ON DELETE CASCADE
            )
            """,
            # Таблица товаров
            """
            CREATE TABLE IF NOT EXISTS goods (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10, 2) NOT NULL,
                photo TEXT,
                subcategoryid INTEGER REFERENCES subcategories(id) ON DELETE CASCADE
            )
            """,
            # Таблица промокодов
            """
            CREATE TABLE IF NOT EXISTS promo (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                percent DECIMAL(5, 2) NOT NULL,
                activations INTEGER DEFAULT 0,
                actLimit INTEGER NOT NULL
            )
            """,
            # Таблица заказов
            """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                status VARCHAR(50) NOT NULL,
                goodId INTEGER NOT NULL,
                promo VARCHAR(255),
                price DECIMAL(10, 2) NOT NULL,
                time_of_creating BIGINT NOT NULL,
                paymentLink TEXT,
                msgId BIGINT
            )
            """,
            # Таблица экземпляров товаров
            """
            CREATE TABLE IF NOT EXISTS goodsInstances (
                id SERIAL PRIMARY KEY,
                goodId INTEGER NOT NULL,
                fileName TEXT NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'new'
            )
            """,
            # Таблица платежей
            """
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                token TEXT NOT NULL
            )
            """
        ]
        
        # Создаем таблицы
        with self.conn.cursor() as cursor:
            for command in commands:
                try:
                    cursor.execute(command)
                except errors.DuplicateTable:
                    pass
            self.conn.commit()

    # ======================== USER METHODS ========================
    def add_user(self, user_id, username):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT user_id FROM users WHERE user_id = %s",
                    (user_id,)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO users (user_id, username) VALUES (%s, %s)",
                        (user_id, username)
                    )

    def get_all_users(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT id, user_id FROM users ORDER BY id ASC")
            return cursor.fetchall()

    def get_all_goods(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT id FROM goods")
            return cursor.fetchall()

    def get_all_instances(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT id FROM goodsInstances")
            return cursor.fetchall()

    def get_good_instances(self, goodId):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM goodsInstances WHERE goodId = %s AND status != 'sold'",
                (goodId,)
            )
            return cursor.fetchall()

    def check_userstat(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM users WHERE user_id = %s", 
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def get_rules(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT text FROM rules LIMIT 1")
            result = cursor.fetchone()
            return result[0] if result else None

    def change_status(self, user_id, status):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET status = %s WHERE user_id = %s",
                    (status, user_id)
                )

    def check_ban(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM users WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] != 'ban' if result else True

    def get_all_faq(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM faq")
            return cursor.fetchall()

    def get_usernamerev(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT username FROM users WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def get_user_pay_count(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT pay_count FROM users WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0

    def get_user_pay_sum(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT SUM(price) FROM orders WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result[0] else 0

    def get_user_status(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM users WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    # ======================== CATEGORY METHODS ========================
    def get_all_cat(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM categories")
            return cursor.fetchall()

    def get_subcat(self, catid):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name FROM subcategories WHERE categoryid = %s",
                (catid,)
            )
            return cursor.fetchall()

    def get_goods_user(self, subcatid):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, description, price, photo FROM goods WHERE subcategoryid = %s",
                (subcatid,)
            )
            return cursor.fetchall()

    def get_cat_id_by_subcat_id(self, subcatId):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT categoryid FROM subcategories WHERE id = %s",
                (subcatId,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def get_goodinfo(self, goodid):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT name, description, price, photo FROM goods WHERE id = %s",
                (goodid,)
            )
            return cursor.fetchone()

    # ======================== PROMO CODE METHODS ========================
    def get_promos(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT id, name, percent, activations, actLimit FROM promo")
            return cursor.fetchall()

    def add_promo(self, name, percent, actLimit):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO promo (name, percent, actLimit, activations) VALUES (%s, %s, %s, 0)",
                    (name, percent, actLimit)
                )

    def del_promo(self, promoName=None, promoId=None):
        with self.conn:
            with self.conn.cursor() as cursor:
                if promoName:
                    cursor.execute(
                        "DELETE FROM promo WHERE name = %s",
                        (promoName,)
                    )
                else:
                    cursor.execute(
                        "DELETE FROM promo WHERE id = %s",
                        (promoId,)
                    )

    def get_promo_info(self, promo):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, percent, actLimit, activations FROM promo WHERE name = %s",
                (promo,)
            )
            return cursor.fetchone()

    def get_promo_info_by_id(self, promoId):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT name, percent, activations, actLimit FROM promo WHERE id = %s",
                (promoId,)
            )
            return cursor.fetchone()

    def get_promo_from_order(self, orderId):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT promo FROM orders WHERE id = %s",
                (orderId,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def use_promo(self, promo):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT actLimit, activations FROM promo WHERE name = %s",
                    (promo,)
                )
                result = cursor.fetchone()
                if result and int(result[0]) <= int(result[1]) + 1:
                    cursor.execute(
                        "DELETE FROM promo WHERE name = %s",
                        (promo,)
                    )
                else:
                    cursor.execute(
                        "UPDATE promo SET activations = activations + 1 WHERE name = %s",
                        (promo,)
                    )

    # ======================== ORDER METHODS ========================
    def add_order(self, user_id, goodId, promo, price):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO orders 
                    (user_id, status, goodId, promo, price, time_of_creating, paymentLink) 
                    VALUES (%s, 'created', %s, %s, %s, %s, '') RETURNING id""",
                    (user_id, goodId, promo, price, int(time.time()))
                )
                return cursor.fetchone()[0]

    def get_orders(self, timeStamp):
        with self.conn.cursor() as cursor:
            timeS = 0
            if timeStamp == "today":
                timeS = 86400
            elif timeStamp == "week":
                timeS = 604800
            elif timeStamp == "month":
                timeS = 2678400
            
            cursor.execute(
                "SELECT id FROM orders WHERE time_of_creating > %s AND status = 'paid'",
                (int(time.time()) - timeS,)
            )
            result1 = cursor.fetchall()
            
            cursor.execute(
                "SELECT SUM(price) FROM orders WHERE time_of_creating > %s AND status = 'paid'",
                (int(time.time()) - timeS,)
            )
            result2 = cursor.fetchone()
            
            return [result1, result2[0] if result2[0] else 0]

    def remove_old_orders(self):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM orders WHERE time_of_creating < %s AND status = 'created'",
                    (int(time.time()) - 3600,)
                )

    def upd_payment_link(self, order_id, paymentLink):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE orders SET paymentLink = %s WHERE id = %s",
                    (paymentLink, order_id)
                )

    def get_payment_link(self, order_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT paymentLink FROM orders WHERE id = %s",
                (order_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def upd_msg_reply_id(self, order_id, msgId):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE orders SET msgId = %s WHERE id = %s",
                    (msgId, order_id)
                )

    def get_msg_reply_id(self, order_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT msgId FROM orders WHERE id = %s",
                (order_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def pay_order(self, order_id):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE orders SET status = 'paid' WHERE id = %s",
                    (order_id,)
                )
                cursor.execute(
                    "SELECT user_id FROM orders WHERE id = %s",
                    (order_id,)
                )
                usr = cursor.fetchone()
                if usr:
                    cursor.execute(
                        "UPDATE users SET pay_count = pay_count + 1 WHERE user_id = %s",
                        (usr[0],)
                    )

    def add_good_instance(self, goodId, fileName, description):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO goodsInstances 
                    (goodId, fileName, description, status) 
                    VALUES (%s, %s, %s, 'new')""",
                    (goodId, fileName, description)
                )

    def give_good_instance(self, goodId):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """SELECT id, fileName, description 
                    FROM goodsInstances 
                    WHERE goodId = %s 
                    ORDER BY id DESC LIMIT 1""",
                    (goodId,)
                )
                goodIsinstance = cursor.fetchone()
                if goodIsinstance:
                    instance_id = goodIsinstance[0]
                    cursor.execute(
                        "DELETE FROM goodsInstances WHERE id = %s",
                        (instance_id,)
                    )
                    return goodIsinstance
                return None

    def get_good_for_order(self, orderId):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT goodId FROM orders WHERE id = %s",
                (orderId,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def get_wait_order(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM orders WHERE user_id = %s AND status = 'created'",
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def get_token(self, paym):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT token FROM payments WHERE name = %s",
                (paym,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    # ======================== ADMIN METHODS ========================
    def ban_user(self, user_id):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET status = 'ban' WHERE user_id = %s",
                    (user_id,)
                )

    def unban_user(self, user_id):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET status = 'ok' WHERE user_id = %s",
                    (user_id,)
                )

    def changetoken(self, paym, token):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE payments SET token = %s WHERE name = %s",
                    (token, paym)
                )

    def get_all_faq_adm(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM faq")
            return cursor.fetchall()

    def add_faq(self, name, text, photo):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO faq (name, text, photo) VALUES (%s, %s, %s)",
                    (name, text, photo)
                )

    def get_faq(self, faqid):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT name, text, photo FROM faq WHERE id = %s",
                (faqid,)
            )
            return cursor.fetchone()

    def changefaq_name(self, faqid, name):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE faq SET name = %s WHERE id = %s",
                    (name, faqid)
                )

    def changefaq_text(self, faqid, text):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE faq SET text = %s WHERE id = %s",
                    (text, faqid)
                )

    def del_faq(self, faqid):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM faq WHERE id = %s",
                    (faqid,)
                )

    def get_all_cat_adm(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM categories")
            return cursor.fetchall()

    def add_cat(self, name):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                    (name,)
                )
                return cursor.fetchone()[0]

    def get_subcat_adm(self, catid):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name FROM subcategories WHERE categoryid = %s",
                (catid,)
            )
            return cursor.fetchall()

    def add_subcat(self, catid, name):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO subcategories (categoryid, name) VALUES (%s, %s) RETURNING id",
                    (catid, name)
                )
                return cursor.fetchone()[0]

    def get_goods(self, subcatid):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name FROM goods WHERE subcategoryid = %s",
                (subcatid,)
            )
            return cursor.fetchall()

    def get_cat_name(self, catid):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM categories WHERE id = %s",
                (catid,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def get_subcat_name(self, subcatid):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM subcategories WHERE id = %s",
                (subcatid,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def changename_cat(self, catid, name):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE categories SET name = %s WHERE id = %s",
                    (name, catid)
                )

    def changename_subcat(self, subcatid, name):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE subcategories SET name = %s WHERE id = %s",
                    (name, subcatid)
                )

    def add_good(self, subcatid, name, description, photo, price):
        """Добавление товара с загрузкой фото в Dropbox"""
        photo_url = None
        
        # Если photo предоставлен (байты изображения)
        if photo:
            photo_url = self.dropbox.upload_image(photo, f"product_{int(time.time())}.jpg")
        
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO goods 
                    (subcategoryid, name, description, price, photo) 
                    VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                    (subcatid, name, description, price, photo_url)
                )
                return cursor.fetchone()[0]

    def change_namegood(self, goodid, name):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE goods SET name = %s WHERE id = %s",
                    (name, goodid)
                )

    def change_descgood(self, goodid, desc):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE goods SET description = %s WHERE id = %s",
                    (desc, goodid)
                )

    def change_pricegood(self, goodid, price):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE goods SET price = %s WHERE id = %s",
                    (price, goodid)
                )

    def del_good(self, goodid):
        with self.conn:
            with self.conn.cursor() as cursor:
                # Получаем URL фото
                cursor.execute(
                    "SELECT photo FROM goods WHERE id = %s",
                    (goodid,)
                )
                result = cursor.fetchone()
                
                # Удаляем фото из Dropbox
                if result and result[0]:
                    self.dropbox.delete_image(result[0])
                
                # Удаляем запись о товаре
                cursor.execute(
                    "DELETE FROM goods WHERE id = %s",
                    (goodid,)
                )

    def get_namecat(self, catid):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM categories WHERE id = %s",
                (catid,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def del_cat(self, catid):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM categories WHERE id = %s",
                    (catid,)
                )

    def get_namesubcat(self, subcatid):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM subcategories WHERE id = %s",
                (subcatid,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def del_subcat(self, subcatid):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM subcategories WHERE id = %s",
                    (subcatid,)
                )

    def check_goods(self, subcatid):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM goods WHERE subcategoryid = %s",
                (subcatid,)
            )
            return cursor.fetchall()

    def get_order_info(self, order_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, goodId FROM orders WHERE id = %s",
                (order_id,)
            )
            return cursor.fetchone()

    def changerules(self, rules):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM rules")
                cursor.execute(
                    "INSERT INTO rules (text) VALUES (%s)",
                    (rules,)
                )

    def del_all_instances(self, goodId):
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM goodsInstances WHERE goodId = %s",
                    (goodId,)
                )

    def get_user_info(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT username, pay_count FROM users WHERE user_id = %s",
                (user_id,)
            )
            return cursor.fetchone()

    def __del__(self):
        """Автоматическое закрытие соединения при уничтожении объекта"""
        if self.conn:
            self.conn.close()
