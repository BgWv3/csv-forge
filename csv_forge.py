import sys
import csv
import os
from difflib import SequenceMatcher

import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableView, QFileDialog, QToolBar, QStatusBar, QMessageBox,
    QTabWidget, QDockWidget, QPushButton, QLabel, QComboBox, 
    QDialog, QFormLayout, QSpinBox, QDoubleSpinBox, QProgressBar,
    QHeaderView, QMenu, QInputDialog, QAbstractItemView, 
    QListWidget, QListWidgetItem, QRadioButton, QButtonGroup, QLineEdit
)
from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtGui import QAction, QColor, QPalette

# =============================================================================
# PANDAS TABLE MODEL
# =============================================================================
class DataFrameModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame()):
        super().__init__()
        self._df = df

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                val = self._df.iloc[index.row(), index.column()]
                if pd.isna(val): return ""
                return str(val)
        return None

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            try:
                # Convert empty string to None
                if value == "":
                    val = None
                else:
                    # Try to preserve numeric type if possible
                    try:
                        if '.' in value: val = float(value)
                        else: val = int(value)
                    except ValueError:
                        val = value
                
                self._df.iloc[index.row(), index.column()] = val
                self.dataChanged.emit(index, index)
                return True
            except:
                return False
        return False

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._df.index[section])
        return None

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def sort(self, column, order):
        colname = self._df.columns[column]
        self.layoutAboutToBeChanged.emit()
        ascending = order == Qt.SortOrder.AscendingOrder
        self._df.sort_values(colname, ascending=ascending, inplace=True)
        self._df.reset_index(drop=True, inplace=True)
        self.layoutChanged.emit()

    def get_dataframe(self):
        return self._df

    # --- Editing Methods ---
    def add_row(self):
        self.layoutAboutToBeChanged.emit()
        new_index = len(self._df)
        self._df.loc[new_index] = [None] * len(self._df.columns)
        self.layoutChanged.emit()

    def add_column(self, name):
        self.layoutAboutToBeChanged.emit()
        self._df[name] = None
        self.layoutChanged.emit()

    def remove_rows(self, rows):
        self.layoutAboutToBeChanged.emit()
        self._df.drop(self._df.index[rows], inplace=True)
        self._df.reset_index(drop=True, inplace=True)
        self.layoutChanged.emit()

    def remove_column(self, col_index):
        self.layoutAboutToBeChanged.emit()
        col_name = self._df.columns[col_index]
        self._df.drop(col_name, axis=1, inplace=True)
        self.layoutChanged.emit()

    def rename_column(self, col_index, new_name):
        self.layoutAboutToBeChanged.emit()
        old_name = self._df.columns[col_index]
        self._df.rename(columns={old_name: new_name}, inplace=True)
        self.layoutChanged.emit()


# =============================================================================
# DIALOGS
# =============================================================================
class JoinDialog(QDialog):
    def __init__(self, left_cols, right_cols, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Join Configuration")
        self.layout = QFormLayout(self)
        self.left_combo = QComboBox()
        self.left_combo.addItems(left_cols)
        self.right_combo = QComboBox()
        self.right_combo.addItems(right_cols)
        self.type_combo = QComboBox()
        self.type_combo.addItems(['inner', 'left', 'right', 'outer'])
        self.layout.addRow("Left Table Column:", self.left_combo)
        self.layout.addRow("Right Table Column:", self.right_combo)
        self.layout.addRow("Join Type:", self.type_combo)
        btn_box = QHBoxLayout()
        ok_btn = QPushButton("Join")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)
        self.layout.addRow(btn_box)
    def get_data(self):
        return self.left_combo.currentText(), self.right_combo.currentText(), self.type_combo.currentText()

class ConcatDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Concatenate Columns")
        self.resize(400, 500)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select columns to combine (in order):"))
        self.col_list = QListWidget()
        for col in columns:
            item = QListWidgetItem(col)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.col_list.addItem(item)
        layout.addWidget(self.col_list)

        form = QFormLayout()
        self.sep_input = QLineEdit()
        self.sep_input.setPlaceholderText("e.g. ' ' or '-' or leave empty")
        self.name_input = QLineEdit("New_Column")
        
        form.addRow("Separator:", self.sep_input)
        form.addRow("New Column Name:", self.name_input)
        layout.addLayout(form)

        btns = QHBoxLayout()
        ok = QPushButton("Create")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)

    def get_data(self):
        selected = []
        for i in range(self.col_list.count()):
            item = self.col_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected, self.sep_input.text(), self.name_input.text()

class MathDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Column Math")
        layout = QVBoxLayout(self)

        form = QFormLayout()
        
        self.new_col = QLineEdit("Result")
        self.col_a = QComboBox()
        self.col_a.addItems(columns)
        self.op = QComboBox()
        self.op.addItems(["+", "-", "*", "/"])
        
        # Operand B selection
        self.rb_col = QRadioButton("Column")
        self.rb_num = QRadioButton("Number")
        self.rb_col.setChecked(True)
        self.bg = QButtonGroup()
        self.bg.addButton(self.rb_col)
        self.bg.addButton(self.rb_num)
        
        self.col_b = QComboBox()
        self.col_b.addItems(columns)
        self.num_b = QDoubleSpinBox()
        self.num_b.setRange(-999999999, 999999999)
        self.num_b.setVisible(False)
        
        # Toggle visibility
        self.rb_col.toggled.connect(lambda: self.toggle_b(True))
        self.rb_num.toggled.connect(lambda: self.toggle_b(False))

        form.addRow("New Column Name:", self.new_col)
        form.addRow("Column A:", self.col_a)
        form.addRow("Operator:", self.op)
        
        b_layout = QHBoxLayout()
        b_layout.addWidget(self.rb_col)
        b_layout.addWidget(self.rb_num)
        form.addRow("Calculate with:", b_layout)
        
        self.stack_widget = QWidget()
        self.stack_layout = QVBoxLayout(self.stack_widget)
        self.stack_layout.setContentsMargins(0,0,0,0)
        self.stack_layout.addWidget(self.col_b)
        self.stack_layout.addWidget(self.num_b)
        form.addRow("Operand B:", self.stack_widget)
        
        layout.addLayout(form)

        btns = QHBoxLayout()
        ok = QPushButton("Calculate")
        ok.clicked.connect(self.accept)
        layout.addWidget(ok)
        layout.addLayout(btns)

    def toggle_b(self, is_col):
        self.col_b.setVisible(is_col)
        self.num_b.setVisible(not is_col)

    def get_data(self):
        mode = "col" if self.rb_col.isChecked() else "num"
        val_b = self.col_b.currentText() if mode == "col" else self.num_b.value()
        return self.new_col.text(), self.col_a.currentText(), self.op.currentText(), mode, val_b

