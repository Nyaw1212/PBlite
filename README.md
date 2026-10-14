# Panel Builder Lite

Panel Builder Lite is a local Windows desktop application for building electrical material takeoffs without Apps Script or Google Sheets.

## Current foundation

- Load an MML material catalog from an Excel workbook (`MML` sheet by default)
- Create, save, and open local project JSON files
- Enter project details
- Add runs with conduit, wires, fittings, and length
- Add gutters and include/exclude runs
- Build a used-materials takeoff with BOS rows first and VAN rows below
- Export `[Project Name] Used Materials.xlsx`

## Run locally

```powershell
py -m pip install -r requirements.txt
py app.py
```

## Build a Windows EXE

```powershell
py -m PyInstaller --noconfirm --onefile --windowed --name "Panel Builder Lite" app.py
```

The executable will be created in `dist\Panel Builder Lite.exe`.

## MML columns

The app recognizes these column names: `CatalogNumber`, `Description`, `Price`, `InventoryCategory`, `Type`, `Size`, `Color`, `Supplier`, `VendorCode`, and `Photo Link`.

For online material photos, add a `Photo Link` (or `Image URL` / `Drive Link`) column. The Material Picker enables **View Photo** for that material and opens the link in your default browser. Share the Drive file with everyone who will use the app.
