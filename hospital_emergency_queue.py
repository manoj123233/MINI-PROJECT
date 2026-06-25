import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

# ================= DATABASE =================

conn = sqlite3.connect("hospital.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    patient_id TEXT PRIMARY KEY,
    patient_name TEXT,
    age INTEGER,
    priority TEXT,
    symptoms TEXT,
    arrival_time TEXT,
    status TEXT
)
""")
conn.commit()

# ================= FUNCTIONS =================

def generate_patient_id():
    cursor.execute("""
    SELECT patient_id
    FROM patients
    ORDER BY patient_id DESC
    LIMIT 1
    """)

    row = cursor.fetchone()

    if row:
        last_id = int(row[0][1:])
        return f"P{last_id + 1:03d}"

    return "P001"


def clear_fields():
    entry_name.delete(0, tk.END)
    entry_age.delete(0, tk.END)
    entry_symptoms.delete(0, tk.END)
    combo_priority.set("")


def load_patients():
    for item in tree.get_children():
        tree.delete(item)

    cursor.execute("""
    SELECT * FROM patients
    ORDER BY
    CASE priority
        WHEN 'Critical' THEN 1
        WHEN 'Serious' THEN 2
        WHEN 'Normal' THEN 3
    END,
    arrival_time
    """)

    for row in cursor.fetchall():
        tree.insert("", tk.END, values=row)


def add_patient():
    name = entry_name.get().strip()
    age = entry_age.get().strip()
    priority = combo_priority.get()
    symptoms = entry_symptoms.get().strip()

    if not all([name, age, priority, symptoms]):
        messagebox.showerror("Error", "Fill all fields")
        return

    try:
        age = int(age)
    except ValueError:
        messagebox.showerror("Error", "Age must be numeric")
        return

    pid = generate_patient_id()
    arrival = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    cursor.execute("""
    INSERT INTO patients
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (pid, name, age, priority, symptoms, arrival, "Waiting"))

    conn.commit()

    load_patients()
    clear_fields()

    messagebox.showinfo("Success", f"Patient Added Successfully\nID: {pid}")


def search_patient():
    pid = entry_search.get().strip()

    if not pid:
        messagebox.showerror("Error", "Enter Patient ID")
        return

    cursor.execute("SELECT * FROM patients WHERE patient_id=?", (pid,))
    row = cursor.fetchone()

    for item in tree.get_children():
        tree.delete(item)

    if row:
        tree.insert("", tk.END, values=row)

        entry_name.delete(0, tk.END)
        entry_name.insert(0, row[1])

        entry_age.delete(0, tk.END)
        entry_age.insert(0, row[2])

        combo_priority.set(row[3])

        entry_symptoms.delete(0, tk.END)
        entry_symptoms.insert(0, row[4])
    else:
        messagebox.showinfo("Search", "Patient Not Found")


def update_patient():
    selected = tree.focus()

    if not selected:
        messagebox.showerror("Error", "Select a patient")
        return

    pid = tree.item(selected)["values"][0]

    name = entry_name.get().strip()
    age = entry_age.get().strip()
    priority = combo_priority.get()
    symptoms = entry_symptoms.get().strip()

    if not all([name, age, priority, symptoms]):
        messagebox.showerror("Error", "Fill all fields")
        return

    try:
        age = int(age)
    except ValueError:
        messagebox.showerror("Error", "Age must be numeric")
        return

    cursor.execute("""
    UPDATE patients
    SET patient_name=?, age=?, priority=?, symptoms=?
    WHERE patient_id=?
    """, (name, age, priority, symptoms, pid))

    conn.commit()
    load_patients()

    messagebox.showinfo("Success", "Patient Updated Successfully")


def delete_patient():
    selected = tree.focus()

    if not selected:
        messagebox.showerror("Error", "Select a patient")
        return

    pid = tree.item(selected)["values"][0]

    cursor.execute("DELETE FROM patients WHERE patient_id=?", (pid,))
    conn.commit()

    load_patients()

    messagebox.showinfo("Deleted", "Patient Deleted Successfully")


