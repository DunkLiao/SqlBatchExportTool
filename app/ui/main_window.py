from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging
import traceback

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.config_model import AppConfig, DbConfig
from app.services.db_service import OracleDbService
from app.services.excel_service import ExcelExportService
from app.services.log_service import configure_logging
from app.services.parameter_service import SqlParameterError, parse_sql_parameters
from app.services.sql_service import SqlService
from app.utils.file_utils import ensure_xlsx_suffix, project_root, resolve_app_path


CONFIG_PATH = project_root() / "config" / "config.json"
LOG_DIR = project_root() / "logs"


@dataclass(frozen=True, slots=True)
class ExportRequest:
    db: DbConfig
    sql_folder: Path
    output_excel: Path
    sql_parameters: dict[str, str]
    sql_parameters_text: str


class BatchExportWorker(QThread):
    log_message = Signal(str)
    failed = Signal(str)
    finished_successfully = Signal(str)

    def __init__(self, request: ExportRequest, logger: logging.Logger) -> None:
        super().__init__()
        self._request = request
        self._logger = logger

    def run(self) -> None:
        db_service = OracleDbService(self._request.db)
        sql_service = SqlService()

        try:
            sql_files = sql_service.list_sql_files(self._request.sql_folder)
            if not sql_files:
                self._emit_info("No .sql files found. A summary workbook will be created.")

            self._emit_info("Connecting to Oracle database...")
            db_service.connect()
            self._emit_info("Connected.")

            with ExcelExportService(self._request.output_excel) as excel_service:
                for sql_file in sql_files:
                    try:
                        sql = sql_service.read_sql(sql_file)
                        result = db_service.execute_query(sql, self._request.sql_parameters)
                        sheet_name = excel_service.write_dataframe(sql_file.stem, result.dataframe)
                        self._emit_info(
                            f"{sql_file.name} Success Rows={result.row_count} "
                            f"Time={result.elapsed_seconds:.2f}s Sheet={sheet_name}"
                        )
                    except Exception as exc:
                        self._emit_error(f"{sql_file.name} Failed {exc}")
                        continue

            self.finished_successfully.emit(f"Export completed: {self._request.output_excel}")
        except Exception as exc:
            self._logger.error("Batch export failed: %s\n%s", exc, traceback.format_exc())
            self.failed.emit(str(exc))
        finally:
            db_service.close()

    def _emit_info(self, message: str) -> None:
        self._logger.info(message)
        self.log_message.emit(message)

    def _emit_error(self, message: str) -> None:
        self._logger.error(message)
        self.log_message.emit(message)


