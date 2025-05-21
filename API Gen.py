# title : API Generator

import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json

# Helper Functions
def parse_columns(column_input):
    schema = {}
    required = []
    for col in column_input.split(","):
        name_type = col.strip().split(":")
        if len(name_type) != 2:
            continue
        name, dtype = name_type
        name = name.strip()
        dtype = dtype.strip().upper()
        if "PRIMARY KEY" in dtype:
            json_type = "integer"
        elif "TEXT" in dtype:
            json_type = "string"
        elif "INTEGER" in dtype:
            json_type = "integer"
        elif "REAL" in dtype or "FLOAT" in dtype:
            json_type = "number"
        else:
            json_type = "string"
        schema[name] = {"type": json_type}
        if "NOT NULL" in dtype or "PRIMARY KEY" in dtype:
            required.append(name)
    return schema, required

def generate_json_schema(table_name, columns_input):
    properties, required = parse_columns(columns_input)
    schema = {
        "title": table_name,
        "type": "object",
        "properties": properties,
        "required": required
    }
    return json.dumps(schema, indent=2)

def generate_stored_procedure_sql(table, columns_input):
    columns = [col.strip().split(":")[0] for col in columns_input.split(",")]
    fields = ", ".join(columns)
    parameters = ", ".join([f"@{col} NVARCHAR(MAX)" for col in columns if col.lower() != "id"])
    updates = ", ".join([f"{col} = @{col}" for col in columns if col.lower() != "id"])
    insert_fields = ", ".join([col for col in columns if col.lower() != "id"])
    insert_values = ", ".join([f"@{col}" for col in columns if col.lower() != "id"])

    sql = f"""CREATE PROCEDURE usp_Upsert_{table}
    @id INT = NULL,
    {parameters}
AS
BEGIN
    SET NOCOUNT ON;

    IF @id IS NOT NULL AND EXISTS (SELECT 1 FROM {table} WHERE id = @id)
    BEGIN
        UPDATE {table}
        SET {updates}
        WHERE id = @id;
    END
    ELSE
    BEGIN
        INSERT INTO {table} ({insert_fields})
        VALUES ({insert_values});
        SET @id = SCOPE_IDENTITY();
    END

    SELECT * FROM {table} WHERE id = @id;
END
"""
    return sql

def generate_fastapi_code(db_file, table, columns_input):
    schema, required = parse_columns(columns_input)
    pydantic_model = "\n".join([f"    {k}: {v['type']}" for k, v in schema.items()])

    code = f'''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()
DATABASE = "{db_file}"

class {table.capitalize()}Model(BaseModel):
{pydantic_model}

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/{table}")
def get_all_records():
    conn = get_db_connection()
    try:
        records = conn.execute("SELECT * FROM {table}").fetchall()
        return [dict(r) for r in records]
    finally:
        conn.close()

@app.get("/api/{table}/{{record_id}}")
def get_record(record_id: int):
    conn = get_db_connection()
    try:
        record = conn.execute("SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
        if record:
            return dict(record)
        raise HTTPException(status_code=404, detail="Record not found")
    finally:
        conn.close()

@app.post("/api/{table}")
def create_or_update(data: {table.capitalize()}Model):
    conn = get_db_connection()
    cursor = conn.cursor()
    fields = data.dict()
    if "id" in fields and fields["id"] is not None:
        columns = ", ".join(f+" = ?" for f in fields if f != "id")
        values = [fields[k] for k in fields if k != "id"]
        values.append(fields["id"])
        cursor.execute(f"UPDATE {table} SET {{columns}} WHERE id = ?", values)
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Update failed")
        conn.commit()
        return {{ "message": "Updated successfully" }}
    else:
        columns = ", ".join(fields.keys())
        placeholders = ", ".join(["?"] * len(fields))
        values = tuple(fields.values())
        cursor.execute(f"INSERT INTO {table} ({{columns}}) VALUES ({{placeholders}})", values)
        conn.commit()
        return {{ "message": "Created successfully", "id": cursor.lastrowid }}
'''
    return code
def generate_dotnet_controller_code(table, columns_input, with_fastapi_style=False):
    class_name = table.capitalize()
    model_fields = "\n        ".join([
        f"public string {col.strip().split(':')[0].capitalize()} {{ get; set; }}"
        for col in columns_input.split(",")
    ])
    route_attr = '[Route("api/[controller]")]' if with_fastapi_style else f'[Route("api/{table}")]'

    controller_code = f"""using Microsoft.AspNetCore.Mvc;

namespace MyApi.Controllers
{{
    {route_attr}
    [ApiController]
    public class {class_name}Controller : ControllerBase
    {{
        [HttpGet]
        public IActionResult Get()
        {{
            return Ok(new[] {{ "value1", "value2" }});
        }}

        [HttpPost]
        public IActionResult Post([FromBody] {class_name}Model model)
        {{
            return Ok(model);
        }}
    }}

    public class {class_name}Model
    {{
        {model_fields}
    }}
}}"""
    return controller_code