def select_record(event):
    selected = tree.focus()

    if not selected:
        return

    values = tree.item(selected)["values"]

    entry_name.delete(0, tk.END)
    entry_name.insert(0, values[1])

    entry_age.delete(0, tk.END)
    entry_age.insert(0, values[2])

    combo_priority.set(values[3])

    entry_symptoms.delete(0, tk.END)
    entry_symptoms.insert(0, values[4])


def treat_next_patient():
    cursor.execute("""
    SELECT *
    FROM patients
    WHERE status='Waiting'
    ORDER BY
    CASE priority
        WHEN 'Critical' THEN 1
        WHEN 'Serious' THEN 2
        WHEN 'Normal' THEN 3
    END,
    arrival_time
    LIMIT 1
    """)

    patient = cursor.fetchone()

    if not patient:
        messagebox.showinfo("Queue", "No waiting patients")
        return

    cursor.execute("""
    UPDATE patients
    SET status='In Treatment'
    WHERE patient_id=?
    """, (patient[0],))

    conn.commit()
    load_patients()

    messagebox.showinfo(
        "Next Patient",
        f"Treat Patient: {patient[0]} - {patient[1]}"
    )


def complete_treatment():
    cursor.execute("""
    SELECT patient_id
    FROM patients
    WHERE status='In Treatment'
    LIMIT 1
    """)

    patient = cursor.fetchone()

    if not patient:
        messagebox.showinfo(
            "Info",
            "No patient is currently in treatment"
        )
        return

    cursor.execute("""
    UPDATE patients
    SET status='Completed'
    WHERE patient_id=?
    """, (patient[0],))

    conn.commit()
    load_patients()

    messagebox.showinfo(
        "Success",
        f"Patient {patient[0]} treatment completed"
    )

# ================= GUI =================

root = tk.Tk()
root.title("Hospital Emergency Queue Management")
root.geometry("1200x650")

# Search Frame

search_frame = tk.Frame(root)
search_frame.pack(pady=5)

tk.Label(search_frame, text="Patient ID").pack(side=tk.LEFT, padx=5)

entry_search = tk.Entry(search_frame)
entry_search.pack(side=tk.LEFT, padx=5)

tk.Button(search_frame, text="Search",
          command=search_patient).pack(side=tk.LEFT, padx=5)

tk.Button(search_frame, text="Show All",
          command=load_patients).pack(side=tk.LEFT, padx=5)

# Form

form = tk.LabelFrame(root, text="Patient Registration",
                     padx=10, pady=10)
form.pack(fill="x", padx=10, pady=10)

tk.Label(form, text="Name").grid(row=0, column=0)
entry_name = tk.Entry(form, width=25)
entry_name.grid(row=0, column=1)

tk.Label(form, text="Age").grid(row=0, column=2)
entry_age = tk.Entry(form, width=20)
entry_age.grid(row=0, column=3)

tk.Label(form, text="Priority").grid(row=1, column=0)

combo_priority = ttk.Combobox(
    form,
    values=["Critical", "Serious", "Normal"],
    state="readonly"
)
combo_priority.grid(row=1, column=1)

tk.Label(form, text="Symptoms").grid(row=1, column=2)
entry_symptoms = tk.Entry(form, width=25)
entry_symptoms.grid(row=1, column=3)

tk.Button(form, text="Add Patient",
          command=add_patient).grid(row=2, column=0, pady=10)

tk.Button(form, text="Update Patient",
          command=update_patient).grid(row=2, column=1)

tk.Button(form, text="Treat Next",
          command=treat_next_patient).grid(row=2, column=2)

tk.Button(form, text="Complete Treatment",
          command=complete_treatment).grid(row=2, column=3)

tk.Button(form, text="Delete Patient",
          command=delete_patient).grid(row=3, column=1, pady=5)

# Table

columns = (
    "ID", "Name", "Age",
    "Priority", "Symptoms",
    "Arrival Time", "Status"
)

tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=160)

tree.pack(fill="both", expand=True, padx=10, pady=10)

tree.bind("<<TreeviewSelect>>", select_record)

load_patients()

root.mainloop()

conn.close()