class TestConnectionWorker(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, db_config: DbConfig, logger: logging.Logger) -> None:
        super().__init__()
        self._db_config = db_config
        self._logger = logger

    def run(self) -> None:
        db_service = OracleDbService(self._db_config)
        try:
            db_service.connect()
            self._logger.info("Oracle test connection succeeded.")
            self.succeeded.emit("Oracle connection succeeded.")
        except Exception as exc:
            self._logger.error("Oracle test connection failed: %s", exc)
            self.failed.emit(str(exc))
        finally:
            db_service.close()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._logger = configure_logging(LOG_DIR)
        self._config = AppConfig.load(CONFIG_PATH)
        self._worker: BatchExportWorker | None = None
        self._test_worker: TestConnectionWorker | None = None

        self.setWindowTitle("Oracle SQL Batch Export Tool")
        self.resize(860, 640)

        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.service_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self._password_visible = False
        self._password_visibility_action = self.password_input.addAction(
            self._create_password_visibility_icon(visible=False),
            QLineEdit.TrailingPosition,
        )
        self._password_visibility_action.setToolTip("Show password")
        self._password_visibility_action.triggered.connect(self._toggle_password_visibility)
        self.sql_folder_input = QLineEdit()
        self.output_excel_input = QLineEdit()
        self.sql_parameters_input = QTextEdit()
        self.sql_parameters_input.setPlaceholderText("DATA_DATE=20260527\nBRANCH_ID=001")
        self.sql_parameters_input.setFixedHeight(92)
        self.test_connect_button = QPushButton("Test Connect")
        self.execute_button = QPushButton("Execute")
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        self._build_ui()
        self._apply_dark_style()
        self._load_config_to_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        title = QLabel("Oracle SQL Batch Export Tool")
        title.setObjectName("TitleLabel")
        root_layout.addWidget(title)

        connection_group = QGroupBox("Oracle Connection")
        connection_form = QFormLayout(connection_group)
        connection_form.addRow("Host", self.host_input)
        connection_form.addRow("Port", self.port_input)
        connection_form.addRow("Service Name", self.service_input)
        connection_form.addRow("Username", self.username_input)
        connection_form.addRow("Password", self.password_input)
        root_layout.addWidget(connection_group)

        file_group = QGroupBox("Files")
        file_layout = QGridLayout(file_group)
        sql_browse_button = QPushButton("Browse")
        output_browse_button = QPushButton("Browse")
        sql_browse_button.clicked.connect(self._browse_sql_folder)
        output_browse_button.clicked.connect(self._browse_output_excel)
        file_layout.addWidget(QLabel("SQL Folder"), 0, 0)
        file_layout.addWidget(self.sql_folder_input, 0, 1)
        file_layout.addWidget(sql_browse_button, 0, 2)
        file_layout.addWidget(QLabel("Output XLSX"), 1, 0)
        file_layout.addWidget(self.output_excel_input, 1, 1)
        file_layout.addWidget(output_browse_button, 1, 2)
        file_layout.setColumnStretch(1, 1)
        root_layout.addWidget(file_group)

        parameters_group = QGroupBox("SQL Parameters")
        parameters_layout = QVBoxLayout(parameters_group)
        parameters_layout.addWidget(self.sql_parameters_input)
        root_layout.addWidget(parameters_group)

        actions_layout = QHBoxLayout()
        actions_layout.addStretch(1)
        self.test_connect_button.clicked.connect(self._test_connection)
        actions_layout.addWidget(self.test_connect_button)
        self.execute_button.clicked.connect(self._execute)
        actions_layout.addWidget(self.execute_button)
        root_layout.addLayout(actions_layout)

        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_area)
        root_layout.addWidget(log_group, 1)

        self.setCentralWidget(central)

    def _toggle_password_visibility(self) -> None:
        self._password_visible = not self._password_visible
        if self._password_visible:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self._password_visibility_action.setToolTip("Hide password")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self._password_visibility_action.setToolTip("Show password")
        self._password_visibility_action.setIcon(
            self._create_password_visibility_icon(visible=self._password_visible)
        )

    def _create_password_visibility_icon(self, visible: bool) -> QIcon:
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#e7eaf0"))
        pen.setWidth(2)
        painter.setPen(pen)

        eye_path = QPainterPath()
        eye_path.moveTo(3, 12)
        eye_path.cubicTo(7, 5, 17, 5, 21, 12)
        eye_path.cubicTo(17, 19, 7, 19, 3, 12)
        painter.drawPath(eye_path)
        painter.drawEllipse(10, 10, 4, 4)

        if visible:
            painter.drawLine(5, 19, 19, 5)

        painter.end()
        return QIcon(pixmap)

    def _apply_dark_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1f2329;
                color: #e7eaf0;
                font-size: 14px;
            }
            QLabel#TitleLabel {
                font-size: 22px;
                font-weight: 700;
                padding: 4px 0 8px 0;
            }
            QGroupBox {
                border: 1px solid #3a404a;
                border-radius: 6px;
                margin-top: 12px;
                padding: 16px 10px 10px 10px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QLineEdit, QTextEdit {
                background-color: #15181d;
                border: 1px solid #444b57;
                border-radius: 4px;
                padding: 7px;
                selection-background-color: #2f6fed;
            }
            QPushButton {
                background-color: #2f6fed;
                border: none;
                border-radius: 4px;
                color: white;
                min-width: 92px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #3d7cff;
            }
            QPushButton:disabled {
                background-color: #4a5260;
                color: #aab1bd;
            }
            """
        )

    def _load_config_to_ui(self) -> None:
        self.host_input.setText(self._config.db.host)
        self.port_input.setText(str(self._config.db.port))
        self.service_input.setText(self._config.db.service_name)
        self.username_input.setText(self._config.db.username)
        self.password_input.setText(self._config.db.password)
        self.sql_folder_input.setText(self._config.last_sql_folder)
        self.output_excel_input.setText(self._config.last_output_excel)
        self.sql_parameters_input.setPlainText(self._config.last_sql_parameters)

    def _browse_sql_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select SQL Folder", self.sql_folder_input.text())
        if folder:
            self.sql_folder_input.setText(folder)

    def _browse_output_excel(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Output Excel",
            self.output_excel_input.text() or str(project_root() / "output" / "export.xlsx"),
            "Excel Workbook (*.xlsx)",
        )
        if path:
            self.output_excel_input.setText(str(ensure_xlsx_suffix(Path(path))))

    def _execute(self) -> None:
        request = self._build_request()
        if request is None:
            return

        self._save_config(request)
        self._set_actions_enabled(False)
        self.log_area.clear()
        self._append_log("Starting batch export...")

        self._worker = BatchExportWorker(request, self._logger)
        self._worker.log_message.connect(self._append_log)
        self._worker.failed.connect(self._handle_failure)
        self._worker.finished_successfully.connect(self._handle_success)
        self._worker.finished.connect(self._handle_finished)
        self._worker.start()

    def _test_connection(self) -> None:
        db_config = self._build_db_config(show_errors=True)
        if db_config is None:
            return

        self._save_current_form()
        self._set_actions_enabled(False)
        self._append_log("Testing Oracle connection...")

        self._test_worker = TestConnectionWorker(db_config, self._logger)
        self._test_worker.succeeded.connect(self._handle_test_success)
        self._test_worker.failed.connect(self._handle_test_failure)
        self._test_worker.finished.connect(self._handle_test_finished)
        self._test_worker.start()

    def _build_db_config(self, show_errors: bool) -> DbConfig | None:
        host = self.host_input.text().strip()
        service_name = self.service_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        try:
            port = int(self.port_input.text().strip())
        except ValueError:
            if show_errors:
                self._show_error("Port must be a number.")
            return None

        if not host or not service_name or not username:
            if show_errors:
                self._show_error("Host, Service Name, and Username are required.")
            return None

        return DbConfig(
            host=host,
            port=port,
            service_name=service_name,
            username=username,
            password=password,
        )

    def _build_request(self) -> ExportRequest | None:
        db_config = self._build_db_config(show_errors=True)
        if db_config is None:
            return None

        sql_folder_text = self.sql_folder_input.text().strip()
        output_excel_text = self.output_excel_input.text().strip()
        sql_parameters_text = self.sql_parameters_input.toPlainText()
        sql_folder = resolve_app_path(sql_folder_text)

        if not sql_folder_text or not sql_folder.exists() or not sql_folder.is_dir():
            self._show_error("SQL Folder does not exist.")
            return None
        if not output_excel_text:
            self._show_error("Output XLSX is required.")
            return None
        output_excel = ensure_xlsx_suffix(resolve_app_path(output_excel_text))
        try:
            sql_parameters = parse_sql_parameters(sql_parameters_text)
        except SqlParameterError as exc:
            self._show_error(f"Invalid SQL Parameters:\n{exc}")
            return None

        return ExportRequest(
            db=db_config,
            sql_folder=sql_folder,
            output_excel=output_excel,
            sql_parameters=sql_parameters,
            sql_parameters_text=sql_parameters_text,
        )

    def _save_config(self, request: ExportRequest) -> None:
        self._config = AppConfig(
            db=request.db,
            last_sql_folder=str(request.sql_folder),
            last_output_excel=str(request.output_excel),
            last_sql_parameters=request.sql_parameters_text,
        )
        self._config.save(CONFIG_PATH)

    def _save_current_form(self) -> None:
        db_config = self._build_db_config(show_errors=False)
        if db_config is None:
            return

        sql_folder_text = self.sql_folder_input.text().strip()
        output_excel_text = self.output_excel_input.text().strip()
        sql_parameters_text = self.sql_parameters_input.toPlainText()
        self._config = AppConfig(
            db=db_config,
            last_sql_folder=sql_folder_text,
            last_output_excel=output_excel_text,
            last_sql_parameters=sql_parameters_text,
        )
        self._config.save(CONFIG_PATH)

    def _append_log(self, message: str) -> None:
        self.log_area.append(message)

    def _handle_test_success(self, message: str) -> None:
        self._append_log(message)
        QMessageBox.information(self, "Test Connect", message)

    def _handle_test_failure(self, message: str) -> None:
        self._append_log(f"Test connection failed: {message}")
        self._show_error(f"Oracle connection failed:\n{message}")

    def _handle_test_finished(self) -> None:
        self._set_actions_enabled(True)
        self._test_worker = None

    def _handle_success(self, message: str) -> None:
        self._append_log(message)
        QMessageBox.information(self, "Export Completed", message)

    def _handle_failure(self, message: str) -> None:
        self._append_log(f"Failed: {message}")
        self._show_error(message)

    def _handle_finished(self) -> None:
        self._set_actions_enabled(True)
        self._worker = None

    def _set_actions_enabled(self, enabled: bool) -> None:
        self.test_connect_button.setEnabled(enabled)
        self.execute_button.setEnabled(enabled)

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event: object) -> None:
        self._save_current_form()
        super().closeEvent(event)