# GUI Functions
def on_generate():
    lang = language_var.get()
    framework = framework_var.get()
    db_file = db_filename_var.get()
    table = table_name_var.get()
    columns = columns_input.get("1.0", tk.END).strip()

    try:
        os.makedirs(f"./generated_controllers", exist_ok=True)
        if lang == "Python":
            code = generate_fastapi_code(db_file, table, columns)
            json_schema = generate_json_schema(table, columns)
            folder = "python"
        elif lang == ".NET":
            code = generate_dotnet_controller_code(table, columns, with_fastapi_style=(framework == "FastAPI-style"))
            json_schema = generate_json_schema(table, columns)
            folder = "dotnet"
        else:
            raise ValueError("Language not supported.")

        stored_proc = generate_stored_procedure_sql(table, columns)
        os.makedirs(f"./generated_controllers/{folder}", exist_ok=True)

        with open(f"./generated_controllers/{folder}/{table}_controller.txt", "w") as f:
            f.write(code)
        with open(f"./generated_controllers/{folder}/{table}_schema.json", "w") as f:
            f.write(json_schema)
        with open(f"./generated_controllers/{folder}/{table}_stored_procedure.sql", "w") as f:
            f.write(stored_proc)

        preview_area.delete("1.0", tk.END)
        preview_area.insert(tk.END, code)

        proc_area.delete("1.0", tk.END)
        proc_area.insert(tk.END, stored_proc)

        messagebox.showinfo("Success", f"Generated controller, schema, and stored procedure.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Build Modern UI
root = tk.Tk()
root.title("Modern API Controller Generator")
root.geometry("1100x800")
root.configure(bg="#f0f2f5")

frame = tk.Frame(root,height=500, bg="#f0f2f5")
frame.pack(fill='both', expand=True, padx=20, pady=20)

# UI Variables
language_var = tk.StringVar(value="Python")
framework_var = tk.StringVar(value="FastAPI")
db_filename_var = tk.StringVar()
table_name_var = tk.StringVar()

# Options layout
options_frame = tk.Frame(frame,height=500 ,bg="#f0f2f5")
options_frame.pack(fill='x', pady=5)

tk.Label(options_frame, text="Language", bg="#f0f2f5").grid(row=0, column=0, sticky='w')
ttk.Combobox(options_frame, textvariable=language_var, values=["Python", ".NET"], width=15).grid(row=1, column=0, padx=5)

tk.Label(options_frame, text="Framework Style", bg="#f0f2f5").grid(row=0, column=1, sticky='w')
ttk.Combobox(options_frame, textvariable=framework_var, values=["FastAPI", "FastAPI-style", "None"], width=20).grid(row=1, column=1, padx=5)

tk.Label(options_frame, text="Database Filename", bg="#f0f2f5").grid(row=0, column=2, sticky='w')
tk.Entry(options_frame, textvariable=db_filename_var, width=30).grid(row=1, column=2, padx=5)

tk.Label(options_frame, text="Table Name", bg="#f0f2f5").grid(row=0, column=3, sticky='w')
tk.Entry(options_frame, textvariable=table_name_var, width=20).grid(row=1, column=3, padx=5)

# Column input
tk.Label(frame, text="Columns (e.g. id:INTEGER PRIMARY KEY, name:TEXT NOT NULL)", bg="#f0f2f5").pack(anchor='w')
columns_input = scrolledtext.ScrolledText(frame, height=5, font=("Consolas", 10))
columns_input.pack(fill='both', pady=5)

# Generate button
tk.Button(frame, text="Generate Controller", command=on_generate, bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=10)

# Preview areas
preview_frame = tk.Frame(frame, bg="#f0f2f5")
preview_frame.pack(fill='both', expand=True)

tk.Label(preview_frame, text="Generated Code Preview", bg="#f0f2f5", font=("Segoe UI", 10, "bold")).grid(
    row=0, column=0, sticky='w', padx=5
)
tk.Label(preview_frame, text="Generated Stored Procedure", bg="#f0f2f5", font=("Segoe UI", 10, "bold")).grid(
    row=0, column=1, sticky='w', padx=5
)

preview_area = scrolledtext.ScrolledText(preview_frame, font=("Consolas", 10))
preview_area.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

proc_area = scrolledtext.ScrolledText(preview_frame, font=("Consolas", 10))
proc_area.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)

# Make both columns and the row expand
preview_frame.grid_columnconfigure(0, weight=1)
preview_frame.grid_columnconfigure(1, weight=1)
preview_frame.grid_rowconfigure(1, weight=1)  # This line makes row 1 (with the previews) expand vertically


root.mainloop()
