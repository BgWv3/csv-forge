import sys
import csv
import os
import time
from difflib import SequenceMatcher

import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableView, QFileDialog, QToolBar, QStatusBar, QMessageBox,
    QTabWidget, QDockWidget, QPushButton, QLabel, QComboBox, 
    QDialog, QFormLayout, QSpinBox, QDoubleSpinBox, QProgressBar,
    QHeaderView, QMenu, QInputDialog, QAbstractItemView, 
    QListWidget, QListWidgetItem, QRadioButton, QButtonGroup, QLineEdit,
    QTextBrowser, QSplashScreen, QAction
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QSize, QTimer
from PyQt5.QtGui import (
    QColor, QPalette, QPixmap, QPainter, 
    QFont, QIcon, QBrush, QPen
)

# =============================================================================
# APP CONFIGURATION
# =============================================================================
APP_NAME = "CSV Forge"
VERSION = "1.3.2"  # Bumped version for "Open on Launch" support

# =============================================================================
# ASSET GENERATORS
# =============================================================================
def create_app_icon():
    size = 128
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Modern Flat Circle Background
    brush = QBrush(QColor("#3d72b4")) 
    painter.setBrush(brush)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)
    
    # Text
    painter.setPen(QColor("white"))
    font = QFont("Segoe UI", 40, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "CSV")
    painter.end()
    return QIcon(pixmap)

def create_splash_pixmap():
    width, height = 500, 300
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#2b2b2b"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Minimalist Border
    pen = QPen(QColor("#3d72b4"))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawRect(0, 0, width, height)
    
    # Title
    painter.setPen(QColor("white"))
    title_font = QFont("Segoe UI", 36, QFont.Bold)
    painter.setFont(title_font)
    text_rect = pixmap.rect()
    text_rect.setBottom(text_rect.bottom() - 60)
    painter.drawText(text_rect, Qt.AlignCenter, APP_NAME)
    
    # Subtitle
    painter.setPen(QColor("#aaaaaa"))
    sub_font = QFont("Segoe UI", 12)
    painter.setFont(sub_font)
    painter.drawText(width - 120, height - 20, f"v{VERSION}")
    
    # Loading
    painter.setPen(QColor("#3d72b4"))
    loading_font = QFont("Segoe UI", 10, QFont.Bold)
    painter.setFont(loading_font)
    painter.drawText(20, height - 20, "Loading Environment...")
    
    painter.end()
    return pixmap

