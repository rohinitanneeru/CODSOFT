import tkinter as tk
from tkinter import messagebox

# Global list to store tasks
todo_list = []

# Function to Add Task
def add_task():
    task = entry.get()
    if task != "":
        todo_list.append({"Task": task, "Status": "Pending"})
        update_listbox()
        entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Warning", "Please enter a task!")

# Function to View/Update Tasks
def update_listbox():
    listbox.delete(0, tk.END)
    for index, task in enumerate(todo_list, 1):
        listbox.insert(tk.END, f"{index}. {task['Task']} - {task['Status']}")

# Function to Remove Task
def remove_task():
    try:
        selected = listbox.curselection()[0]
        removed_task = todo_list.pop(selected)
        update_listbox()
        messagebox.showinfo("Removed", f"Task Removed: {removed_task['Task']}")
    except IndexError:
        messagebox.showwarning("Warning", "Please select a task to remove!")

# Function to Mark Task as Done
def mark_done():
    try:
        selected = listbox.curselection()[0]
        todo_list[selected]["Status"] = "Done"
        update_listbox()
    except IndexError:
        messagebox.showwarning("Warning", "Please select a task to mark as done!")

# Create main window
window = tk.Tk()
window.title("To-Do List App")
window.geometry("400x400")
window.config(bg="#f0f0f0")

# Title
title = tk.Label(window, text="📝 To-Do List", font=("Arial", 20, "bold"), bg="#f0f0f0")
title.pack(pady=10)

# Entry box
entry_frame = tk.Frame(window, bg="#f0f0f0")
entry_frame.pack(pady=5)

entry = tk.Entry(entry_frame, width=25, font=("Arial", 14))
entry.grid(row=0, column=0, padx=5)

add_button = tk.Button(entry_frame, text="Add Task", width=10, command=add_task, bg="#4CAF50", fg="white")
add_button.grid(row=0, column=1)

# Listbox to display tasks
listbox = tk.Listbox(window, width=40, height=10, font=("Arial", 12))
listbox.pack(pady=10)

# Buttons
btn_frame = tk.Frame(window, bg="#f0f0f0")
btn_frame.pack(pady=5)

remove_btn = tk.Button(btn_frame, text="Remove Task", width=12, command=remove_task, bg="#f44336", fg="white")
remove_btn.grid(row=0, column=0, padx=5)

done_btn = tk.Button(btn_frame, text="Mark Done", width=12, command=mark_done, bg="#2196F3", fg="white")
done_btn.grid(row=0, column=1, padx=5)

exit_btn = tk.Button(btn_frame, text="Exit", width=12, command=window.quit, bg="#9C27B0", fg="white")
exit_btn.grid(row=0, column=2, padx=5)

# Run application
window.mainloop()