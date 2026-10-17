APP_STYLE = """
/* —— Base —— */
QMainWindow, QDialog, QWidget {
    background-color: #eef1f6;
    color: #0f172a;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 13px;
}

/* —— Sidebar navigation —— */
#NavSidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #0f172a, stop:1 #1e293b);
    border: none;
    padding: 0;
    outline: 0;
}
#NavSidebar::item {
    color: #94a3b8;
    padding: 14px 20px;
    margin: 4px 10px;
    border-radius: 8px;
    border-left: 3px solid transparent;
}
#NavSidebar::item:hover {
    background-color: rgba(255, 255, 255, 0.06);
    color: #e2e8f0;
}
#NavSidebar::item:selected {
    background-color: rgba(37, 99, 235, 0.25);
    color: #ffffff;
    border-left: 3px solid #60a5fa;
    font-weight: 600;
}
QLabel.nav-brand {
    color: #f8fafc;
    font-size: 17px;
    font-weight: 700;
    padding: 20px 20px 4px 20px;
}
QLabel.nav-tagline {
    color: #64748b;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0 20px 16px 20px;
}
QPushButton#NavLogout {
    background-color: transparent;
    color: #cbd5e1;
    border: 1px solid #475569;
    border-radius: 8px;
    margin: 12px 14px 16px 14px;
    padding: 10px 14px;
    font-weight: 600;
    min-width: 0;
}
QPushButton#NavLogout:hover {
    background-color: rgba(255, 255, 255, 0.08);
    color: #f8fafc;
    border-color: #64748b;
}
QPushButton#NavLogout:pressed {
    background-color: rgba(255, 255, 255, 0.04);
}

/* —— Page chrome —— */
#ContentStack > QWidget {
    background-color: #eef1f6;
}
#GlobalSearchWrap {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
}
#GlobalSearchBar {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 14px;
}
#GlobalSearchBar:focus {
    border: 1px solid #2563eb;
    background-color: #ffffff;
}
QLabel.title {
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
}
QLabel.subtitle {
    color: #64748b;
    font-size: 13px;
    max-width: 520px;
}
QWidget.toolbar {
    padding: 4px 0 12px 0;
}

/* —— Buttons —— */
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    padding: 9px 16px;
    border-radius: 8px;
    min-width: 76px;
    font-weight: 600;
}
QPushButton:hover { background-color: #1d4ed8; }
QPushButton:pressed { background-color: #1e40af; }
QPushButton:disabled {
    background-color: #cbd5e1;
    color: #94a3b8;
}
QPushButton[class="secondary"] {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
}
QPushButton[class="secondary"]:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
}
QPushButton[class="ghost"] {
    background-color: transparent;
    color: #475569;
    border: 1px dashed #cbd5e1;
    min-width: 48px;
    padding: 8px 12px;
}
QPushButton[class="ghost"]:hover {
    background-color: #f1f5f9;
    border-color: #64748b;
    color: #0f172a;
}
QPushButton[class="danger"] {
    background-color: #dc2626;
}
QPushButton[class="danger"]:hover { background-color: #b91c1c; }

/* —— Inputs —— */
QLineEdit, QPlainTextEdit, QComboBox, QDoubleSpinBox {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #bfdbfe;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #2563eb;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}

/* —— Tables —— */
QTableWidget[class="data-table"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    gridline-color: transparent;
    alternate-background-color: #f8fafc;
    selection-background-color: #dbeafe;
    selection-color: #0f172a;
    outline: 0;
}
QTableWidget[class="data-table"]::item {
    padding: 8px 12px;
    border-bottom: 1px solid #f1f5f9;
}
QHeaderView::section {
    background: #f1f5f9;
    color: #475569;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid #e2e8f0;
    font-weight: 600;
    font-size: 12px;
    text-transform: none;
}
QTableWidget[class="data-table"] QHeaderView::section:first {
    border-top-left-radius: 12px;
}
QTableWidget {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    gridline-color: #f1f5f9;
    selection-background-color: #dbeafe;
}

/* —— Cards & groups —— */
QGroupBox {
    font-weight: 600;
    font-size: 13px;
    color: #334155;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    margin-top: 14px;
    padding: 16px 14px 14px 14px;
    background: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #0f172a;
}
QFrame[class="info-box"] {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 10px;
    padding: 12px 14px;
}
QLabel.hint {
    color: #64748b;
    font-size: 12px;
    line-height: 1.4;
}

/* —— Tabs & toolbox —— */
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    border-radius: 0 10px 10px 10px;
    background: #ffffff;
    top: -1px;
    padding: 4px;
}
QTabBar::tab {
    padding: 11px 20px;
    margin-right: 3px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    background: #e2e8f0;
    color: #475569;
    font-weight: 500;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #0f172a;
    font-weight: 700;
    border: 1px solid #e2e8f0;
    border-bottom: none;
}
/* BOM sections (Materials tab) */
QGroupBox[class="bom-section"] {
    margin-top: 8px;
    font-size: 14px;
}
QGroupBox[class="bom-section"]::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 4px 10px;
    color: #1e3a8a;
    background: #e0e7ff;
    border-radius: 6px;
}
#MaterialBomScroll {
    background: transparent;
}

/* —— Product image upload —— */
#ProductImagePanel QFrame[class="upload-slot"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
}
QFrame[class="upload-preview"] {
    background: #f8fafc;
    border: 2px dashed #cbd5e1;
    border-radius: 12px;
}
QFrame[class="upload-preview"][hasImage="true"] {
    background: #0f172a;
    border: 2px solid #334155;
}
QFrame[class="upload-preview"]:hover {
    border-color: #60a5fa;
    background: #f0f9ff;
}
QFrame[class="upload-preview"][hasImage="true"]:hover {
    background: #1e293b;
    border-color: #93c5fd;
}
QLabel[class="upload-plus"] {
    font-size: 36px;
    font-weight: 300;
    color: #94a3b8;
}
QLabel[class="upload-hint"] {
    font-size: 12px;
    color: #64748b;
}
QLabel[class="upload-filename"] {
    font-size: 12px;
    color: #475569;
    padding: 0 4px;
}
QLabel[class="upload-image"] {
    background: transparent;
}
QLabel[class="slot-title"] {
    font-weight: 700;
    font-size: 14px;
    color: #0f172a;
}
QLabel[class="slot-subtitle"] {
    font-size: 12px;
    color: #64748b;
    margin-bottom: 4px;
}
#OverviewScroll {
    background: transparent;
}
QGroupBox[class="overview-section"] {
    margin-top: 4px;
}
QFrame[class="extras-panel"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    margin-top: 4px;
}
#ProductImagePanel QLabel.hint {
    color: #475569;
    font-size: 12px;
}
QFrame[class="extra-tile"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}
QFrame[class="extra-tile"]:hover {
    border-color: #93c5fd;
}
QLabel[class="extra-thumb"] {
    background: #f1f5f9;
    border-radius: 8px;
}
QLabel[class="extra-name"] {
    font-size: 11px;
    color: #475569;
}
QFrame[class="add-extra-tile"] {
    background: #f8fafc;
    border: 2px dashed #cbd5e1;
    border-radius: 12px;
}
QFrame[class="add-extra-tile"]:hover {
    border-color: #2563eb;
    background: #eff6ff;
}
QLabel[class="image-preview"] {
    background: transparent;
    border: none;
    color: #64748b;
    font-size: 12px;
}

/* —— Cost summary —— */
#PhotoPreviewPane QLabel[class="image-preview"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    min-height: 420px;
}

QLabel[class="field-label"] {
    color: #475569;
    font-weight: 500;
    font-size: 12px;
    padding-right: 4px;
}
#PricingScroll {
    background: transparent;
}

/* Live cost summary styles live in widgets/cost_summary.py (COST_SUMMARY_STYLE) */

/* —— Dialog buttons —— */
QDialogButtonBox QPushButton {
    min-width: 88px;
}
"""

