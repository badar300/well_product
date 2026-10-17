from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from well_product.auth import validate_credentials
from well_product.ui.assets import asset_path
from well_product.ui.styles import LOGIN_STYLE


class LoginDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LoginDialog")
        self.setWindowTitle("Sign in — Well Product")
        self.setFixedSize(960, 560)
        self.setStyleSheet(LOGIN_STYLE)

        hero = QFrame()
        hero.setObjectName("LoginHero")
        hero.setMinimumWidth(520)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(12)

        self._hero_image = QLabel()
        self._hero_image.setObjectName("LoginHeroImage")
        self._hero_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for name in ("login_hero.jpg", "login_hero.png"):
            path = asset_path(name)
            if path.is_file():
                pix = QPixmap(str(path))
                if not pix.isNull():
                    self._hero_image.setPixmap(
                        pix.scaled(
                            460,
                            340,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
                    break

        hero_tag = QLabel("Precision costing for modern garment production")
        hero_tag.setObjectName("LoginHeroTag")
        hero_tag.setWordWrap(True)

        hero_layout.addWidget(self._hero_image, stretch=1)
        hero_layout.addWidget(hero_tag)

        form = QFrame()
        form.setObjectName("LoginForm")
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(40, 48, 40, 32)
        form_layout.setSpacing(10)

        brand = QLabel("Well Product")
        brand.setObjectName("LoginBrand")
        sub = QLabel("Garment costing")
        sub.setObjectName("LoginSub")
        form_layout.addWidget(brand)
        form_layout.addWidget(sub)
        form_layout.addSpacing(20)

        user_lbl = QLabel("Username")
        user_lbl.setProperty("class", "login-label")
        self._user = QLineEdit()
        self._user.setPlaceholderText("Username")
        pass_lbl = QLabel("Password")
        pass_lbl.setProperty("class", "login-label")
        self._pass = QLineEdit()
        self._pass.setPlaceholderText("Password")
        self._pass.setEchoMode(QLineEdit.EchoMode.Password)

        self._error = QLabel("")
        self._error.setObjectName("LoginError")
        self._error.hide()

        sign_in = QPushButton("Sign in")
        sign_in.setDefault(True)
        sign_in.setAutoDefault(True)
        sign_in.clicked.connect(self._try_login)
        self._pass.returnPressed.connect(self._try_login)
        self._user.returnPressed.connect(lambda: self._pass.setFocus())

        form_layout.addWidget(user_lbl)
        form_layout.addWidget(self._user)
        form_layout.addWidget(pass_lbl)
        form_layout.addWidget(self._pass)
        form_layout.addWidget(self._error)
        form_layout.addSpacing(8)
        form_layout.addWidget(sign_in)
        form_layout.addStretch()

        body = QHBoxLayout()
        body.setSpacing(0)
        body.setContentsMargins(0, 0, 0, 0)
        body.addWidget(hero, stretch=55)
        body.addWidget(form, stretch=45)

        year = datetime.now().year
        footer = QLabel(
            f"© {year} Well Product. All rights reserved.  ·  "
            "Created by Badar baig · 03234200045"
        )
        footer.setObjectName("LoginFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setWordWrap(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addLayout(body, stretch=1)
        root.addWidget(footer)

        self._pass.setFocus()

    def _try_login(self) -> None:
        if validate_credentials(self._user.text(), self._pass.text()):
            self.accept()
            return
        self._error.setText("Invalid username or password.")
        self._error.show()
        self._pass.clear()
        self._pass.setFocus()
