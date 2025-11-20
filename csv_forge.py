import sys
import csv
import os
from difflib import SequenceMatcher
import intro

import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableView, QFileDialog, QToolBar, QStatusBar, QMessageBox,
    QTabWidget, QDockWidget, QPushButton, QLabel, QComboBox, 
    QDialog, QFormLayout, QSpinBox, QDoubleSpinBox, QProgressBar,
    QHeaderView, QMenu, QInputDialog
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
                return str(val)
        return None

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            try:
                current_dtype = self._df.iloc[:, index.column()].dtype
                if pd.api.types.is_numeric_dtype(current_dtype):
                    if '.' in value:
                        val = float(value)
                    else:
                        val = int(value)
                else:
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

# =============================================================================
# UTILITY DIALOGS
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
        
        # NEW: Connect tab switch to stats update
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

        tools = [
            ("Combiner (Stack Files)", self.tool_combiner),
            ("Splitter (Chunk File)", self.tool_splitter),
            ("Joiner (Merge Columns)", self.tool_joiner),
            ("Fuzzy Dedupe (Current)", self.tool_fuzzy_dedupe),
            ("Fuzzy Match (External)", self.tool_fuzzy_match),
        ]

        for name, func in tools:
            btn = QPushButton(name)
            btn.setStyleSheet("padding: 10px; text-align: left;")
            btn.clicked.connect(func)
            layout.addWidget(btn)

        widget.setLayout(layout)
        dock.setWidget(widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    def create_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # NEW: Permanent indicators
        self.lbl_rows = QLabel("Rows: 0")
        self.lbl_cols = QLabel("Cols: 0")
        self.lbl_mem = QLabel("Mem: 0 KB")
        
        # Styling for indicators
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
        """Update the row/col/memory counts based on active tab"""
        df = self.get_current_df()
        if df is not None:
            rows = df.shape[0]
            cols = df.shape[1]
            # Calculate memory usage in MB
            mem_bytes = df.memory_usage(deep=True).sum()
            mem_mb = mem_bytes / (1024 * 1024)
            
            self.lbl_rows.setText(f"Rows: {rows:,}")
            self.lbl_cols.setText(f"Cols: {cols}")
            self.lbl_mem.setText(f"Mem: {mem_mb:.2f} MB")
        else:
            self.lbl_rows.setText("Rows: 0")
            self.lbl_cols.setText("Cols: 0")
            self.lbl_mem.setText("Mem: 0 KB")

    # --- File Operations ---
    def detect_encoding(self, filepath):
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    f.readline()
                return enc
            except:
                continue
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
            
            if max_commas > 0:
                return best_row
            return None
        except:
            return None

    def load_csv(self):
        fnames, _ = QFileDialog.getOpenFileNames(self, "Open CSV", "", "CSV Files (*.csv)")
        if not fnames:
            return
        
        for fname in fnames:
            try:
                enc = self.detect_encoding(fname)
                
                try:
                    df = pd.read_csv(fname, encoding=enc)
                except pd.errors.ParserError:
                    print(f"Parser error detected in {fname}. Attempting auto-detect...")
                    skip_rows = self.find_valid_header_row(fname, enc)
                    
                    if skip_rows is not None and skip_rows > 0:
                        df = pd.read_csv(fname, encoding=enc, skiprows=skip_rows)
                        self.status_bar.showMessage(f"Auto-detected header at row {skip_rows + 1}")
                    else:
                        rows, ok = QInputDialog.getInt(self, "Import Error", 
                            "Structure mismatch detected.\nHow many header rows should be skipped?", 
                            0, 0, 100)
                        if ok:
                            df = pd.read_csv(fname, encoding=enc, skiprows=rows)
                        else:
                            raise
                
                df.columns = df.columns.str.strip()
                self.create_tab(df, os.path.basename(fname))
                
                if "Auto-detected" not in self.status_bar.currentMessage():
                    self.status_bar.showMessage(f"Loaded {fname} ({enc})")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open {fname}\n{str(e)}")

    def create_tab(self, df, title):
        view = QTableView()
        model = DataFrameModel(df)
        view.setModel(model)
        view.setSortingEnabled(True)
        view.horizontalHeader().setStretchLastSection(True)
        
        idx = self.tabs.addTab(view, title)
        self.tabs.setCurrentIndex(idx)
        # Update stats immediately
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
        if df is None:
            return
        
        fname, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if fname:
            try:
                df.to_csv(fname, index=False)
                self.status_bar.showMessage(f"Saved to {fname}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file:\n{str(e)}")

    # --- TOOLS IMPLEMENTATION ---
    def tool_combiner(self):
        fnames, _ = QFileDialog.getOpenFileNames(self, "Select CSVs to Append", "", "CSV Files (*.csv)")
        if not fnames: return

        dfs = []
        current_df = self.get_current_df()
        if current_df is not None:
            reply = QMessageBox.question(self, "Append?", "Append selected files to the currently open table?", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                dfs.append(current_df)

        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        try:
            count = len(fnames)
            for i, f in enumerate(fnames):
                enc = self.detect_encoding(f)
                d = pd.read_csv(f, encoding=enc)
                d['source_file'] = os.path.basename(f)
                dfs.append(d)
                self.progress.setValue(int((i+1)/count * 100))
            
            combined = pd.concat(dfs, ignore_index=True)
            self.create_tab(combined, "Combined_Result")
            self.status_bar.showMessage(f"Combined {len(dfs)} sources. Total rows: {len(combined)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.progress.setVisible(False)

    def tool_splitter(self):
        df = self.get_current_df()
        if df is None:
            QMessageBox.warning(self, "Warning", "No CSV open to split.")
            return

        rows, ok = QInputDialog.getInt(self, "Split CSV", "Rows per file:", 1000, 1, 1000000)
        
        if ok:
            dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
            if dir_path:
                self.progress.setVisible(True)
                total_rows = len(df)
                chunks = (total_rows // rows) + 1
                
                try:
                    for i in range(chunks):
                        start = i * rows
                        end = start + rows
                        chunk = df.iloc[start:end]
                        if not chunk.empty:
                            chunk.to_csv(os.path.join(dir_path, f"split_{i+1}.csv"), index=False)
                        self.progress.setValue(int((i+1)/chunks * 100))
                    
                    QMessageBox.information(self, "Success", f"Split into {chunks} files in {dir_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
                finally:
                    self.progress.setVisible(False)

    def tool_joiner(self):
        left_df = self.get_current_df()
        if left_df is None:
            QMessageBox.warning(self, "Warning", "Open the Main (Left) CSV first.")
            return

        fname, _ = QFileDialog.getOpenFileName(self, "Select Second (Right) CSV", "", "CSV Files (*.csv)")
        if not fname: return

        try:
            enc = self.detect_encoding(fname)
            right_df = pd.read_csv(fname, encoding=enc)
            right_df.columns = right_df.columns.str.strip()

            dialog = JoinDialog(left_df.columns, right_df.columns, self)
            if dialog.exec():
                l_col, r_col, j_type = dialog.get_data()
                if l_col == r_col:
                    result = pd.merge(left_df, right_df, on=l_col, how=j_type)
                else:
                    result = pd.merge(left_df, right_df, left_on=l_col, right_on=r_col, how=j_type)
                self.create_tab(result, f"Join_{j_type}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def tool_fuzzy_dedupe(self):
        df = self.get_current_df()
        if df is None:
            QMessageBox.warning(self, "Warning", "No data to scan.")
            return

        col, ok_col = QInputDialog.getItem(self, "Column Selection", "Select Column to check for duplicates:", df.columns.tolist(), 0, False)
        if not ok_col: return
        
        thresh, ok_thresh = QInputDialog.getDouble(self, "Similarity Threshold", "Threshold (0.0 - 1.0):", 0.8, 0.0, 1.0, 2)
        if not ok_thresh: return

        self.status_bar.showMessage("Running detailed fuzzy analysis...")
        self.progress.setVisible(True)
        QApplication.processEvents()
        
        try:
            records = df.to_dict('records')
            columns = df.columns.tolist()
            matches = []
            total_records = len(records)
            
            for i in range(total_records):
                if i % 20 == 0: 
                    self.progress.setValue(int(i/total_records*100))
                    QApplication.processEvents()
                    
                for j in range(i + 1, total_records):
                    s1 = str(records[i].get(col, ''))
                    s2 = str(records[j].get(col, ''))
                    
                    if not s1 or not s2 or s1 == 'nan' or s2 == 'nan': continue

                    ratio = SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
                    
                    if ratio >= thresh:
                        match_row = {
                            'Row_Index_1': i + 2,
                            'Row_Index_2': j + 2,
                            'Similarity_Score': f"{ratio:.2%}",
                        }
                        for field in columns: match_row[f"{field}_1"] = records[i].get(field, '')
                        for field in columns: match_row[f"{field}_2"] = records[j].get(field, '')
                        match_row['Action'] = 'REVIEW'
                        matches.append(match_row)
            
            if matches:
                cols_ordered = ['Row_Index_1', 'Row_Index_2', 'Similarity_Score']
                cols_ordered += [f"{c}_1" for c in columns]
                cols_ordered += [f"{c}_2" for c in columns]
                cols_ordered.append('Action')
                
                result_df = pd.DataFrame(matches)
                result_df = result_df[cols_ordered]
                self.create_tab(result_df, "Fuzzy_Duplicates_Detailed")
                QMessageBox.information(self, "Complete", f"Found {len(matches)} potential duplicates.")
            else:
                QMessageBox.information(self, "Result", "No fuzzy duplicates found above threshold.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.progress.setValue(0)
            self.progress.setVisible(False)
            self.status_bar.clearMessage()

    def tool_fuzzy_match(self):
        df_target = self.get_current_df()
        if df_target is None:
            QMessageBox.warning(self, "Warning", "Open the Target CSV first.")
            return

        fname, _ = QFileDialog.getOpenFileName(self, "Select Master List CSV", "", "CSV Files (*.csv)")
        if not fname: return
        
        try:
            enc = self.detect_encoding(fname)
            df_master = pd.read_csv(fname, encoding=enc)

            col_target, ok1 = QInputDialog.getItem(self, "Match Configuration", "Select Column in CURRENT tab:", df_target.columns.tolist(), 0, False)
            if not ok1: return
            col_master, ok2 = QInputDialog.getItem(self, "Match Configuration", "Select Column in MASTER file:", df_master.columns.tolist(), 0, False)
            if not ok2: return

            thresh, ok3 = QInputDialog.getDouble(self, "Similarity", "Threshold:", 0.8, 0.1, 1.0, 2)
            if not ok3: return

            self.status_bar.showMessage("Matching...")
            self.progress.setVisible(True)
            QApplication.processEvents()
            
            results = []
            master_lookup = df_master[col_master].dropna().astype(str).tolist()
            total = len(df_target)
            
            for idx, row in df_target.iterrows():
                if idx % 10 == 0: self.progress.setValue(int(idx/total * 100))
                
                target_val = str(row[col_target])
                best_ratio = 0
                best_match = None
                
                for m_val in master_lookup:
                    ratio = SequenceMatcher(None, target_val.lower(), m_val.lower()).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_match = m_val
                
                match_status = "Exact" if best_ratio == 1.0 else ("Fuzzy" if best_ratio >= thresh else "No Match")
                
                row_data = row.to_dict()
                row_data['Match_Status'] = match_status
                row_data['Best_Match_Found'] = best_match if best_ratio >= thresh else None
                row_data['Similarity_Score'] = round(best_ratio, 3)
                results.append(row_data)

            result_df = pd.DataFrame(results)
            self.create_tab(result_df, "Matched_Results")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.progress.setValue(0)
            self.progress.setVisible(False)
            self.status_bar.clearMessage()

if __name__ == "__main__":
    intro
    app = QApplication(sys.argv)
    window = CSVForge()
    window.show()
    sys.exit(app.exec())