LOGIN_STYLE = """
/* Self-contained login screen (do not combine with APP_STYLE — avoids QWidget bg bleed). */
#LoginDialog {
    background-color: #0f172a;
    color: #0f172a;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 13px;
}
#LoginDialog QWidget {
    background-color: transparent;
}
#LoginHero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1e293b, stop:1 #0f172a);
    border: none;
}
#LoginHeroImage {
    background: transparent;
    border-radius: 12px;
}
#LoginHeroTag {
    background: transparent;
    color: #ffffff;
    font-size: 15px;
    font-weight: 600;
    line-height: 1.45;
    padding: 8px 4px 0 4px;
}
#LoginForm {
    background-color: #ffffff;
}
#LoginForm QWidget {
    background-color: transparent;
}
#LoginBrand {
    background: transparent;
    font-size: 28px;
    font-weight: 800;
    color: #020617;
}
#LoginSub {
    background: transparent;
    font-size: 13px;
    color: #334155;
    margin-bottom: 8px;
}
#LoginDialog QLabel[class="login-label"] {
    background: transparent;
    color: #1e293b;
    font-size: 12px;
    font-weight: 600;
    padding-top: 4px;
}
#LoginError {
    background: transparent;
    color: #b91c1c;
    font-size: 12px;
    font-weight: 600;
}
#LoginFooter {
    background-color: #0f172a;
    color: #cbd5e1;
    font-size: 11px;
    padding: 12px 16px;
    border-top: 1px solid #475569;
}
#LoginForm QLineEdit {
    background-color: #ffffff;
    color: #020617;
    border: 2px solid #64748b;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 14px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}
#LoginForm QLineEdit:focus {
    border: 2px solid #1d4ed8;
}
#LoginForm QPushButton {
    background-color: #1d4ed8;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    min-height: 44px;
    font-size: 14px;
    font-weight: 700;
    padding: 10px 16px;
}
#LoginForm QPushButton:hover {
    background-color: #1e40af;
}
#LoginForm QPushButton:pressed {
    background-color: #1e3a8a;
}
"""
