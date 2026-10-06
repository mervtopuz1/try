from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from pydantic import BaseModel
from datetime import date
import sqlite3
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")

app = FastAPI(title="Smart ATM API")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Add bank column if it does not exist
    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN bank TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # Add role column if it does not exist
    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN role TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # ATM assignments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS atm_assignments (
            atm_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            assigned_date TEXT,
            end_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Add assigned_date if old table already existed
    try:
        cursor.execute(
            "ALTER TABLE atm_assignments ADD COLUMN assigned_date TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # Add end_date if old table already existed
    try:
        cursor.execute(
            "ALTER TABLE atm_assignments ADD COLUMN end_date TEXT"
        )
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

init_db()

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str
# ------------------------------------------
# CORS
# ------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------
# DATA PATHS
# ------------------------------------------



CASH_FILE = os.path.join(
    BASE_DIR,
    "data",
    "cash_predictions.csv"
)

FAILURE_FILE = os.path.join(
    BASE_DIR,
    "data",
    "failure_predictions.csv"
)


# ------------------------------------------
# LOAD DATA
# ------------------------------------------

cash_df = pd.read_csv(CASH_FILE)
failure_df = pd.read_csv(FAILURE_FILE)

ATM_INFO_FILE = os.path.join(
    BASE_DIR,
    "data",
    "atm_info.csv"
)

atm_info_df = pd.read_csv(ATM_INFO_FILE)

# ------------------------------------------
# ROOT
# ------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Smart ATM API is running"
    }


# ------------------------------------------
# HEALTH
# ------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "cash_records": len(cash_df),
        "failure_records": len(failure_df)
    }

@app.post("/register")
def register_user(user: RegisterRequest):

    hashed_password = hashlib.sha256(
        user.password.encode()
    ).hexdigest()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users (name, email, password, bank, role)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user.name,
            user.email,
            hashed_password,
            "All",
            "Employee"
        )
    )

    conn.commit()
    conn.close()

    return {
        "message": "User registered successfully",
        "name": user.name,
        "email": user.email
    }

@app.post("/login")
def login_user(user: LoginRequest):

    hashed_password = hashlib.sha256(
        user.password.strip().encode()
    ).hexdigest()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, email, bank, role
        FROM users
        WHERE email = ? AND password = ?
        """,
        (user.email, hashed_password)
    )

    existing_user = cursor.fetchone()

    conn.close()

    if existing_user is None:
        return {
            "message": "Invalid email or password"
        }

    return {
        "message": "Login successful",
        "user_id": existing_user[0],
        "name": existing_user[1],
        "email": existing_user[2],
        "bank": existing_user[3],
        "role": existing_user[4]
    }


@app.post("/atms/assign")
def assign_atm(atm_id: int, user_id: int, end_date: str):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    assigned_date = date.today().isoformat()

    cursor.execute("""
        INSERT OR REPLACE INTO atm_assignments
        (atm_id, user_id, assigned_date, end_date)
        VALUES (?, ?, ?, ?)
    """, (
        atm_id,
        user_id,
        assigned_date,
        end_date
    ))

    conn.commit()
    conn.close()

    return {
        "message": "ATM assigned successfully",
        "assigned_date": assigned_date,
        "end_date": end_date
    }

@app.get("/users")
def get_users():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email, bank, role
        FROM users
    """)

    users = cursor.fetchall()
    conn.close()

    return [
        {
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "bank": user[3],
            "role": user[4]
        }
        for user in users
    ]

class UserUpdate(BaseModel):
    bank: str
    role: str

class UserEdit(BaseModel):
    name: str
    email: str
    password: str | None = None

@app.put("/users/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate
):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET bank = ?, role = ?
        WHERE id = ?
        """,
        (data.bank, data.role, user_id)
    )

    conn.commit()
    conn.close()

    return {
        "message": "User updated successfully"
    }

@app.delete("/users/{user_id}")
def delete_account(user_id: int):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return {
        "message": "Account deleted successfully"
    }

@app.put("/users/{user_id}/edit")
def edit_user(user_id: int, data: UserEdit):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if data.password:
        hashed_password = hashlib.sha256(
            data.password.encode()
        ).hexdigest()

        cursor.execute(
            """
            UPDATE users
            SET name = ?, email = ?, password = ?
            WHERE id = ?
            """,
            (
                data.name,
                data.email,
                hashed_password,
                user_id
            )
        )

    else:
        cursor.execute(
            """
            UPDATE users
            SET name = ?, email = ?
            WHERE id = ?
            """,
            (
                data.name,
                data.email,
                user_id
            )
        )

    conn.commit()
    conn.close()

    return {
        "message": "User updated successfully"
    }

@app.get("/users/visible")
def get_visible_users(current_user_id: int):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT bank, role
        FROM users
        WHERE id = ?
        """,
        (current_user_id,)
    )

    current_user = cursor.fetchone()

    if current_user is None:
        conn.close()
        return []

    current_bank = current_user[0]
    current_role = current_user[1]

    if current_role == "Super Manager":

        cursor.execute("""
            SELECT id, name, email, bank, role
            FROM users
        """)

    elif current_role == "Manager":

        cursor.execute(
            """
            SELECT id, name, email, bank, role
            FROM users
            WHERE bank = ?
            """,
            (current_bank,)
        )

    else:
        conn.close()
        return []

    users = cursor.fetchall()
    conn.close()

    return [
        {
            "id": u[0],
            "name": u[1],
            "email": u[2],
            "bank": u[3],
            "role": u[4]
        }
        for u in users
    ]