# =============================================================================
# MAIN APPLICATION
# =============================================================================
class CSVForge(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Forge - Advanced Toolkit")
        self.resize(1200, 800)
        self.apply_dark_theme()

        # State
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_footer_stats)
        self.setCentralWidget(self.tabs)

        # Setup UI Components
        self.create_menu()
        self.create_toolbar()
        self.create_sidebar()
        self.create_statusbar()

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        QApplication.setPalette(palette)

    def create_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        open_action = QAction("Open CSV...", self)
        open_action.triggered.connect(self.load_csv)
        file_menu.addAction(open_action)
        save_action = QAction("Save Current Tab", self)
        save_action.triggered.connect(self.save_csv)
        file_menu.addAction(save_action)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        btn_open = QAction("📂 Open", self)
        btn_open.triggered.connect(self.load_csv)
        toolbar.addAction(btn_open)
        btn_save = QAction("💾 Save", self)
        btn_save.triggered.connect(self.save_csv)
        toolbar.addAction(btn_save)

    def create_sidebar(self):
        dock = QDockWidget("Toolbox", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Define your tools in Groups (Header Name, List of Tools)
        tool_groups = [
            ("File Operations", [
                ("Combiner (Stack Files)", self.tool_combiner),
                ("Splitter (Chunk File)", self.tool_splitter),
                ("Joiner (Merge Columns)", self.tool_joiner),
                ("Remove Exact Duplicates", self.tool_remove_duplicates),
            ]),
            ("Fuzzy Logic", [
                ("Fuzzy Dedupe (Current)", self.tool_fuzzy_dedupe),
                ("Fuzzy Match (External)", self.tool_fuzzy_match),
            ]),
            ("Calculations & Edits", [
                ("Concatenate Columns", self.tool_concatenate),
                ("Column Math", self.tool_calculate)
            ])
        ]

        # Loop through the groups
        for header, tools in tool_groups:
            # 1. Add the Section Header
            lbl = QLabel(header)
            # Styling: Bold, light grey text, with some top margin for spacing
            lbl.setStyleSheet("font-weight: bold; color: #aaa; margin-top: 15px; margin-bottom: 5px;")
            layout.addWidget(lbl)

            # 2. Add the Buttons for this group
            for name, func in tools:
                btn = QPushButton(name)
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 8px; 
                        text-align: left;
                        background-color: #444;
                        border: none;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #555;
                    }
                    QPushButton:pressed {
                        background-color: #2a82da;
                    }
                """)
                btn.clicked.connect(func)
                layout.addWidget(btn)

        widget.setLayout(layout)
        dock.setWidget(widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    def create_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.lbl_rows = QLabel("Rows: 0")
        self.lbl_cols = QLabel("Cols: 0")
        self.lbl_mem = QLabel("Mem: 0 MB")
        style = "padding: 0 10px; font-weight: bold; color: #ccc;"
        self.lbl_rows.setStyleSheet(style)
        self.lbl_cols.setStyleSheet(style)
        self.lbl_mem.setStyleSheet(style)
        self.status_bar.addPermanentWidget(self.lbl_rows)
        self.status_bar.addPermanentWidget(self.lbl_cols)
        self.status_bar.addPermanentWidget(self.lbl_mem)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress)

    def update_footer_stats(self):
        df = self.get_current_df()
        if df is not None:
            rows = df.shape[0]
            cols = df.shape[1]
            mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            self.lbl_rows.setText(f"Rows: {rows:,}")
            self.lbl_cols.setText(f"Cols: {cols}")
            self.lbl_mem.setText(f"Mem: {mem_mb:.2f} MB")
        else:
            self.lbl_rows.setText("Rows: 0")
            self.lbl_cols.setText("Cols: 0")
            self.lbl_mem.setText("Mem: 0 MB")

    # --- File Operations ---
    def detect_encoding(self, filepath):
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    f.readline()
                return enc
            except: continue
        return 'utf-8'

    def find_valid_header_row(self, filepath, encoding):
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                lines = [f.readline() for _ in range(50)]
            max_commas = 0
            best_row = 0
            for i, line in enumerate(lines):
                if not line.strip(): continue 
                commas = line.count(',')
                if commas > max_commas:
                    max_commas = commas
                    best_row = i
            return best_row if max_commas > 0 else None
        except: return None

    def load_csv(self):
        fnames, _ = QFileDialog.getOpenFileNames(self, "Open CSV", "", "CSV Files (*.csv)")
        if not fnames: return
        for fname in fnames:
            try:
                enc = self.detect_encoding(fname)
                try:
                    df = pd.read_csv(fname, encoding=enc)
                except pd.errors.ParserError:
                    skip_rows = self.find_valid_header_row(fname, enc)
                    if skip_rows is not None and skip_rows > 0:
                        df = pd.read_csv(fname, encoding=enc, skiprows=skip_rows)
                        self.status_bar.showMessage(f"Auto-detected header at row {skip_rows + 1}")
                    else:
                        rows, ok = QInputDialog.getInt(self, "Import Error", "Structure mismatch detected.\nHeader rows to skip?", 0, 0, 100)
                        if ok: df = pd.read_csv(fname, encoding=enc, skiprows=rows)
                        else: raise
                df.columns = df.columns.str.strip()
                self.create_tab(df, os.path.basename(fname))
                if "Auto-detected" not in self.status_bar.currentMessage():
                    self.status_bar.showMessage(f"Loaded {fname} ({enc})")
            except Exception as e: QMessageBox.critical(self, "Error", f"Could not open {fname}\n{str(e)}")

    def create_tab(self, df, title):
        view = QTableView()
        model = DataFrameModel(df)
        view.setModel(model)
        view.setSortingEnabled(True)
        view.horizontalHeader().setStretchLastSection(True)
        view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        view.customContextMenuRequested.connect(lambda pos: self.show_context_menu(pos, view))
        idx = self.tabs.addTab(view, title)
        self.tabs.setCurrentIndex(idx)
        self.update_footer_stats()

    def close_tab(self, index):
        self.tabs.removeTab(index)
        self.update_footer_stats()

    def get_current_df(self):
        current_widget = self.tabs.currentWidget()
        if current_widget:
            return current_widget.model().get_dataframe()
        return None

    def save_csv(self):
        df = self.get_current_df()
        if df is None: return
        fname, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if fname:
            try:
                df.to_csv(fname, index=False)
                self.status_bar.showMessage(f"Saved to {fname}")
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    # --- CONTEXT MENU ---
    def show_context_menu(self, pos, view):
        menu = QMenu(self)
        model = view.model()
        index = view.indexAt(pos)
        selected_rows = sorted(set(idx.row() for idx in view.selectionModel().selectedRows()))
        
        add_row_act = QAction("Add Empty Row", self)
        add_row_act.triggered.connect(lambda: [model.add_row(), self.update_footer_stats()])
        menu.addAction(add_row_act)
        
        add_col_act = QAction("Add Column...", self)
        add_col_act.triggered.connect(lambda: self.prompt_add_column(model))
        menu.addAction(add_col_act)
        
        menu.addSeparator()
        
        if selected_rows:
            del_row_act = QAction(f"Delete {len(selected_rows)} Selected Row(s)", self)
            del_row_act.triggered.connect(lambda: [model.remove_rows(selected_rows), self.update_footer_stats()])
            menu.addAction(del_row_act)
        
        if index.isValid():
            col_idx = index.column()
            col_name = model.headerData(col_idx, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            menu.addSeparator()
            rename_act = QAction(f"Rename Column '{col_name}'...", self)
            rename_act.triggered.connect(lambda: self.prompt_rename_column(model, col_idx, col_name))
            menu.addAction(rename_act)
            del_col_act = QAction(f"Delete Column '{col_name}'", self)
            del_col_act.triggered.connect(lambda: [model.remove_column(col_idx), self.update_footer_stats()])
            menu.addAction(del_col_act)

        menu.exec(view.viewport().mapToGlobal(pos))

    def prompt_add_column(self, model):
        name, ok = QInputDialog.getText(self, "Add Column", "New Column Name:")
        if ok and name:
            model.add_column(name)
            self.update_footer_stats()

    def prompt_rename_column(self, model, col_idx, old_name):
        name, ok = QInputDialog.getText(self, "Rename Column", "New Name:", text=old_name)
        if ok and name:
            model.rename_column(col_idx, name)

    # --- TOOLS ---
    def tool_combiner(self):
        fnames, _ = QFileDialog.getOpenFileNames(self, "Select CSVs", "", "CSV (*.csv)")
        if not fnames: return
        dfs = []
        if self.get_current_df() is not None:
            if QMessageBox.question(self, "Append?", "Append to current table?") == QMessageBox.StandardButton.Yes:
                dfs.append(self.get_current_df())
        self.progress.setVisible(True)
        try:
            for i, f in enumerate(fnames):
                d = pd.read_csv(f, encoding=self.detect_encoding(f))
                d['source_file'] = os.path.basename(f)
                dfs.append(d)
                self.progress.setValue(int((i+1)/len(fnames)*100))
            self.create_tab(pd.concat(dfs, ignore_index=True), "Combined")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))
        finally: self.progress.setVisible(False)

    def tool_splitter(self):
        df = self.get_current_df()
        if df is None: return
        rows, ok = QInputDialog.getInt(self, "Split", "Rows per file:", 1000, 1)
        if ok:
            d = QFileDialog.getExistingDirectory(self, "Output Dir")
            if d:
                try:
                    for i in range((len(df)//rows)+1):
                        df.iloc[i*rows:(i+1)*rows].to_csv(os.path.join(d, f"split_{i+1}.csv"), index=False)
                    QMessageBox.information(self, "Done", "Split complete")
                except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def tool_joiner(self):
        left = self.get_current_df()
        if left is None: return
        fname, _ = QFileDialog.getOpenFileName(self, "Right CSV", "", "CSV (*.csv)")
        if not fname: return
        try:
            right = pd.read_csv(fname, encoding=self.detect_encoding(fname))
            right.columns = right.columns.str.strip()
            d = JoinDialog(left.columns, right.columns, self)
            if d.exec():
                l, r, t = d.get_data()
                if l == r: res = pd.merge(left, right, on=l, how=t)
                else: res = pd.merge(left, right, left_on=l, right_on=r, how=t)
                self.create_tab(res, f"Join_{t}")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def tool_remove_duplicates(self):
        df = self.get_current_df()
        if df is None: return
        col, ok = QInputDialog.getItem(self, "Deduplicate", "Column:", df.columns.tolist(), 0, False)
        if ok:
            if QMessageBox.question(self, "Confirm", "Keep first occurrence only?") == QMessageBox.StandardButton.Yes:
                try:
                    before = len(df)
                    df.drop_duplicates(subset=[col], keep='first', inplace=True)
                    df.reset_index(drop=True, inplace=True)
                    self.tabs.currentWidget().model().layoutChanged.emit()
                    self.update_footer_stats()
                    QMessageBox.information(self, "Done", f"Removed {before - len(df)} rows.")
                except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def tool_concatenate(self):
        df = self.get_current_df()
        if df is None: return
        d = ConcatDialog(df.columns, self)
        if d.exec():
            cols, sep, name = d.get_data()
            if not cols:
                QMessageBox.warning(self, "Warning", "Select at least one column")
                return
            try:
                self.tabs.currentWidget().model().layoutAboutToBeChanged.emit()
                df[name] = df[cols[0]].astype(str)
                for c in cols[1:]:
                    df[name] = df[name] + sep + df[c].astype(str)
                self.tabs.currentWidget().model().layoutChanged.emit()
                self.update_footer_stats()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def tool_calculate(self):
        df = self.get_current_df()
        if df is None: return
        d = MathDialog(df.columns, self)
        if d.exec():
            new_col, col_a, op, mode, val_b = d.get_data()
            try:
                self.tabs.currentWidget().model().layoutAboutToBeChanged.emit()
                
                # Convert col A to numeric (coercing errors)
                s_a = pd.to_numeric(df[col_a], errors='coerce').fillna(0)
                
                if mode == "col":
                    s_b = pd.to_numeric(df[val_b], errors='coerce').fillna(0)
                else:
                    s_b = float(val_b)
                
                if op == "+": df[new_col] = s_a + s_b
                elif op == "-": df[new_col] = s_a - s_b
                elif op == "*": df[new_col] = s_a * s_b
                elif op == "/": df[new_col] = s_a / s_b
                
                self.tabs.currentWidget().model().layoutChanged.emit()
                self.update_footer_stats()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def tool_fuzzy_dedupe(self):
        df = self.get_current_df()
        if df is None: return
        col, ok = QInputDialog.getItem(self, "Fuzzy Dedupe", "Column:", df.columns.tolist(), 0, False)
        if not ok: return
        thresh, ok = QInputDialog.getDouble(self, "Threshold", "0.0-1.0:", 0.8, 0, 1, 2)
        if not ok: return

        self.progress.setVisible(True)
        QApplication.processEvents()
        try:
            recs = df.to_dict('records')
            cols = df.columns.tolist()
            matches = []
            for i in range(len(recs)):
                if i % 50 == 0: 
                    self.progress.setValue(int(i/len(recs)*100))
                    QApplication.processEvents()
                for j in range(i+1, len(recs)):
                    s1, s2 = str(recs[i].get(col,'')), str(recs[j].get(col,''))
                    if not s1 or not s2 or s1=='nan' or s2=='nan': continue
                    ratio = SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
                    if ratio >= thresh:
                        row = {'Row_1': i+2, 'Row_2': j+2, 'Score': f"{ratio:.2%}", 'Action': 'REVIEW'}
                        for c in cols: row[f"{c}_1"] = recs[i].get(c,'')
                        for c in cols: row[f"{c}_2"] = recs[j].get(c,'')
                        matches.append(row)
            if matches:
                final_cols = ['Row_1', 'Row_2', 'Score'] + [f"{c}_1" for c in cols] + [f"{c}_2" for c in cols] + ['Action']
                self.create_tab(pd.DataFrame(matches)[final_cols], "Fuzzy_Dupes")
            else: QMessageBox.information(self, "Result", "No duplicates found.")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))
        finally: self.progress.setVisible(False)

    def tool_fuzzy_match(self):
        target = self.get_current_df()
        if target is None: return
        fname, _ = QFileDialog.getOpenFileName(self, "Master CSV", "", "CSV (*.csv)")
        if not fname: return
        try:
            master = pd.read_csv(fname, encoding=self.detect_encoding(fname))
            c_t, ok1 = QInputDialog.getItem(self, "Target Col", "Current Table:", target.columns.tolist(), 0, False)
            if not ok1: return
            c_m, ok2 = QInputDialog.getItem(self, "Master Col", "Master Table:", master.columns.tolist(), 0, False)
            if not ok2: return
            thresh, ok3 = QInputDialog.getDouble(self, "Threshold", "0.0-1.0:", 0.8, 0, 1, 2)
            if not ok3: return

            self.progress.setVisible(True)
            QApplication.processEvents()
            res = []
            m_vals = master[c_m].dropna().astype(str).tolist()
            for i, row in target.iterrows():
                if i % 10 == 0: self.progress.setValue(int(i/len(target)*100))
                t_val = str(row[c_t])
                best_r, best_v = 0, None
                for m in m_vals:
                    r = SequenceMatcher(None, t_val.lower(), m.lower()).ratio()
                    if r > best_r: best_r, best_v = r, m
                d = row.to_dict()
                d['Match_Status'] = "Exact" if best_r==1.0 else ("Fuzzy" if best_r>=thresh else "No Match")
                d['Best_Match'] = best_v if best_r>=thresh else None
                d['Score'] = round(best_r, 3)
                res.append(d)
            self.create_tab(pd.DataFrame(res), "Matched_Results")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))
        finally: self.progress.setVisible(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVForge()
    window.show()
    sys.exit(app.exec())