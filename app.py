from __future__ import annotations

import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from pblite.catalog import load_mml, search_materials
from pblite.exporter import export_used_materials
from pblite.models import Gutter, Project, Run, SelectedMaterial
from pblite.storage import load_cached_catalog, load_project, save_cached_catalog, save_project
from pblite.takeoff import material_total, used_materials


class MaterialPicker(tk.Toplevel):
    def __init__(self, parent, catalog, title, kinds=()):
        super().__init__(parent)
        self.title(title)
        self.geometry("1120x680")
        self.minsize(900, 540)
        self.catalog, self.kinds, self.selection, self.quantity = catalog, kinds, None, 1.0
        self.query = tk.StringVar()
        self.type_filter = tk.StringVar(value="All")
        self.size_filter = tk.StringVar(value="All")
        self.color_filter = tk.StringVar(value="All")
        self.quantity_var = tk.StringVar(value="1")
        self.filtered_items = []
        self.query.trace_add("write", lambda *_: self.refresh())

        header = ttk.Frame(self, padding=(16, 14, 16, 8))
        header.pack(fill="x")
        ttk.Label(header, text=title, font=("Segoe UI", 15, "bold")).pack(side="left")
        ttk.Label(header, text="Search your loaded MML, then select a material and quantity.", foreground="#5f6368").pack(side="left", padx=14)

        filters = ttk.LabelFrame(self, text="Find material", padding=10)
        filters.pack(fill="x", padx=16, pady=(0, 8))
        ttk.Label(filters, text="Search").grid(row=0, column=0, sticky="w")
        search = ttk.Entry(filters, textvariable=self.query, width=42)
        search.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        search.focus_set()
        for column, label, variable, values in (
            (1, "Type", self.type_filter, self._filter_values("Type")),
            (2, "Size", self.size_filter, self._filter_values("Size")),
            (3, "Color", self.color_filter, self._filter_values("Color")),
        ):
            ttk.Label(filters, text=label).grid(row=0, column=column, sticky="w")
            combo = ttk.Combobox(filters, textvariable=variable, values=["All", *values], state="readonly", width=16)
            combo.grid(row=1, column=column, sticky="ew", padx=(0, 10))
            combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh())
        filters.columnconfigure(0, weight=1)

        body = ttk.Frame(self, padding=(16, 0, 16, 0))
        body.pack(fill="both", expand=True)
        columns = ("catalog", "description", "type", "size", "color", "price")
        table = ttk.Frame(body)
        table.pack(side="left", fill="both", expand=True)
        self.tree = ttk.Treeview(table, columns=columns, show="headings", selectmode="browse")
        for column, label, width in (("catalog", "Catalog #", 145), ("description", "Description", 360), ("type", "Type", 95), ("size", "Size", 75), ("color", "Color", 95), ("price", "Price", 90)):
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor="w")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.show_details)
        self.tree.bind("<Double-1>", lambda _event: self.select())

        details = ttk.LabelFrame(body, text="Selected material", padding=14, width=280)
        details.pack(side="right", fill="y", padx=(12, 0))
        details.pack_propagate(False)
        self.detail_catalog = ttk.Label(details, text="Choose a material", font=("Segoe UI", 12, "bold"), wraplength=245)
        self.detail_catalog.pack(anchor="w", pady=(0, 10))
        self.detail_description = ttk.Label(details, text="", wraplength=245, justify="left")
        self.detail_description.pack(anchor="w", pady=(0, 14))
        self.detail_meta = ttk.Label(details, text="", foreground="#5f6368", justify="left", wraplength=245)
        self.detail_meta.pack(anchor="w")
        ttk.Separator(details).pack(fill="x", pady=16)
        ttk.Label(details, text="Quantity").pack(anchor="w")
        ttk.Spinbox(details, from_=0.01, to=99999, increment=1, textvariable=self.quantity_var, width=12).pack(anchor="w", pady=(4, 14))
        ttk.Label(details, text="For wire, use the number of individual conductors.\nRun length is calculated separately.", wraplength=245, foreground="#5f6368", justify="left").pack(anchor="w")
        self.photo_button = ttk.Button(details, text="View Photo", command=self.open_photo, state="disabled")
        self.photo_button.pack(anchor="w", pady=(16, 0))

        footer = ttk.Frame(self, padding=16)
        footer.pack(fill="x")
        self.result_label = ttk.Label(footer, text="0 materials")
        self.result_label.pack(side="left")
        ttk.Button(footer, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(footer, text="Add Material", command=self.select).pack(side="right", padx=(0, 8))
        self.refresh()
        self.transient(parent)
        self.grab_set()

    def _filter_values(self, field):
        allowed = search_materials(self.catalog, kinds=self.kinds)
        return sorted({str(item.get(field, "")).strip() for item in allowed if str(item.get(field, "")).strip()}, key=str.lower)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.photo_button.config(state="disabled")
        self.filtered_items = []
        for item in search_materials(self.catalog, self.query.get(), self.kinds):
            if self.type_filter.get() != "All" and item.get("Type") != self.type_filter.get():
                continue
            if self.size_filter.get() != "All" and item.get("Size") != self.size_filter.get():
                continue
            if self.color_filter.get() != "All" and item.get("Color") != self.color_filter.get():
                continue
            index = len(self.filtered_items)
            self.filtered_items.append(item)
            self.tree.insert("", "end", iid=str(index), values=(item["CatalogNumber"], item["Description"], item["Type"], item["Size"], item["Color"], f"${item['Price']:,.2f}"))
        self.result_label.config(text=f"{len(self.filtered_items):,} material{'s' if len(self.filtered_items) != 1 else ''}")

    def show_details(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.filtered_items[int(selected[0])]
        self.detail_catalog.config(text=item["CatalogNumber"])
        self.detail_description.config(text=item["Description"] or "No description")
        parts = [f"Type: {item['Type'] or '—'}", f"Size: {item['Size'] or '—'}", f"Color: {item['Color'] or '—'}", f"Unit price: ${item['Price']:,.2f}"]
        self.detail_meta.config(text="\n".join(parts))
        self.photo_button.config(state="normal" if item.get("PhotoLink") else "disabled")

    def open_photo(self):
        selected = self.tree.selection()
        if not selected:
            return
        link = self.filtered_items[int(selected[0])].get("PhotoLink", "").strip()
        if link:
            webbrowser.open_new_tab(link)

    def select(self):
        selected = self.tree.selection()
        if not selected:
            return
        try:
            self.quantity = float(self.quantity_var.get())
            if self.quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid quantity", "Enter a quantity greater than zero.", parent=self)
            return
        self.selection = self.filtered_items[int(selected[0])]
        self.destroy()


class PanelBuilderLite(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Panel Builder Lite")
        self.geometry("1180x760")
        self.project, self.catalog, self.project_path = Project(), [], None
        self.vars = {key: tk.StringVar() for key in ("project_name", "address", "model", "electrician", "lender")}
        self._build_ui()
        self.restore_cached_catalog()

    def _build_ui(self):
        toolbar = ttk.Frame(self, padding=8)
        toolbar.pack(fill="x")
        for text, command in (("Load MML", self.load_mml), ("New", self.new_project), ("Open", self.open_project), ("Save", self.save_project), ("Export XLSX", self.export_xlsx)):
            ttk.Button(toolbar, text=text, command=command).pack(side="left", padx=3)
        self.catalog_label = ttk.Label(toolbar, text="No MML loaded")
        self.catalog_label.pack(side="right")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.project_tab = ttk.Frame(self.tabs, padding=18)
        self.runs_tab = ttk.Frame(self.tabs, padding=10)
        self.gutters_tab = ttk.Frame(self.tabs, padding=10)
        self.summary_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.project_tab, text="Project")
        self.tabs.add(self.runs_tab, text="Runs")
        self.tabs.add(self.gutters_tab, text="Gutters")
        self.tabs.add(self.summary_tab, text="Used Materials")
        self._build_project_tab(); self._build_runs_tab(); self._build_gutters_tab(); self._build_summary_tab()

    def _build_project_tab(self):
        for row, (label, key) in enumerate((("Project name", "project_name"), ("Address", "address"), ("Model", "model"), ("Electrician", "electrician"), ("Lender", "lender"))):
            ttk.Label(self.project_tab, text=label).grid(row=row, column=0, sticky="w", pady=6)
            ttk.Entry(self.project_tab, textvariable=self.vars[key], width=65).grid(row=row, column=1, sticky="ew", pady=6)

    def _build_runs_tab(self):
        bar = ttk.Frame(self.runs_tab); bar.pack(fill="x")
        ttk.Button(bar, text="Add Run", command=self.add_run).pack(side="left")
        ttk.Button(bar, text="Edit Selected", command=self.edit_run).pack(side="left", padx=5)
        ttk.Button(bar, text="Remove", command=self.remove_run).pack(side="left")
        self.runs_tree = ttk.Treeview(self.runs_tab, columns=("name", "length", "conduit", "wires", "fittings"), show="headings")
        for key, label, width in (("name", "Run", 220), ("length", "Length (ft)", 100), ("conduit", "Conduit", 220), ("wires", "Wires", 290), ("fittings", "Fittings", 290)):
            self.runs_tree.heading(key, text=label); self.runs_tree.column(key, width=width)
        self.runs_tree.pack(fill="both", expand=True, pady=10)

    def _build_gutters_tab(self):
        bar = ttk.Frame(self.gutters_tab); bar.pack(fill="x")
        ttk.Button(bar, text="Add Gutter", command=self.add_gutter).pack(side="left")
        ttk.Button(bar, text="Edit Selected", command=self.edit_gutter).pack(side="left", padx=5)
        ttk.Button(bar, text="Remove", command=self.remove_gutter).pack(side="left")
        self.gutters_tree = ttk.Treeview(self.gutters_tab, columns=("name", "length", "runs", "fittings"), show="headings")
        for key, label, width in (("name", "Gutter", 240), ("length", "Length (ft)", 110), ("runs", "Included runs", 400), ("fittings", "Fittings", 350)):
            self.gutters_tree.heading(key, text=label); self.gutters_tree.column(key, width=width)
        self.gutters_tree.pack(fill="both", expand=True, pady=10)

    def _build_summary_tab(self):
        self.total_label = ttk.Label(self.summary_tab, font=("Segoe UI", 13, "bold"))
        self.total_label.pack(anchor="e")
        self.summary_tree = ttk.Treeview(self.summary_tab, columns=("description", "catalog", "qty", "price", "total"), show="headings")
        for key, label, width in (("description", "Description", 510), ("catalog", "Catalog Number", 180), ("qty", "Qty", 120), ("price", "Unit Price", 140), ("total", "Total", 140)):
            self.summary_tree.heading(key, text=label); self.summary_tree.column(key, width=width)
        self.summary_tree.pack(fill="both", expand=True, pady=10)

    def sync_project_details(self):
        for key, variable in self.vars.items():
            setattr(self.project, key, variable.get().strip())

    def sync_form(self):
        for key, variable in self.vars.items(): variable.set(getattr(self.project, key))

    def load_mml(self):
        path = filedialog.askopenfilename(filetypes=[("Excel workbook", "*.xlsx *.xlsm")])
        if not path: return
        try:
            self.catalog = load_mml(path)
            if not self.catalog:
                messagebox.showwarning("No materials found", "No catalog rows were found in that workbook.")
                return
            save_cached_catalog(self.catalog)
            self.catalog_label.config(text=f"MML cached: {len(self.catalog):,} materials")
            messagebox.showinfo("MML loaded", "The MML is now saved locally and will load automatically next time.")
        except Exception as error:
            messagebox.showerror("MML load failed", str(error))

    def restore_cached_catalog(self):
        try:
            self.catalog = load_cached_catalog()
        except Exception:
            self.catalog = []
        if self.catalog:
            self.catalog_label.config(text=f"MML cached: {len(self.catalog):,} materials")

    def new_project(self):
        self.project, self.project_path = Project(), None
        self.sync_form(); self.refresh_all()

    def open_project(self):
        path = filedialog.askopenfilename(filetypes=[("Panel Builder project", "*.json")])
        if not path: return
        try:
            self.project, self.project_path = load_project(path), path
            self.sync_form(); self.refresh_all()
        except Exception as error:
            messagebox.showerror("Open failed", str(error))

    def save_project(self):
        self.sync_project_details()
        path = self.project_path or filedialog.asksaveasfilename(defaultextension=".json", initialfile=f"{self.project.project_name or 'Project'}.json", filetypes=[("Panel Builder project", "*.json")])
        if not path: return
        save_project(path, self.project); self.project_path = path
        messagebox.showinfo("Saved", "Project saved locally.")

    def export_xlsx(self):
        self.sync_project_details()
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"{self.project.project_name or 'Project'} Used Materials.xlsx", filetypes=[("Excel workbook", "*.xlsx")])
        if not path: return
        export_used_materials(path, self.project)
        messagebox.showinfo("Exported", f"Created:\n{path}")

    def choose_material(self, title, kinds=()):
        if not self.catalog:
            messagebox.showwarning("Load MML first", "Load your MML Excel workbook before selecting materials.")
            return None
        picker = MaterialPicker(self, self.catalog, title, kinds)
        self.wait_window(picker)
        return (picker.selection, picker.quantity) if picker.selection else (None, 0)

    def add_run(self):
        run = Run(name=f"Run {len(self.project.runs) + 1}")
        self.project.runs.append(run); self.edit_run(run)

    def selected_run(self):
        selected = self.runs_tree.selection()
        return next((run for run in self.project.runs if run.id == selected[0]), None) if selected else None

    def edit_run(self, run=None):
        run = run or self.selected_run()
        if not run: return
        dialog = tk.Toplevel(self); dialog.title("Edit Run"); dialog.geometry("760x560"); dialog.transient(self); dialog.grab_set()
        name, length = tk.StringVar(value=run.name), tk.StringVar(value=str(run.length_ft))
        ttk.Label(dialog, text="Run name").pack(anchor="w", padx=12, pady=(12, 0)); ttk.Entry(dialog, textvariable=name).pack(fill="x", padx=12)
        ttk.Label(dialog, text="Length (ft)").pack(anchor="w", padx=12, pady=(10, 0)); ttk.Entry(dialog, textvariable=length).pack(fill="x", padx=12)
        selected_label = ttk.Label(dialog, text=f"Conduit: {run.conduit.catalog_number if run.conduit else 'Not selected'}"); selected_label.pack(anchor="w", padx=12, pady=10)
        def select_conduit():
            item, quantity = self.choose_material("Select Conduit", ("CONDUIT",))
            if item: run.conduit = SelectedMaterial.from_catalog(item, quantity); selected_label.config(text=f"Conduit: {run.conduit.catalog_number}")
        ttk.Button(dialog, text="Select Conduit", command=select_conduit).pack(anchor="w", padx=12)
        lists = ttk.Frame(dialog); lists.pack(fill="both", expand=True, padx=12, pady=12)
        wires = tk.Listbox(lists); fittings = tk.Listbox(lists); wires.pack(side="left", fill="both", expand=True, padx=(0, 6)); fittings.pack(side="left", fill="both", expand=True)
        def refresh_lists():
            wires.delete(0, "end"); fittings.delete(0, "end")
            for item in run.wires: wires.insert("end", f"{item.quantity:g} × {item.catalog_number} — {item.description}")
            for item in run.fittings: fittings.insert("end", f"{item.quantity:g} × {item.catalog_number} — {item.description}")
        def add_wire():
            item, quantity = self.choose_material("Add Wire", ("WIRE",))
            if item: run.wires.append(SelectedMaterial.from_catalog(item, quantity)); refresh_lists()
        def add_fitting():
            item, quantity = self.choose_material("Add Fitting")
            if item: run.fittings.append(SelectedMaterial.from_catalog(item, quantity)); refresh_lists()
        buttons = ttk.Frame(dialog); buttons.pack(fill="x", padx=12)
        ttk.Button(buttons, text="Add Wire", command=add_wire).pack(side="left")
        ttk.Button(buttons, text="Add Fitting", command=add_fitting).pack(side="left", padx=6)
        def save():
            try: run.length_ft = float(length.get() or 0)
            except ValueError: messagebox.showerror("Invalid length", "Enter a number for length."); return
            run.name = name.get().strip() or run.name; dialog.destroy(); self.refresh_all()
        ttk.Button(dialog, text="Save Run", command=save).pack(pady=12)
        refresh_lists(); self.wait_window(dialog)

    def remove_run(self):
        run = self.selected_run()
        if run: self.project.runs.remove(run); self.refresh_all()

    def add_gutter(self):
        gutter = Gutter(name=f"Gutter {len(self.project.gutters) + 1}")
        self.project.gutters.append(gutter); self.edit_gutter(gutter)

    def selected_gutter(self):
        selected = self.gutters_tree.selection()
        return next((gutter for gutter in self.project.gutters if gutter.id == selected[0]), None) if selected else None

    def edit_gutter(self, gutter=None):
        gutter = gutter or self.selected_gutter()
        if not gutter: return
        dialog = tk.Toplevel(self); dialog.title("Edit Gutter"); dialog.geometry("650x520"); dialog.transient(self); dialog.grab_set()
        name, length = tk.StringVar(value=gutter.name), tk.StringVar(value=str(gutter.length_ft))
        ttk.Label(dialog, text="Gutter name").pack(anchor="w", padx=12, pady=(12, 0)); ttk.Entry(dialog, textvariable=name).pack(fill="x", padx=12)
        ttk.Label(dialog, text="Length (ft)").pack(anchor="w", padx=12, pady=(10, 0)); ttk.Entry(dialog, textvariable=length).pack(fill="x", padx=12)
        ttk.Label(dialog, text="Include wires from these runs").pack(anchor="w", padx=12, pady=(12, 0))
        selections = {}
        holder = ttk.Frame(dialog); holder.pack(fill="x", padx=12)
        for run in self.project.runs:
            var = tk.BooleanVar(value=run.id in gutter.included_run_ids); selections[run.id] = var
            ttk.Checkbutton(holder, text=run.name, variable=var).pack(anchor="w")
        def save():
            try: gutter.length_ft = float(length.get() or 0)
            except ValueError: messagebox.showerror("Invalid length", "Enter a number for length."); return
            gutter.name = name.get().strip() or gutter.name
            gutter.included_run_ids = [run_id for run_id, var in selections.items() if var.get()]
            dialog.destroy(); self.refresh_all()
        ttk.Button(dialog, text="Save Gutter", command=save).pack(pady=14)
        self.wait_window(dialog)

    def remove_gutter(self):
        gutter = self.selected_gutter()
        if gutter: self.project.gutters.remove(gutter); self.refresh_all()

    def refresh_all(self):
        self.runs_tree.delete(*self.runs_tree.get_children())
        for run in self.project.runs:
            self.runs_tree.insert("", "end", iid=run.id, values=(run.name, f"{run.length_ft:g}", run.conduit.catalog_number if run.conduit else "", ", ".join(item.catalog_number for item in run.wires), ", ".join(item.catalog_number for item in run.fittings)))
        self.gutters_tree.delete(*self.gutters_tree.get_children())
        names = {run.id: run.name for run in self.project.runs}
        for gutter in self.project.gutters:
            self.gutters_tree.insert("", "end", iid=gutter.id, values=(gutter.name, f"{gutter.length_ft:g}", ", ".join(names.get(run_id, "") for run_id in gutter.included_run_ids), ", ".join(item.catalog_number for item in gutter.fittings)))
        self.summary_tree.delete(*self.summary_tree.get_children())
        materials = used_materials(self.project)
        for item in materials:
            self.summary_tree.insert("", "end", values=(item.description, item.catalog_number, f"{item.quantity:g}", f"${item.price:,.2f}", f"${item.quantity * item.price:,.2f}"))
        self.total_label.config(text=f"Grand Total: ${material_total(materials):,.2f}")


if __name__ == "__main__":
    PanelBuilderLite().mainloop()