class ATMAssignment(BaseModel):
    atm_id: int
    user_id: int
    end_date: str | None


@app.put("/atms/{atm_id}/assign")
def assign_atm(
    atm_id: int,
    data: ATMAssignment,
    current_user_id: int
):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Giriş yapan Manager'ı bul
    cursor.execute(
        """
        SELECT bank, role
        FROM users
        WHERE id = ?
        """,
        (current_user_id,)
    )

    current_user = cursor.fetchone()

    if current_user is None:
        conn.close()
        return {"message": "User not found"}

    current_bank, current_role = current_user

    # Sadece Manager veya Super Manager atama yapabilir
    if current_role not in ["Manager", "Super Manager"]:
        conn.close()
        return {
            "message": "You are not authorized to assign ATMs"
        }

    # Atanacak kullanıcıyı kontrol et
    cursor.execute(
        """
        SELECT bank
        FROM users
        WHERE id = ?
        """,
        (data.user_id,)
    )

    target_user = cursor.fetchone()

    if target_user is None:
        conn.close()
        return {"message": "Target user not found"}

    target_bank = target_user[0]

    # ATM'nin bankasını bul
    atm_info = pd.read_csv(
        os.path.join(BASE_DIR, "data", "atm_info.csv")
    )

    atm_row = atm_info[atm_info["atm_id"] == atm_id]

    if atm_row.empty:
        conn.close()
        return {"message": "ATM not found"}

    atm_bank = atm_row.iloc[0]["bank"]

    # Manager sadece kendi bankasına işlem yapabilir
    if current_role == "Manager":

        if (
            atm_bank != current_bank
            or target_bank != current_bank
        ):
            conn.close()
            return {
                "message":
                "You can only assign ATMs and users from your own bank"
            }

    # Assigned date bugün
    assigned_date = date.today().isoformat()

    # Atamayı kaydet / varsa güncelle
    cursor.execute(
        """
        INSERT INTO atm_assignments
        (
            atm_id,
            user_id,
            assigned_date,
            end_date
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(atm_id)
        DO UPDATE SET
            user_id = excluded.user_id,
            assigned_date = excluded.assigned_date,
            end_date = excluded.end_date
        """,
        (
            atm_id,
            data.user_id,
            assigned_date,
            data.end_date
        )
    )

    conn.commit()
    conn.close()

    return {
        "message": "ATM assigned successfully",
        "assigned_date": assigned_date,
        "end_date": data.end_date
    }

# ------------------------------------------
# CASH PREDICTIONS
# ------------------------------------------

@app.get("/cash")
def get_cash_predictions():
    return cash_df.to_dict(orient="records")


# ------------------------------------------
# CASH SUMMARY
# ------------------------------------------

@app.get("/cash/summary")
def get_cash_summary():

    return {
        "total_records": len(cash_df),
        "average_actual": float(cash_df["actual"].mean()),
        "average_predicted": float(cash_df["predicted"].mean()),
        "average_error": float(cash_df["absolute_error"].mean())
    }

# ------------------------------------------
# FAILURE PREDICTIONS
# ------------------------------------------

@app.get("/failure")
def get_failure_predictions():
    return failure_df.to_dict(orient="records")


# ------------------------------------------
# FAILURE SUMMARY
# ------------------------------------------

@app.get("/failure/summary")
def get_failure_summary():

    failure_column = "failure_probability"

    if failure_column in failure_df.columns:

        average_probability = float(
            failure_df[failure_column].mean()
        )

    else:
        average_probability = None

    return {
        "total_records": len(failure_df),
        "average_failure_probability": average_probability
    }
# ------------------------------------------
# ATM LIST
# ------------------------------------------