# =============================================================================
# DATA MODEL
# =============================================================================
class DataFrameModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame()):
        super().__init__()
        self._df = df

    def rowCount(self, parent=None): return self._df.shape[0]
    def columnCount(self, parent=None): return self._df.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole or role == Qt.EditRole:
                val = self._df.iloc[index.row(), index.column()]
                if pd.isna(val): return ""
                return str(val)
        return None

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            try:
                val = None if value == "" else value
                if val:
                    try:
                        if '.' in val: val = float(val)
                        else: val = int(val)
                    except: pass
                self._df.iloc[index.row(), index.column()] = val
                self.dataChanged.emit(index, index)
                return True
            except: return False
        return False

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal: return str(self._df.columns[section])
            if orientation == Qt.Vertical: return str(self._df.index[section])
        return None

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def sort(self, column, order):
        colname = self._df.columns[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(colname, ascending=(order == Qt.AscendingOrder), inplace=True)
        self._df.reset_index(drop=True, inplace=True)
        self.layoutChanged.emit()
    
    def get_dataframe(self): return self._df
    
    def add_row(self):
        self.layoutAboutToBeChanged.emit()
        self._df.loc[len(self._df)] = [None] * len(self._df.columns)
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
        self._df.drop(self._df.columns[col_index], axis=1, inplace=True)
        self.layoutChanged.emit()
    
    def rename_column(self, col_index, new_name):
        self.layoutAboutToBeChanged.emit()
        self._df.rename(columns={self._df.columns[col_index]: new_name}, inplace=True)
        self.layoutChanged.emit()

# =============================================================================
# DIALOGS
# =============================================================================
class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - User Guide")
        self.resize(700, 600)
        layout = QVBoxLayout(self)
        self.text_browser = QTextBrowser()
        self.text_browser.setHtml(f"""
            <h1 style="color: #3d72b4;">{APP_NAME} <span style="font-size: 14px; color: #666;">v{VERSION}</span></h1>
            <p>Your all-in-one toolkit for manipulating CSV files.</p>
            <hr>
            <h3>🚀 Quick Start</h3>
            <ul>
                <li><b>Open:</b> File > Open CSV</li>
                <li><b>Edit:</b> Double-click cells</li>
                <li><b>Save:</b> File > Save Current Tab</li>
            </ul>
        """)
        layout.addWidget(self.text_browser)
        btn = QPushButton("Close")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class JoinDialog(QDialog):
    def __init__(self, left_cols, right_cols, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Join Configuration")
        self.resize(400, 200)
        self.layout = QFormLayout(self)
        self.left_combo = QComboBox()
        self.left_combo.addItems(left_cols)
        self.right_combo = QComboBox()
        self.right_combo.addItems(right_cols)
        self.type_combo = QComboBox()
        self.type_combo.addItems(['inner', 'left', 'right', 'outer'])
        self.layout.addRow("Left Column:", self.left_combo)
        self.layout.addRow("Right Column:", self.right_combo)
        self.layout.addRow("Join Type:", self.type_combo)
        btn_box = QHBoxLayout()
        ok_btn = QPushButton("Join Tables")
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
        layout.addWidget(QLabel("Select columns to combine:"))
        self.col_list = QListWidget()
        for col in columns:
            item = QListWidgetItem(col)
            item.setCheckState(Qt.Unchecked)
            self.col_list.addItem(item)
        layout.addWidget(self.col_list)
        form = QFormLayout()
        self.sep_input = QLineEdit()
        self.sep_input.setPlaceholderText("e.g. ' ' or '-'")
        self.name_input = QLineEdit("New_Column")
        form.addRow("Separator:", self.sep_input)
        form.addRow("New Name:", self.name_input)
        layout.addLayout(form)
        btns = QHBoxLayout()
        ok = QPushButton("Create Column")
        ok.clicked.connect(self.accept)
        btns.addWidget(ok)
        layout.addLayout(btns)
    def get_data(self):
        selected = [self.col_list.item(i).text() for i in range(self.col_list.count()) if self.col_list.item(i).checkState() == Qt.Checked]
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
        self.rb_col = QRadioButton("Column")
        self.rb_num = QRadioButton("Number")
        self.rb_col.setChecked(True)
        self.bg = QButtonGroup()
        self.bg.addButton(self.rb_col)
        self.bg.addButton(self.rb_num)
        self.col_b = QComboBox()
        self.col_b.addItems(columns)
        self.num_b = QDoubleSpinBox()
        self.num_b.setRange(-1e9, 1e9)
        self.num_b.setVisible(False)
        self.rb_col.toggled.connect(lambda: [self.col_b.setVisible(True), self.num_b.setVisible(False)])
        self.rb_num.toggled.connect(lambda: [self.col_b.setVisible(False), self.num_b.setVisible(True)])
        form.addRow("New Name:", self.new_col)
        form.addRow("Column A:", self.col_a)
        form.addRow("Operator:", self.op)
        b_layout = QHBoxLayout()
        b_layout.addWidget(self.rb_col)
        b_layout.addWidget(self.rb_num)
        form.addRow("With:", b_layout)
        stack = QWidget()
        stack_l = QVBoxLayout(stack)
        stack_l.setContentsMargins(0,0,0,0)
        stack_l.addWidget(self.col_b)
        stack_l.addWidget(self.num_b)
        form.addRow("Operand B:", stack)
        layout.addLayout(form)
        ok = QPushButton("Calculate")
        ok.clicked.connect(self.accept)
        layout.addWidget(ok)
    def get_data(self):
        mode = "col" if self.rb_col.isChecked() else "num"
        val_b = self.col_b.currentText() if mode == "col" else self.num_b.value()
        return self.new_col.text(), self.col_a.currentText(), self.op.currentText(), mode, val_b

# =============================================================================
# MAIN WINDOW
# =============================================================================
class CSVForge(QMainWindow):
    def __init__(self, file_to_open=None):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.resize(1200, 800)
        self.setWindowIcon(create_app_icon())
        
        self.apply_modern_theme()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_footer_stats)
        self.setCentralWidget(self.tabs)

        self.create_menu()
        self.create_toolbar()
        self.create_sidebar()
        self.create_statusbar()
        
        # Check if file was passed during initialization (Double-Click Launch)
        if file_to_open and os.path.exists(file_to_open):
            self.load_specific_file(file_to_open)

    def apply_modern_theme(self):
        QApplication.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setPalette(palette)

        self.setStyleSheet("""
            QMainWindow { background-color: #353535; }
            QToolTip { color: #ffffff; background-color: #2a2a2a; border: 1px solid white; }
            QMenuBar { background-color: #353535; color: white; }
            QMenuBar::item:selected { background-color: #3d72b4; }
            QMenu { background-color: #2b2b2b; color: white; border: 1px solid #555; }
            QMenu::item:selected { background-color: #3d72b4; }
            QTableView { background-color: #252525; gridline-color: #444; color: #ddd; selection-background-color: #3d72b4; selection-color: white; }
            QHeaderView::section { background-color: #353535; color: white; padding: 4px; border: 1px solid #444; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #353535; color: #aaa; padding: 8px 16px; border: 1px solid #444; border-bottom: none; }
            QTabBar::tab:selected { background: #252525; color: white; border-top: 2px solid #3d72b4; }
            QPushButton { background-color: #444; border: 1px solid #555; color: white; padding: 6px 12px; border-radius: 4px; }
            QPushButton:hover { background-color: #505050; border: 1px solid #3d72b4; }
            QPushButton:pressed { background-color: #3d72b4; }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background-color: #252525; border: 1px solid #555; color: white; padding: 4px; border-radius: 3px; }
            QComboBox::drop-down { border: none; }
            QScrollBar:vertical { border: none; background: #2b2b2b; width: 10px; margin: 0; }
            QScrollBar::handle:vertical { background: #555; min-height: 20px; border-radius: 5px; }
            QScrollBar::handle:vertical:hover { background: #3d72b4; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

    def create_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        file_menu.addAction("Open CSV...", self.load_csv)
        file_menu.addAction("Save Current Tab", self.save_csv)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        help_menu = menu.addMenu("Help")
        help_menu.addAction("User Guide", self.show_help)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        btn_open = QAction("📂 Open", self)
        btn_open.triggered.connect(self.load_csv)
        toolbar.addAction(btn_open)
        btn_save = QAction("💾 Save", self)
        btn_save.triggered.connect(self.save_csv)
        toolbar.addAction(btn_save)

    def create_sidebar(self):
        dock = QDockWidget("Toolbox", self)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        sidebar_btn_style = """
            QPushButton {
                text-align: left;
                padding: 10px;
                background-color: #2b2b2b;
                border: none;
                border-radius: 5px;
                margin-bottom: 2px;
            }
            QPushButton:hover {
                background-color: #3d72b4;
                color: white;
            }
        """

        groups = [
            ("File Operations", [
                ("Stack Files", self.tool_combiner),
                ("Split File", self.tool_splitter),
                ("Join Files", self.tool_joiner),
                ("Remove Duplicates", self.tool_remove_duplicates),
            ]),
            ("Fuzzy Logic", [
                ("Fuzzy Dedupe", self.tool_fuzzy_dedupe),
                ("Fuzzy Match (External)", self.tool_fuzzy_match),
            ]),
            ("Calculations", [
                ("Concatenate", self.tool_concatenate),
                ("Math Operations", self.tool_calculate)
            ])
        ]

        for header, tools in groups:
            lbl = QLabel(header.upper())
            lbl.setStyleSheet("color: #888; font-weight: bold; font-size: 11px; margin-top: 15px; margin-bottom: 5px;")
            layout.addWidget(lbl)
            for name, func in tools:
                btn = QPushButton(f"  {name}")
                btn.setStyleSheet(sidebar_btn_style)
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(func)
                layout.addWidget(btn)

        widget.setLayout(layout)
        dock.setWidget(widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def create_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.lbl_rows = QLabel("Rows: 0")
        self.lbl_cols = QLabel("Cols: 0")
        self.lbl_mem = QLabel("Mem: 0 MB")
        lbl_style = "color: #aaa; padding: 0 10px; font-family: monospace;"
        self.lbl_rows.setStyleSheet(lbl_style)
        self.lbl_cols.setStyleSheet(lbl_style)
        self.lbl_mem.setStyleSheet(lbl_style)
        self.status_bar.addPermanentWidget(self.lbl_rows)
        self.status_bar.addPermanentWidget(self.lbl_cols)
        self.status_bar.addPermanentWidget(self.lbl_mem)
        self.progress = QProgressBar()
        self.progress.setStyleSheet("QProgressBar { border: 1px solid #555; border-radius: 2px; text-align: center; background: #252525; color: white; } QProgressBar::chunk { background-color: #3d72b4; }")
        self.progress.setFixedWidth(150)
        self.progress.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress)

    def update_footer_stats(self):
        df = self.get_current_df()
        if df is not None:
            rows, cols = df.shape
            mem = df.memory_usage(deep=True).sum() / (1024**2)
            self.lbl_rows.setText(f"Rows: {rows:,}")
            self.lbl_cols.setText(f"Cols: {cols}")
            self.lbl_mem.setText(f"Mem: {mem:.2f} MB")
        else:
            self.lbl_rows.setText("Rows: 0")
            self.lbl_cols.setText("Cols: 0")
            self.lbl_mem.setText("Mem: 0 MB")

    def detect_encoding(self, filepath):
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f: f.readline()
                return enc
            except: continue
        return 'utf-8'

    def find_valid_header_row(self, filepath, encoding):
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                lines = [f.readline() for _ in range(50)]
            max_c, best_r = 0, 0
            for i, line in enumerate(lines):
                if not line.strip(): continue
                c = line.count(',')
                if c > max_c: max_c, best_r = c, i
            return best_r if max_c > 0 else None
        except: return None

    # NEW METHOD: Load specific file directly (Refactored logic)
    def load_specific_file(self, fname):
        try:
            enc = self.detect_encoding(fname)
            try:
                df = pd.read_csv(fname, encoding=enc)
            except:
                skip = self.find_valid_header_row(fname, enc)
                if skip: 
                    df = pd.read_csv(fname, encoding=enc, skiprows=skip)
                    self.status_bar.showMessage(f"Auto-detected header at row {skip+1}")
                else: raise
            df.columns = df.columns.str.strip()
            self.create_tab(df, os.path.basename(fname))
            if "Auto" not in self.status_bar.currentMessage():
                self.status_bar.showMessage(f"Loaded {fname}")
        except Exception as e: QMessageBox.critical(self, "Error", f"Could not load file:\n{str(e)}")

    def load_csv(self):
        fnames, _ = QFileDialog.getOpenFileNames(self, "Open CSV", "", "CSV Files (*.csv)")
        if not fnames: return
        for fname in fnames:
            self.load_specific_file(fname)

    def create_tab(self, df, title):
        view = QTableView()
        model = DataFrameModel(df)
        view.setModel(model)
        view.setSortingEnabled(True)
        view.horizontalHeader().setStretchLastSection(True)
        view.setAlternatingRowColors(True)
        view.setContextMenuPolicy(Qt.CustomContextMenu)
        view.customContextMenuRequested.connect(lambda pos: self.show_context_menu(pos, view))
        self.tabs.addTab(view, title)
        self.tabs.setCurrentIndex(self.tabs.count()-1)
        self.update_footer_stats()

    def close_tab(self, index):
        self.tabs.removeTab(index)
        self.update_footer_stats()

    def get_current_df(self):
        if self.tabs.currentWidget(): return self.tabs.currentWidget().model().get_dataframe()
        return None

    def save_csv(self):
        df = self.get_current_df()
        if df is None: return
        fname, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if fname:
            try:
                df.to_csv(fname, index=False)
                self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(fname))
                self.status_bar.showMessage(f"Saved {fname}")
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def show_help(self):
        HelpDialog(self).exec_()

    def show_context_menu(self, pos, view):
        menu = QMenu(self)
        model = view.model()
        idx = view.indexAt(pos)
        rows = sorted(set(i.row() for i in view.selectionModel().selectedRows()))
        
        menu.addAction("Add Empty Row", lambda: [model.add_row(), self.update_footer_stats()])
        menu.addAction("Add Column...", lambda: self.prompt_add_column(model))
        menu.addSeparator()
        if rows: menu.addAction(f"Delete {len(rows)} Row(s)", lambda: [model.remove_rows(rows), self.update_footer_stats()])
        if idx.isValid():
            c_idx = idx.column()
            c_name = model.headerData(c_idx, Qt.Horizontal, Qt.DisplayRole)
            menu.addAction(f"Rename '{c_name}'...", lambda: self.prompt_rename_column(model, c_idx, c_name))
            menu.addAction(f"Delete '{c_name}'", lambda: [model.remove_column(c_idx), self.update_footer_stats()])
        menu.exec_(view.viewport().mapToGlobal(pos))

    def prompt_add_column(self, model):
        name, ok = QInputDialog.getText(self, "Add Column", "Name:")
        if ok and name: 
            model.add_column(name)
            self.update_footer_stats()

    def prompt_rename_column(self, model, idx, old):
        name, ok = QInputDialog.getText(self, "Rename", "Name:", text=old)
        if ok and name: model.rename_column(idx, name)

    # --- Tools ---
    def tool_combiner(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select CSVs", "", "CSV (*.csv)")
        if not files: return
        dfs = []
        if self.get_current_df() is not None:
            if QMessageBox.question(self, "Append?", "Append to current tab?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                dfs.append(self.get_current_df())
        
        self.progress.setVisible(True)
        try:
            for i, f in enumerate(files):
                d = pd.read_csv(f, encoding=self.detect_encoding(f))
                d['source_file'] = os.path.basename(f)
                dfs.append(d)
                self.progress.setValue(int((i+1)/len(files)*100))
                QApplication.processEvents()
            self.create_tab(pd.concat(dfs, ignore_index=True), "Combined_Result")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))
        finally: self.progress.setVisible(False)

    def tool_splitter(self):
        df = self.get_current_df()
        if df is None: return
        rows, ok = QInputDialog.getInt(self, "Split", "Rows per file:", 1000, 1)
        if ok:
            d = QFileDialog.getExistingDirectory(self, "Output Folder")
            if d:
                try:
                    for i in range((len(df)//rows)+1):
                        df.iloc[i*rows:(i+1)*rows].to_csv(os.path.join(d, f"split_{i+1}.csv"), index=False)
                    QMessageBox.information(self, "Done", f"Split into {(len(df)//rows)+1} files.")
                except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def tool_joiner(self):
        left = self.get_current_df()
        if left is None: return
        fname, _ = QFileDialog.getOpenFileName(self, "Right CSV", "", "CSV (*.csv)")
        if not fname: return
        try:
            right = pd.read_csv(fname, encoding=self.detect_encoding(fname))
            d = JoinDialog(left.columns, right.columns, self)
            if d.exec_():
                l, r, t = d.get_data()
                res = pd.merge(left, right, left_on=l, right_on=r, how=t) if l != r else pd.merge(left, right, on=l, how=t)
                self.create_tab(res, f"Join_{t}")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def tool_remove_duplicates(self):
        df = self.get_current_df()
        if df is None: return
        col, ok = QInputDialog.getItem(self, "Deduplicate", "Column:", df.columns.tolist(), 0, False)
        if ok:
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
        if d.exec_():
            cols, sep, name = d.get_data()
            if not cols: return
            try:
                df[name] = df[cols[0]].astype(str)
                for c in cols[1:]: df[name] = df[name] + sep + df[c].astype(str)
                self.tabs.currentWidget().model().layoutChanged.emit()
                self.update_footer_stats()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def tool_calculate(self):
        df = self.get_current_df()
        if df is None: return
        d = MathDialog(df.columns, self)
        if d.exec_():
            new_col, col_a, op, mode, val_b = d.get_data()
            try:
                s_a = pd.to_numeric(df[col_a], errors='coerce').fillna(0)
                s_b = pd.to_numeric(df[val_b], errors='coerce').fillna(0) if mode == "col" else float(val_b)
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
        try:
            recs = df.to_dict('records')
            matches = []
            for i in range(len(recs)):
                if i % 20 == 0: 
                    self.progress.setValue(int(i/len(recs)*100))
                    QApplication.processEvents()
                for j in range(i+1, len(recs)):
                    s1, s2 = str(recs[i].get(col,'')), str(recs[j].get(col,''))
                    if not s1 or not s2 or s1 == 'nan': continue
                    ratio = SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
                    if ratio >= thresh:
                        row = {'Row 1': i+2, 'Row 2': j+2, 'Score': f"{ratio:.2%}", 'Action': 'REVIEW'}
                        for c in df.columns: row[f"{c}_1"] = recs[i].get(c,''); row[f"{c}_2"] = recs[j].get(c,'')
                        matches.append(row)
            if matches:
                self.create_tab(pd.DataFrame(matches), "Fuzzy_Dupes")
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
            res = []
            m_vals = master[c_m].dropna().astype(str).tolist()
            for i, row in target.iterrows():
                if i % 10 == 0: 
                    self.progress.setValue(int(i/len(target)*100))
                    QApplication.processEvents()
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
    
    splash = QSplashScreen(create_splash_pixmap(), Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()
    time.sleep(1.2)
    
    # CHECK FOR FILE ARGUMENTS (This is the fix for double-clicking a CSV)
    file_to_open = None
    if len(sys.argv) > 1:
        # sys.argv[0] is the script/exe name
        # sys.argv[1] is the file path Windows passes in
        potential_file = sys.argv[1]
        if os.path.exists(potential_file) and potential_file.lower().endswith('.csv'):
            file_to_open = potential_file

    window = CSVForge(file_to_open)
    window.show()
    splash.finish(window)
    sys.exit(app.exec_())