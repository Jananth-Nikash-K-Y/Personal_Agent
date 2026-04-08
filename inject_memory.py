import os
import sqlite3

DB_PATH = "data/Lee.db"

def inject_memory():
    conn = sqlite3.connect(DB_PATH)
    memories = [
        "User earns 30,000 INR salary every month.",
        "User receives a 5,700 INR performance bonus every year in April for Q1.",
        "User pays 3,500 INR for EMI on the 5th of every month.",
        "User has average credit card bill of 5,000 to 6,000 INR.",
        "User has OTT subscriptions: Netflix (199 INR), Apple bundle (219 INR), YouTube Premium (149 INR).",
        "User saves 5,000 INR for his wife every month."
    ]
    for fact in memories:
        try:
            conn.execute("INSERT INTO user_memory (fact, created_at) VALUES (?, datetime('now'))", (fact,))
        except sqlite3.IntegrityError:
            pass # Already exists
            
    conn.commit()
    conn.close()
    print("Memories injected.")

if __name__ == "__main__":
    inject_memory()