@app.get("/atms")
def get_atms(
    bank: str = None,
    current_user_id: int = None
):

    print("RECEIVED bank param:", repr(bank))
    print("RECEIVED current_user_id:", repr(current_user_id))

    # Cash predictions
    cash = cash_df.groupby("atm_id").agg(
        predicted_cash=("predicted", "mean"),
        actual_cash=("actual", "mean")
    ).reset_index()

    # Failure predictions
    failure = failure_df.groupby("atm_id").agg(
        failure_probability=("failure_probability", "mean")
    ).reset_index()

    # ATM information
    atm_info = pd.read_csv(
        os.path.join(BASE_DIR, "data", "atm_info.csv")
    )

    # Maintenance information
    maintenance = pd.read_csv(
        os.path.join(BASE_DIR, "data", "atm_maintenance.csv")
    )

    maintenance = maintenance.groupby("atm_id").agg(
        days_since_maintenance=("days_since_maintenance", "mean"),
        maintenance_count=("maintenance_count", "max"),
        failure_count=("failure_count", "max"),
        network_errors=("network_errors", "max"),
        card_reader_errors=("card_reader_errors", "max"),
        dispenser_errors=("dispenser_errors", "max")
    ).reset_index()

    atms = atm_info.copy()

    atms = pd.merge(atms, cash, on="atm_id", how="left")
  
    atms = pd.merge(atms, failure, on="atm_id", how="left")
  
    atms = pd.merge(atms, maintenance, on="atm_id", how="left")
    
    # Risk level
    def get_risk(probability):

        if pd.isna(probability):
            return "N/A"

        if probability >= 0.60:
            return "High"
        elif probability >= 0.30:
            return "Medium"
        else:
            return "Low"

    atms["risk_level"] = atms["failure_probability"].apply(get_risk)

    # Format numbers
    atms["predicted_cash"] = atms["predicted_cash"].round(2)
    atms["actual_cash"] = atms["actual_cash"].round(2)
    atms["failure_probability"] = atms["failure_probability"].round(4)
    if bank and bank.lower() != "undefined" and bank.strip() != "":
        atms = atms[atms["bank"] == bank]

    # ATM assignments

    # ATM assignments

    conn = sqlite3.connect(DB_PATH)

    # Süresi geçmiş atamaları sil
    today = date.today().isoformat()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM atm_assignments
        WHERE end_date IS NOT NULL
        AND end_date < ?
        """,
        (today,)
    )

    conn.commit()

    # Güncel assignment'ları al
    assignments = pd.read_sql_query(
        """
        SELECT atm_id, user_id, assigned_date, end_date
        FROM atm_assignments
        """,
        conn
    )

    conn.close()

    atms = pd.merge(
        atms,
        assignments,
        on="atm_id",
        how="left"
    )

    print("BEFORE ROLE FILTER:", len(atms))

    atms = atms.astype(object).where(pd.notna(atms), None)

    if current_user_id is not None:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT role
            FROM users
            WHERE id = ?
            """,
            (current_user_id,)
        )

        current_user = cursor.fetchone()

        conn.close()

        print("CURRENT USER ROW:", current_user)

        if current_user is not None:
            current_role = current_user[0]
            print("CURRENT ROLE:", repr(current_role))

            # Employee sadece kendisine atanmış ATM'leri görür
            if current_role == "Employee":
                atms = atms[
                    atms["user_id"] == current_user_id
                ]
                print("AFTER EMPLOYEE FILTER:", len(atms)) 

    return atms.to_dict(orient="records")

class ATMCreate(BaseModel):
    location: str
    atm_type: str
    atm_age: int
    current_user_id: int


@app.post("/atms")
def add_atm(data: ATMCreate):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Giriş yapan kullanıcının rolünü ve bankasını bul
    cursor.execute(
        """
        SELECT bank, role
        FROM users
        WHERE id = ?
        """,
        (data.current_user_id,)
    )

    current_user = cursor.fetchone()

    if current_user is None:
        conn.close()
        return {"message": "User not found"}

    current_bank, current_role = current_user

    # SADECE Manager ATM ekleyebilir
    if current_role != "Manager":
        conn.close()
        return {
            "message": "Only Managers can add ATMs"
        }

    # CSV dosyasını oku
    atm_info_path = os.path.join(
        BASE_DIR,
        "data",
        "atm_info.csv"
    )

    atm_info = pd.read_csv(atm_info_path)

    # Yeni ATM ID
    if len(atm_info) == 0:
        new_atm_id = 1
    else:
        new_atm_id = int(atm_info["atm_id"].max()) + 1

    # Yeni ATM
    new_atm = pd.DataFrame([{
        "atm_id": new_atm_id,
        "location": data.location,
        "atm_type": data.atm_type,
        "atm_age": data.atm_age,
        "bank": current_bank
    }])

    # CSV'ye ekle
    atm_info = pd.concat(
        [atm_info, new_atm],
        ignore_index=True
    )

    atm_info.to_csv(
        atm_info_path,
        index=False
    )

    conn.close()

    return {
        "message": "ATM added successfully",
        "atm_id": new_atm_id,
        "bank": current_bank
    }

@app.get("/atms/{atm_id}/cash-history")
def get_atm_cash_history(atm_id: int):

    history = cash_df[
        cash_df["atm_id"] == atm_id
    ][["date", "actual", "predicted"]]

    return history.to_dict(orient="records")