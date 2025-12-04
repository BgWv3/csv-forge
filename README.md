# CSV Forge

> The All-in-One CSV Manipulation Toolkit.

CSV Forge is a robust, dark-mode GUI application built with Python and PyQt5. It is designed to replace the need for writing one-off data processing scripts. It provides a spreadsheet-like interface for viewing, editing, merging, cleaning, and analyzing CSV files of any size.

## 🚀 Key Features

🖥️ **Smart Interface**
**Native Dark Mode:** Easy on the eyes for late-night data work.
**Tabbed Viewing:** Work on multiple CSVs simultaneously.
**Smart Loader:** Automatically detects file encoding (UTF-8, Latin-1, CP1252) and identifies the correct header row if metadata exists at the top of the file.
**Live Stats:** Real-time footer indicators for Row Count, Column Count, and Memory Usage.

🛠️ **The Toolbox**
**Combiner (Stack):** Merge multiple CSV files vertically into one master dataset.
**Splitter (Chunk):** Break large files into smaller, manageable chunks (e.g., 1000 rows per file).
**Joiner (SQL-Style):** Perform Left, Right, Inner, or Outer joins between two CSVs based on a common key.
**Deduplicator:** Instantly remove exact duplicate rows based on a specific column.

🧠 **Fuzzy Logic Engine**
**Fuzzy Dedupe:** Scans a single file to find rows that are almost identical (e.g., typos in names/addresses) and generates a reviewable report.
**Fuzzy Match:** Matches your current dataset against an external "Master List" (Source of Truth), identifying exact matches and partial matches with similarity scores.

✏️ **Editing & Manipulation**
**In-Cell Editing:** Double-click any cell to edit data directly.
**Context Menu:** Right-click to Add/Delete Rows or Columns.
**Column Math:** Perform arithmetic (+, -, *, /) between columns or using constant numbers.
**Concatenation:** Merge multiple columns into one (e.g., First + Last = Full Name).

## Releases

![GitHub release (latest by date)](https://img.shields.io/github/v/release/BgWv3/csv-forge)

## 📦 Installation

### Prerequisites

* Python 3.8 or higher.

### Dependencies

Install the required libraries using pip:

```python
pip install pandas PyQt5
```


## 🏃 Usage

1. **Download:** Save the script as csv_forge.py.
2. **Run:** Open your terminal/command prompt and run:

    ```python
    python csv_forge.py
    ```

### Workflow Examples

1. **Merging Two Lists (The Joiner)**
    * Open your main CSV file (The "Left" table).
    * Click Joiner in the sidebar.
    * Select the second CSV file (The "Right" table).
    * Choose the matching columns (e.g., `Email` = `Email Address`) and the Join Type (usually Left).

2. **Cleaning Dirty Data (Fuzzy Dedupe)**
    * Open a CSV containing potential duplicates.
    * Click Fuzzy Dedupe.
    * Select the column to scan (e.g., `Company Name`).
    * Set a threshold (0.8 is recommended).
    * The tool creates a new tab showing pairs of records that look similar, allowing you to decide which to keep.

3. **Preparing Data for Import (Math & Concat)**
    * Concat: Click Concatenate Columns, select `City`, `State`, and `Zip`, enter `,`  as a separator, and name the new column Full Address.
    * **Math:** Click **Column Math**, select `Subtotal`, choose `*` (multiply), select `Number` mode, enter `0.06`, and name the result `Tax`.

## 🖱️ Editing Controls

|Action|How to do it|
|--|--|
|Edit Cell|Double-click any cell.|
|Add Row|Right-click anywhere -> "Add Empty Row".|
|Delete Row|Select row(s) -> Right-click -> "Delete Selected Row(s)".|
|Rename Column|Right-click a cell in that column -> "Rename Column...".|
|Delete Column|Right-click a cell in that column -> "Delete Column...".|

## 🏗️ Building an Executable (Optional)

If you want to create a standalone `.exe` file to share with colleagues who don't have Python installed:

1. Install PyInstaller:

    ```python
    pip install pyinstaller
    ```

2. Build the app:

    ```python
    pyinstaller --noconsole --onefile --name="CSV_Forge" csv_forge.py
    ```

3. The executable will be located in the `dist/` folder.

## 📄 License

This project is open-source. Feel free to modify and distribute.