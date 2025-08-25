#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contact Manager (Tkinter GUI)
Features:
- Contact fields: Store Name, Phone, Email, Address
- Add, View, Search (by Name/Phone), Update, Delete
- User-friendly interface (Treeview list, form fields, buttons)
- Persistent storage to JSON (contacts.json in the same folder)
Run:
    python contact_manager.py
"""
import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_TITLE = "Contact Manager"
DATA_FILE = "contacts.json"


def validate_phone(phone: str) -> bool:
    # Basic validation: allow digits, spaces, +, -, parentheses
    phone = phone.strip()
    return bool(re.fullmatch(r"[0-9+\-() ]{7,20}", phone))


def validate_email(email: str) -> bool:
    email = email.strip()
    # Very light email check
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


class ContactManager:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title(APP_TITLE)
        master.geometry("900x560")
        master.minsize(820, 520)

        self.contacts = []
        self.filtered_contacts = []
        self.selected_index = None  # index within filtered_contacts

        self._build_ui()
        self._load_contacts()
        self._refresh_table()

    # ----------------------- UI -----------------------
    def _build_ui(self):
        # Top bar (title + actions)
        top = ttk.Frame(self.master, padding=(12, 10))
        top.pack(fill="x")
        title = ttk.Label(top, text=APP_TITLE, font=("Segoe UI", 16, "bold"))
        title.pack(side="left")

        btn_frame = ttk.Frame(top)
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="Import JSON", command=self.import_json).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Export JSON", command=self.export_json).pack(side="left", padx=4)

        # Main content split (left form / right list)
        main = ttk.Frame(self.master, padding=(12, 0))
        main.pack(fill="both", expand=True)

        self.master.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # Left: Form
        form_card = ttk.LabelFrame(main, text="Contact Details", padding=12)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(4, 12))

        self.var_name = tk.StringVar()
        self.var_phone = tk.StringVar()
        self.var_email = tk.StringVar()
        self.txt_address = tk.Text(form_card, height=6, width=30, wrap="word")

        ttk.Label(form_card, text="Store Name *").grid(row=0, column=0, sticky="w")
        self.ent_name = ttk.Entry(form_card, textvariable=self.var_name)
        self.ent_name.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(form_card, text="Phone *").grid(row=2, column=0, sticky="w")
        self.ent_phone = ttk.Entry(form_card, textvariable=self.var_phone)
        self.ent_phone.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(form_card, text="Email").grid(row=4, column=0, sticky="w")
        self.ent_email = ttk.Entry(form_card, textvariable=self.var_email)
        self.ent_email.grid(row=5, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(form_card, text="Address").grid(row=6, column=0, sticky="w")
        self.txt_address.grid(row=7, column=0, sticky="nsew", pady=(0, 8))

        form_card.columnconfigure(0, weight=1)
        form_card.rowconfigure(7, weight=1)

        # Form action buttons
        form_btns = ttk.Frame(form_card)
        form_btns.grid(row=8, column=0, sticky="ew")
        ttk.Button(form_btns, text="Add New", command=self.add_contact).pack(side="left", padx=(0, 6))
        ttk.Button(form_btns, text="Update Selected", command=self.update_contact).pack(side="left", padx=6)
        ttk.Button(form_btns, text="Clear Form", command=self.clear_form).pack(side="left", padx=6)
        ttk.Button(form_btns, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=6)

        # Right: Search + Table
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        search_bar = ttk.Frame(right)
        search_bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(search_bar, text="Search (Name or Phone): ").pack(side="left")
        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", lambda *_: self._apply_search())
        self.ent_search = ttk.Entry(search_bar, textvariable=self.var_search)
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(6, 6))
        ttk.Button(search_bar, text="Clear", command=lambda: self.var_search.set("")).pack(side="left")

        # Table
        cols = ("name", "phone", "email", "address")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c.title())
        self.tree.column("name", width=160, anchor="w")
        self.tree.column("phone", width=120, anchor="w")
        self.tree.column("email", width=180, anchor="w")
        self.tree.column("address", width=260, anchor="w")

        vsb = ttk.Scrollbar(right, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(right, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # Footer help
        footer = ttk.Frame(self.master, padding=(12, 6))
        footer.pack(fill="x")
        ttk.Label(
            footer,
            text="Tip: Double-click a row to load it into the form for quick edits. *Required fields",
            foreground="#555"
        ).pack(side="left")

        # Style tweaks
        style = ttk.Style(self.master)
        try:
            self.master.call("source", "sun-valley.tcl")  # optional theme if present
            style.theme_use("sun-valley-dark")
        except Exception:
            pass
        style.configure("Treeview", rowheight=26)

    # ----------------------- Data I/O -----------------------
    def _load_contacts(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.contacts = json.load(f)
            except Exception:
                messagebox.showwarning("Load Error", "Could not read contacts.json, starting fresh.")
                self.contacts = []
        else:
            self.contacts = []
        self.filtered_contacts = list(self.contacts)

    def _save_contacts(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.contacts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save contacts:\n{e}")

    # ----------------------- Helpers -----------------------
    def _clear_table(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    def _refresh_table(self):
        self._clear_table()
        for idx, c in enumerate(self.filtered_contacts):
            self.tree.insert("", "end", iid=str(idx), values=(c["name"], c["phone"], c.get("email", ""), c.get("address", "")))

    def _apply_search(self):
        term = self.var_search.get().strip().lower()
        if not term:
            self.filtered_contacts = list(self.contacts)
        else:
            self.filtered_contacts = [
                c for c in self.contacts
                if term in c["name"].lower() or term in c["phone"].lower()
            ]
        self.selected_index = None
        self._refresh_table()

    def on_tree_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            self.selected_index = None
            return
        self.selected_index = int(sel[0])

    def on_tree_double_click(self, _event=None):
        # Load selected into form
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        c = self.filtered_contacts[idx]
        self.var_name.set(c["name"])
        self.var_phone.set(c["phone"])
        self.var_email.set(c.get("email", ""))
        self.txt_address.delete("1.0", "end")
        self.txt_address.insert("1.0", c.get("address", ""))

    def clear_form(self):
        self.var_name.set("")
        self.var_phone.set("")
        self.var_email.set("")
        self.txt_address.delete("1.0", "end")
        self.ent_name.focus_set()

    # ----------------------- CRUD -----------------------
    def add_contact(self):
        name = self.var_name.get().strip()
        phone = self.var_phone.get().strip()
        email = self.var_email.get().strip()
        address = self.txt_address.get("1.0", "end").strip()

        if not name or not phone:
            messagebox.showwarning("Missing Fields", "Store Name and Phone are required.")
            return
        if phone and not validate_phone(phone):
            messagebox.showwarning("Invalid Phone", "Please enter a valid phone number (digits, +, -, (), spaces).")
            return
        if email and not validate_email(email):
            messagebox.showwarning("Invalid Email", "Please enter a valid email address.")
            return

        # Prevent exact duplicate (same name + phone)
        for c in self.contacts:
            if c["name"].strip().lower() == name.lower() and c["phone"].strip() == phone:
                messagebox.showinfo("Duplicate", "A contact with the same name and phone already exists.")
                return

        new_contact = {"name": name, "phone": phone, "email": email, "address": address}
        self.contacts.append(new_contact)
        self._save_contacts()
        self._apply_search()  # respects current filter
        self.clear_form()

    def update_contact(self):
        if self.selected_index is None:
            messagebox.showinfo("No Selection", "Please select a contact from the list to update.")
            return

        name = self.var_name.get().strip()
        phone = self.var_phone.get().strip()
        email = self.var_email.get().strip()
        address = self.txt_address.get("1.0", "end").strip()

        if not name or not phone:
            messagebox.showwarning("Missing Fields", "Store Name and Phone are required.")
            return
        if phone and not validate_phone(phone):
            messagebox.showwarning("Invalid Phone", "Please enter a valid phone number (digits, +, -, (), spaces).")
            return
        if email and not validate_email(email):
            messagebox.showwarning("Invalid Email", "Please enter a valid email address.")
            return

        # Map filtered index back to real contacts index
        target = self.filtered_contacts[self.selected_index]
        real_index = self.contacts.index(target)

        self.contacts[real_index] = {"name": name, "phone": phone, "email": email, "address": address}
        self._save_contacts()
        self._apply_search()
        self.clear_form()

    def delete_selected(self):
        if self.selected_index is None:
            messagebox.showinfo("No Selection", "Please select a contact to delete.")
            return
        c = self.filtered_contacts[self.selected_index]
        if messagebox.askyesno("Confirm Delete", f"Delete contact '{c['name']}'?"):
            real_index = self.contacts.index(c)
            del self.contacts[real_index]
            self._save_contacts()
            self._apply_search()
            self.clear_form()

    # ----------------------- Import/Export -----------------------
    def export_json(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile="contacts_export.json",
            title="Export Contacts"
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.contacts, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exported", f"Contacts exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export contacts:\n{e}")

    def import_json(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
            title="Import Contacts"
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                imported = json.load(f)
            # Validate items
            valid = []
            for c in imported:
                name = str(c.get("name", "")).strip()
                phone = str(c.get("phone", "")).strip()
                email = str(c.get("email", "")).strip()
                address = str(c.get("address", "")).strip()
                if not name or not phone:
                    continue
                valid.append({"name": name, "phone": phone, "email": email, "address": address})
            # Merge: avoid exact duplicates (name+phone)
            existing_pairs = {(c["name"].lower().strip(), c["phone"].strip()) for c in self.contacts}
            new_items = [c for c in valid if (c["name"].lower().strip(), c["phone"].strip()) not in existing_pairs]
            self.contacts.extend(new_items)
            self._save_contacts()
            self._apply_search()
            messagebox.showinfo("Imported", f"Imported {len(new_items)} contacts.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import contacts:\n{e}")


def main():
    root = tk.Tk()
    ContactManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
