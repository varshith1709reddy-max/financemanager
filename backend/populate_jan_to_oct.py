import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import get_db_path

def populate_database(db_path=None):
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Ensure Student Categories Exist
    student_categories = [
        # Income
        ("Pocket Money / Parents Allowance", "income", "#10B981", "cash"),
        ("Freelance & Part-time Tutoring", "income", "#059669", "briefcase"),
        ("College Stipend & Awards", "income", "#34D399", "award"),
        ("Cash Gift / Festival", "income", "#6EE7B7", "gift"),
        
        # Expense
        ("College Canteen & Mess", "expense", "#F59E0B", "coffee"),
        ("Snacks, Swiggy & Zomato", "expense", "#F97316", "shopping-cart"),
        ("Books, Xerox & Stationery", "expense", "#6366F1", "book"),
        ("Hostel / PG Room Rent", "expense", "#EF4444", "home"),
        ("Metro, Bus & Bike Petrol", "expense", "#3B82F6", "truck"),
        ("Mobile Recharge & Internet", "expense", "#0EA5E9", "zap"),
        ("Movies & Hangouts with Friends", "expense", "#EC4899", "film"),
        ("College Fest & Lab Materials", "expense", "#8B5CF6", "tag"),
        ("Miscellaneous", "expense", "#6B7280", "archive"),
    ]

    cur.execute("DELETE FROM categories WHERE user_id IS NULL;")
    for name, c_type, color, icon in student_categories:
        cur.execute("""
            INSERT INTO categories (name, type, color, icon, user_id)
            VALUES (?, ?, ?, ?, NULL);
        """, (name, c_type, color, icon))

    cur.execute("SELECT id, name, type FROM categories WHERE user_id IS NULL;")
    cat_map = {r["name"]: r["id"] for r in cur.fetchall()}

    # All users to populate
    cur.execute("SELECT id, username, full_name FROM users;")
    users = cur.fetchall()

    months = [f"2026-{m:02d}" for m in range(1, 11)]

    for user in users:
        u_id = user["id"]
        cur.execute("UPDATE users SET currency = 'INR' WHERE id = ?;", (u_id,))

        # Clear existing transactions, budgets, goals, accounts for clean 10-month dataset
        cur.execute("DELETE FROM transactions WHERE user_id = ?;", (u_id,))
        cur.execute("DELETE FROM budgets WHERE user_id = ?;", (u_id,))
        cur.execute("DELETE FROM savings_goals WHERE user_id = ?;", (u_id,))
        cur.execute("DELETE FROM accounts WHERE user_id = ?;", (u_id,))

        # 2. Student Accounts with initial balances
        student_accounts = [
            ("SBI Student Savings Account", "savings", 5000.0, "SBI-8812"),
            ("GPay / PhonePe UPI Wallet", "checking", 1500.0, "UPI-4144"),
            ("Cash in Pocket", "cash", 600.0, "CASH")
        ]

        acc_map = {}
        for acc_name, acc_type, init_b, num in student_accounts:
            cur.execute("""
                INSERT INTO accounts (user_id, name, type, balance, initial_balance, currency, account_number)
                VALUES (?, ?, ?, ?, ?, 'INR', ?);
            """, (u_id, acc_name, acc_type, init_b, init_b, num))
            acc_map[acc_name] = cur.lastrowid

        sbi = acc_map["SBI Student Savings Account"]
        upi = acc_map["GPay / PhonePe UPI Wallet"]
        cash = acc_map["Cash in Pocket"]

        # 3. Monthly Transactions Jan-Oct 2026
        # Format: (account, to_account, category_name, type, amount, day, description, notes, tags)
        monthly_data = {
            "2026-01": [
                (sbi, None, "Pocket Money / Parents Allowance", "income", 11000.0, "01", "Semester 4 Pocket Money from Dad", "Semester start allowance", "pocket-money"),
                (sbi, upi, None, "transfer", 2800.0, "02", "Transfer to GPay for Monthly UPI Spend", "UPI budget", "transfer"),
                (upi, cash, None, "transfer", 500.0, "03", "Cash Withdrawal for Local Travel & Xerox", "Cash buffer", "transfer"),
                (sbi, None, "Hostel / PG Room Rent", "expense", 4500.0, "02", "PG Room Rent (Shared)", "Rent with electricity", "rent,pg"),
                (upi, None, "Books, Xerox & Stationery", "expense", 650.0, "04", "DBMS & OS Reference Books", "Used textbooks from senior", "books"),
                (upi, None, "Metro, Bus & Bike Petrol", "expense", 500.0, "05", "Metro Smart Card Recharge", "Monthly commute", "metro"),
                (cash, None, "College Canteen & Mess", "expense", 70.0, "08", "Canteen Samosa & Masala Tea", "Break snacks with friends", "canteen"),
                (upi, None, "College Canteen & Mess", "expense", 110.0, "12", "College Canteen Lunch Thali", "Afternoon lunch", "canteen"),
                (cash, None, "Books, Xerox & Stationery", "expense", 140.0, "15", "Lab Record Sheets & Files", "Stationery store", "stationery"),
                (upi, None, "College Canteen & Mess", "expense", 85.0, "18", "Canteen Masala Dosa & Chai", "Morning breakfast", "canteen"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 260.0, "21", "Swiggy Hostel Dinner with Roommates", "Late night study food", "food"),
                (upi, None, "Movies & Hangouts with Friends", "expense", 320.0, "26", "Republic Day Blockbuster Movie", "Multiplex ticket with classmates", "movie"),
                (upi, None, "College Canteen & Mess", "expense", 95.0, "28", "Canteen Cold Coffee & Sandwich", "Evening snack", "canteen")
            ],
            "2026-02": [
                (sbi, None, "Pocket Money / Parents Allowance", "income", 10000.0, "01", "Monthly Pocket Money from Home", "Monthly allowance", "pocket-money"),
                (sbi, None, "Freelance & Part-time Tutoring", "income", 2500.0, "10", "Python & C++ Tutoring for Junior", "Weekend coding tuition", "tutoring"),
                (sbi, upi, None, "transfer", 2800.0, "02", "Transfer to UPI for Daily Expenses", "UPI wallet refill", "transfer"),
                (upi, cash, None, "transfer", 500.0, "04", "Cash in Pocket Buffer", "Wallet buffer", "transfer"),
                (sbi, None, "Hostel / PG Room Rent", "expense", 4500.0, "02", "PG Room Rent", "Monthly room rent", "rent"),
                (upi, None, "Metro, Bus & Bike Petrol", "expense", 500.0, "05", "Metro Card Topup", "Metro commute", "metro"),
                (upi, None, "College Canteen & Mess", "expense", 75.0, "07", "Canteen Idli Vada Breakfast", "Breakfast", "canteen"),
                (upi, None, "College Fest & Lab Materials", "expense", 500.0, "11", "Tech Fest Registration & Hackathon Kit", "College event registration", "fest"),
                (cash, None, "Metro, Bus & Bike Petrol", "expense", 300.0, "13", "Bike Petrol for Commute", "Fuel bunk", "petrol"),
                (cash, None, "Books, Xerox & Stationery", "expense", 95.0, "15", "Mid-term Exam Question Bank Xerox", "Exam xerox", "xerox"),
                (upi, None, "College Canteen & Mess", "expense", 120.0, "18", "Canteen Thali Lunch", "Lunch", "canteen"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 290.0, "21", "Zomato Late Night Study Pizza", "Roommates treat", "food"),
                (cash, None, "Metro, Bus & Bike Petrol", "expense", 80.0, "24", "Auto Fare Share to College", "Auto travel", "travel"),
                (cash, None, "College Canteen & Mess", "expense", 65.0, "26", "Canteen Tea & Cutlet with Batchmates", "Evening snacks", "canteen")
            ],
            "2026-03": [
                (sbi, None, "Pocket Money / Parents Allowance", "income", 10000.0, "01", "Monthly College Pocket Money", "Monthly deposit from parents", "pocket-money"),
                (upi, None, "Cash Gift / Festival", "income", 1500.0, "24", "Holi Festive Gift from Uncle via GPay", "Festival gift money", "gift"),
                (sbi, upi, None, "transfer", 2200.0, "02", "Transfer to GPay Wallet", "Monthly spend limit", "transfer"),
                (upi, cash, None, "transfer", 500.0, "04", "Cash for Local Purchases", "Cash pocket buffer", "transfer"),
                (sbi, None, "Hostel / PG Room Rent", "expense", 4500.0, "02", "PG Room Rent", "Monthly PG fee", "rent"),
                (upi, None, "Metro, Bus & Bike Petrol", "expense", 500.0, "05", "Metro Pass Recharge", "Monthly smart card", "metro"),
                (cash, None, "Books, Xerox & Stationery", "expense", 130.0, "08", "Assignment Sheets & Project Files", "Stationery", "stationery"),
                (upi, None, "College Canteen & Mess", "expense", 110.0, "12", "Canteen Chole Bhature", "Lunch", "canteen"),
                (cash, None, "College Canteen & Mess", "expense", 60.0, "16", "Canteen Coffee & Puff", "Quick snack", "canteen"),
                (cash, None, "Books, Xerox & Stationery", "expense", 115.0, "20", "Mid-Sem Exam Xerox Printouts", "Lecture notes photocopy", "xerox"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 380.0, "23", "Holi Celebration Sweets & Snacks", "Holi snacks with hostel group", "food"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 240.0, "26", "Swiggy Shawarma & Mojito Delivery", "Dinner order", "food"),
                (upi, None, "College Canteen & Mess", "expense", 135.0, "29", "Canteen Fried Rice & Manchurian", "Lunch", "canteen")
            ],
            "2026-04": [
                (sbi, None, "Pocket Money / Parents Allowance", "income", 10000.0, "01", "Monthly Pocket Money from Parents", "Monthly allowance", "pocket-money"),
                (sbi, None, "College Stipend & Awards", "income", 3000.0, "18", "2nd Prize in Inter-College Hackathon", "Cash prize award", "award"),
                (sbi, upi, None, "transfer", 2500.0, "02", "Transfer to UPI Wallet", "Daily expenses budget", "transfer"),
                (upi, cash, None, "transfer", 600.0, "03", "Cash Buffer for Lab Printouts", "Cash", "transfer"),
                (sbi, None, "Hostel / PG Room Rent", "expense", 4500.0, "02", "PG Room Rent", "Monthly PG accommodation", "rent"),
                (upi, None, "Mobile Recharge & Internet", "expense", 719.0, "04", "Jio 3-Month 5G Unlimited Pack", "Quarterly mobile recharge", "recharge"),
                (cash, None, "Books, Xerox & Stationery", "expense", 220.0, "07", "Lab Observation Manual Binding & Xerox", "Lab submission documents", "xerox"),
                (upi, None, "College Canteen & Mess", "expense", 130.0, "10", "Canteen Veg Biryani & Soda", "Lunch with project team", "canteen"),
                (upi, None, "Metro, Bus & Bike Petrol", "expense", 500.0, "14", "Metro Card Recharge", "College commute", "metro"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 420.0, "18", "Celebration Treat for Hackathon Prize", "Pizza treat for teammates", "food"),
                (cash, None, "Metro, Bus & Bike Petrol", "expense", 350.0, "22", "Bike Petrol for Exam Days", "Petrol", "petrol"),
                (cash, None, "Books, Xerox & Stationery", "expense", 160.0, "25", "Semester Project Report Binding", "Hardbound report copy", "stationery"),
                (upi, None, "Movies & Hangouts with Friends", "expense", 310.0, "28", "Movie Outing after Lab Exams", "Cinema ticket", "movie")
            ],
            "2026-05": [
                (sbi, None, "Pocket Money / Parents Allowance", "income", 9000.0, "01", "Exam Month & Vacation Travel Allowance", "Allowance", "pocket-money"),
                (sbi, upi, None, "transfer", 2000.0, "02", "Transfer to UPI for May", "UPI", "transfer"),
                (upi, cash, None, "transfer", 400.0, "04", "Cash in Pocket for Hometown Journey", "Travel cash buffer", "transfer"),
                (sbi, None, "Hostel / PG Room Rent", "expense", 4500.0, "02", "PG Room Rent & Advance", "Monthly rent", "rent"),
                (cash, None, "Books, Xerox & Stationery", "expense", 180.0, "06", "University Exam Hall Ticket & Stationery", "Pens, ruler & hall ticket print", "stationery"),
                (upi, None, "College Canteen & Mess", "expense", 85.0, "10", "Canteen Cold Drink & Sandwich", "Quick exam break", "canteen"),
                (upi, None, "College Canteen & Mess", "expense", 110.0, "15", "Canteen Thali after Final Exam", "Last day lunch", "canteen"),
                (upi, None, "Metro, Bus & Bike Petrol", "expense", 680.0, "20", "Bus Ticket to Hometown for Vacation", "Interstate travel", "travel"),
                (cash, None, "Snacks, Swiggy & Zomato", "expense", 140.0, "21", "Travel Snacks & Mineral Water", "Bus journey refreshments", "food"),
                (upi, None, "Movies & Hangouts with Friends", "expense", 190.0, "27", "Ice Cream & Falooda with Hometown Friends", "Vacation hangout", "food")
            ],
            "2026-06": [
                (sbi, None, "Pocket Money / Parents Allowance", "income", 6000.0, "01", "Vacation Pocket Money from Parents", "Vacation allowance", "pocket-money"),
                (sbi, None, "Freelance & Part-time Tutoring", "income", 4000.0, "15", "Summer Web Development Stipend", "Freelance frontend project", "tutoring"),
                (sbi, upi, None, "transfer", 2000.0, "02", "Transfer to GPay Wallet", "UPI budget", "transfer"),
                (upi, cash, None, "transfer", 300.0, "05", "Cash in Pocket", "Cash buffer", "transfer"),
                (upi, None, "Books, Xerox & Stationery", "expense", 499.0, "05", "Udemy Python & Data Structures Course", "Summer upskilling certification", "books"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 220.0, "10", "Cafe Coffee & Coding Session", "Work cafe visit", "food"),
                (upi, None, "Books, Xerox & Stationery", "expense", 380.0, "16", "Secondhand Algorithm Reference Book", "Technical book purchase", "books"),
                (upi, None, "Metro, Bus & Bike Petrol", "expense", 400.0, "20", "Metro Smart Card for Internship Commute", "Internship commute", "metro"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 180.0, "24", "Swiggy Burger & Beverage", "Evening snack", "food"),
                (cash, None, "Movies & Hangouts with Friends", "expense", 120.0, "28", "Chaat & Juices with School Batchmates", "Street food hangout", "food")
            ],
            "2026-07": [
                (sbi, None, "Pocket Money / Parents Allowance", "income", 12000.0, "01", "Semester 5 Pocket Money & New Books Budget", "Semester start allowance from Dad", "pocket-money"),
                (sbi, upi, None, "transfer", 3500.0, "02", "Transfer to GPay for Semester Start", "UPI budget", "transfer"),
                (upi, cash, None, "transfer", 900.0, "03", "Cash Withdrawal for Books & Records", "Cash", "transfer"),
                (sbi, None, "Hostel / PG Room Rent", "expense", 4500.0, "02", "PG Room Rent (Semester 5)", "PG rent", "rent"),
                (upi, None, "Mobile Recharge & Internet", "expense", 719.0, "04", "Jio 5G 3-Month Plan", "Unlimited student 5G data", "recharge"),
                (cash, None, "Books, Xerox & Stationery", "expense", 750.0, "05", "Core Engineering Textbooks & Record Books", "New semester stationery", "books"),
                (upi, None, "Metro, Bus & Bike Petrol", "expense", 500.0, "08", "Metro Monthly Student Card Recharge", "Daily commute", "metro"),
                (cash, None, "College Canteen & Mess", "expense", 80.0, "11", "Canteen Tea & Samosa Welcome Snacks", "Canteen", "canteen"),
                (upi, None, "College Canteen & Mess", "expense", 110.0, "15", "College Canteen South Indian Meals", "Lunch", "canteen"),
                (upi, None, "College Fest & Lab Materials", "expense", 350.0, "19", "Fresher Welcome Party Batch Contribution", "Fresher welcome fund", "fest"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 270.0, "23", "Zomato Biryani Night with Batchmates", "Hostel weekend dinner", "food"),
                (cash, None, "Metro, Bus & Bike Petrol", "expense", 300.0, "27", "Bike Petrol Refill", "Commute", "petrol"),
                (upi, None, "College Canteen & Mess", "expense", 90.0, "30", "Canteen Cold Coffee & Puff", "Snacks", "canteen")
            ],
            "2026-08": [
                (sbi, None, "Pocket Money / Parents Allowance", "income", 10000.0, "01", "Monthly Pocket Money from Dad", "Allowance", "pocket-money"),
                (upi, None, "Cash Gift / Festival", "income", 2000.0, "28", "Raksha Bandhan & Birthday Cash Gift", "Family festive gift", "gift"),
                (sbi, upi, None, "transfer", 2500.0, "02", "Transfer to UPI Wallet", "UPI budget", "transfer"),
                (upi, cash, None, "transfer", 600.0, "03", "Cash in Pocket Buffer", "Cash buffer", "transfer"),
                (sbi, None, "Hostel / PG Room Rent", "expense", 4500.0, "02", "PG Room Rent", "Monthly room rent", "rent"),
                (upi, None, "Metro, Bus & Bike Petrol", "expense", 500.0, "05", "Metro Card Topup", "Travel", "metro"),
                (cash, None, "Books, Xerox & Stationery", "expense", 140.0, "08", "Assignment Printouts & Spiral Binding", "Assignment copy", "xerox"),
                (upi, None, "College Canteen & Mess", "expense", 110.0, "11", "Canteen Lunch Thali", "Lunch", "canteen"),
                (upi, None, "Movies & Hangouts with Friends", "expense", 280.0, "15", "Independence Day Cafe Outing with Friends", "Holiday hangout", "food"),
                (cash, None, "College Canteen & Mess", "expense", 65.0, "18", "Canteen Samosa & Tea", "Canteen break", "canteen"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 250.0, "22", "Swiggy Hostel Dinner", "Weekend food", "food"),
                (cash, None, "Metro, Bus & Bike Petrol", "expense", 350.0, "25", "Bike Petrol for College Commute", "Fuel bunk", "petrol"),
                (upi, None, "Movies & Hangouts with Friends", "expense", 360.0, "29", "Weekend Blockbuster Movie Ticket & Popcorn", "Cinema with roommates", "movie")
            ],
            "2026-09": [
                (sbi, None, "Pocket Money / Parents Allowance", "income", 10000.0, "01", "Monthly Pocket Money from Home", "Parents monthly transfer", "pocket-money"),
                (sbi, None, "Freelance & Part-time Tutoring", "income", 3000.0, "12", "Maths & Coding Tuition for Class 10", "Part-time tutoring", "tutoring"),
                (sbi, upi, None, "transfer", 2500.0, "02", "Transfer to GPay Wallet", "UPI refill", "transfer"),
                (upi, cash, None, "transfer", 600.0, "04", "Cash in Pocket Buffer", "Cash", "transfer"),
                (sbi, None, "Hostel / PG Room Rent", "expense", 4500.0, "02", "PG Room Rent", "Shared hostel room", "rent"),
                (upi, None, "Movies & Hangouts with Friends", "expense", 200.0, "05", "Teachers Day Gift & Cake Contribution", "Class celebration contribution", "fest"),
                (upi, None, "Metro, Bus & Bike Petrol", "expense", 500.0, "06", "Metro Card Recharge", "Metro commute", "metro"),
                (cash, None, "Books, Xerox & Stationery", "expense", 160.0, "09", "Operating Systems Lab Manual & Notes Xerox", "Lab xerox", "xerox"),
                (upi, None, "College Canteen & Mess", "expense", 90.0, "13", "Canteen Dosa & Filter Coffee", "Breakfast", "canteen"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 280.0, "17", "Swiggy Pizza with Hostel Friends", "Late night snack", "food"),
                (upi, None, "College Canteen & Mess", "expense", 120.0, "21", "Canteen Fried Rice Lunch", "Afternoon lunch", "canteen"),
                (cash, None, "Metro, Bus & Bike Petrol", "expense", 320.0, "24", "Bike Petrol for College", "Fuel", "petrol"),
                (cash, None, "College Canteen & Mess", "expense", 60.0, "28", "Canteen Evening Tea & Puff", "Canteen break", "canteen")
            ],
            "2026-10": [
                (sbi, None, "Pocket Money / Parents Allowance", "income", 10000.0, "01", "Monthly Pocket Money from Dad", "October allowance", "pocket-money"),
                (sbi, None, "Freelance & Part-time Tutoring", "income", 3500.0, "08", "Class 10 Python Tutoring", "Taught Python programming basics", "tutoring"),
                (upi, None, "Cash Gift / Festival", "income", 1000.0, "14", "Diwali Cash Gift from Uncle", "Festive gift via GPay", "gift"),
                (sbi, upi, None, "transfer", 3500.0, "02", "Transfer to GPay for Festive Month", "Monthly UPI spend budget", "transfer"),
                (upi, cash, None, "transfer", 800.0, "04", "Cash Withdrawal for Local Travel & Xerox", "Kept in wallet for xerox and bus", "transfer"),
                (sbi, None, "Hostel / PG Room Rent", "expense", 4500.0, "02", "PG Room Rent (Sharing)", "Room rent including electricity", "rent,pg"),
                (upi, None, "Mobile Recharge & Internet", "expense", 719.0, "03", "Jio 5G 3-Month Plan", "Unlimited 5G student data plan", "recharge"),
                (upi, None, "College Canteen & Mess", "expense", 85.0, "03", "Canteen Samosa & Tea", "Break snacks with classmates", "canteen"),
                (cash, None, "Books, Xerox & Stationery", "expense", 150.0, "04", "DBMS Record Book & Lab Manual", "Bought for lab submissions", "stationery"),
                (upi, None, "Metro, Bus & Bike Petrol", "expense", 500.0, "05", "Metro Card Recharge", "Monthly smart card topup", "metro"),
                (upi, None, "College Canteen & Mess", "expense", 120.0, "06", "College Canteen Lunch Thali", "Lunch between lab sessions", "canteen"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 280.0, "07", "Zomato Hostel Pizza with Roommates", "Late night study session", "food"),
                (cash, None, "Books, Xerox & Stationery", "expense", 85.0, "09", "Semester Exam Notes Xerox", "Printed 40 pages of lecture slides", "xerox"),
                (upi, None, "College Canteen & Mess", "expense", 90.0, "10", "Dosa & Filter Coffee", "Morning breakfast", "canteen"),
                (upi, None, "Movies & Hangouts with Friends", "expense", 350.0, "11", "Movie Ticket & Popcorn at Mall", "Watched weekend blockbuster with friends", "movie"),
                (cash, None, "Metro, Bus & Bike Petrol", "expense", 300.0, "12", "Bike Petrol for College Commute", "Fuel fillup", "petrol"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 190.0, "13", "Swiggy Biryani Delivery", "Sunday dinner", "food"),
                (upi, None, "College Fest & Lab Materials", "expense", 450.0, "14", "College Tech Fest Registration & T-Shirt", "Hackathon entry fee + kit", "fest"),
                (upi, None, "Books, Xerox & Stationery", "expense", 240.0, "15", "DSA Reference Textbook", "Used textbook from senior", "books"),
                (upi, None, "College Canteen & Mess", "expense", 110.0, "17", "Canteen Fried Rice", "Afternoon lunch", "canteen"),
                (upi, None, "Movies & Hangouts with Friends", "expense", 180.0, "18", "Bowling & Arcade with batchmates", "College weekend outing", "fun"),
                (upi, None, "Metro, Bus & Bike Petrol", "expense", 200.0, "19", "Auto fare sharing with friends", "Late to college exam hall", "travel"),
                (upi, None, "Snacks, Swiggy & Zomato", "expense", 140.0, "20", "Burger & Cold Drink", "Evening hangout", "food")
            ]
        }

        # Insert all transactions from Jan to Oct
        for month_key, txns in monthly_data.items():
            for src_id, dst_id, c_name, t_type, amt, day_str, desc, notes, tags in txns:
                c_id = cat_map.get(c_name) if c_name else None
                date_str = f"{month_key}-{day_str}"
                cur.execute("""
                    INSERT INTO transactions (user_id, account_id, to_account_id, category_id, type, amount, date, description, notes, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (u_id, src_id, dst_id, c_id, t_type, amt, date_str, desc, notes, tags))

        # 4. Monthly Budgets for all 10 months (Jan-Oct 2026)
        budget_caps = [
            ("College Canteen & Mess", 1200.0, 0.8),
            ("Snacks, Swiggy & Zomato", 1000.0, 0.75),
            ("Books, Xerox & Stationery", 800.0, 0.8),
            ("Metro, Bus & Bike Petrol", 1200.0, 0.8),
            ("Hostel / PG Room Rent", 4500.0, 0.95),
            ("Movies & Hangouts with Friends", 800.0, 0.75),
            ("Mobile Recharge & Internet", 800.0, 0.9),
        ]

        for m in months:
            for c_name, limit, thresh in budget_caps:
                c_id = cat_map.get(c_name)
                if c_id:
                    cur.execute("""
                        INSERT INTO budgets (user_id, category_id, amount_limit, month, alert_threshold)
                        VALUES (?, ?, ?, ?, ?);
                    """, (u_id, c_id, limit, m, thresh))

        # 5. Student Savings Goals (Realistic College Student Milestones)
        student_goals = [
            ("Semester Exam Fees", 3500.0, 3500.0, "2026-11-15", "#10B981", "Saved for semester exam registration fee"),
            ("Placement & DSA Course", 2500.0, 2500.0, "2026-10-30", "#059669", "DSA interview preparation course"),
            ("College Goa Trip with Friends", 12000.0, 8500.0, "2027-01-20", "#3B82F6", "Semester break beach trip with college friends"),
            ("Coding Laptop Upgrade (M2/M3)", 55000.0, 26000.0, "2027-06-30", "#8B5CF6", "For AI/ML project & software development"),
            ("Noise Cancelling Headphones", 4500.0, 3200.0, "2026-12-25", "#F59E0B", "For studying in college library & hostel")
        ]

        for g_name, tgt, cur_amt, dt, clr, note in student_goals:
            comp = 1 if cur_amt >= tgt else 0
            cur.execute("""
                INSERT INTO savings_goals (user_id, name, target_amount, current_amount, target_date, color, notes, is_completed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (u_id, g_name, tgt, cur_amt, dt, clr, note, comp))

        # 6. Recalculate Balances for All Student Accounts
        cur.execute("SELECT id, initial_balance FROM accounts WHERE user_id = ?;", (u_id,))
        for acc in cur.fetchall():
            aid = acc["id"]
            init_b = float(acc["initial_balance"] or 0.0)

            cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE account_id = ? AND type = 'income';", (aid,))
            inc = float(cur.fetchone()[0])

            cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE account_id = ? AND type = 'expense';", (aid,))
            exp = float(cur.fetchone()[0])

            cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE account_id = ? AND type = 'transfer';", (aid,))
            xfer_out = float(cur.fetchone()[0])

            cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE to_account_id = ? AND type = 'transfer';", (aid,))
            xfer_in = float(cur.fetchone()[0])

            bal = round(init_b + inc - exp - xfer_out + xfer_in, 2)
            cur.execute("UPDATE accounts SET balance = ? WHERE id = ?;", (bal, aid))

    conn.commit()
    conn.close()
    print("SUCCESS: Configured balanced 10-month (Jan to Oct 2026) Student Pocket Money data!")

if __name__ == "__main__":
    populate_database()
