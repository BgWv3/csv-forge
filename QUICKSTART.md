# ⚡ CSV Forge - Quickstart Guide

Welcome to CSV Forge! This guide will help you perform the most common tasks in under 2 minutes.

## 1. Launching the App

* Double-click CSV_Forge.exe.
* Wait for the splash screen to load (2-4 seconds on first run).

## 2. Opening Files

* Click the Open folder icon in the top toolbar.
* Select one or more .csv files.
* Each file will open in its own Tab.

>*Tip: You can also drag and drop a CSV file directly onto the window.*

## 3. Top 3 Common Tasks

### 🅰️ Merging Two Files (SQL Join)

*Goal: Add columns from File B into File A based on a matching ID.*

1. Open your Main File (File A).
2. Click Join Files in the sidebar.
3. Select your Secondary File (File B).
4. In the popup dialog:
    * Left Column: Select the unique ID in your Main File.
    * Right Column: Select the matching ID in the Secondary File.
    * Join Type: Choose Left to keep all rows from your Main File.
    * Click Join Tables. A new tab with the merged data will appear.

### 🅱️ Stacking Multiple Files (Combine)

*Goal: Combine 5 separate monthly reports into one big master file.*

1. Click Stack Files in the sidebar.
2. Select all 5 files at once (hold Ctrl or Shift).
3. The tool will stack them vertically and create a new tab named Combined_Result.

> *Bonus: A new column source_file is added so you know where each row came from.*

### ©️ Finding Duplicates (Fuzzy Dedupe)

*Goal: Find "John Smith" and "Jon Smith" in a messy customer list.*

1. Open your customer list CSV.
2. Click Fuzzy Dedupe in the sidebar.
3. Select the column to scan (e.g., Full Name).
4. Keep the threshold at 0.80.
5. Click OK. A report tab will open showing all potential duplicate pairs for your review.
6. Saving Your Work
    * Click the Save disk icon in the toolbar.
    * Give your new file a name.
    * *Note: This saves the currently active tab only.*

---
*Need more help? `Click Help > User Guide` inside the application.*