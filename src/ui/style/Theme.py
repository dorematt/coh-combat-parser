def apply_stylesheet(app):
    import os
    from data.Globals import Globals
    from PyQt5.QtGui import QIcon, QFont
    from PyQt5.QtCore import QFile, QIODevice, QTextStream

    # Load the stylesheet
    stylesheet_path = os.path.join(Globals.ROOT_DIR, "ui", "style", "Combinear.qss")
    stylesheet = QFile(stylesheet_path)
    stylesheet.open(QIODevice.ReadOnly | QFile.Text)
    stream = QTextStream(stylesheet)
    app.setStyleSheet(stream.readAll())

    # Print font information for debugging
    print("Current Font:", app.font().family(), app.font().pointSize())
    
    # Set the font globally for the application

    # Print font information after setting it for debugging
    print("Updated Font:", app.font().family(), app.font().pointSize())

    # Set the application icon
    app.setWindowIcon(QIcon(os.path.join(Globals.ROOT_DIR, "ui", "icon", "icon_256.png")))

def apply_header_style_fix(component):
    '''This is a workaround for a bug in Qt5 that causes the header to not be styled correctly.'''
    component.header().setStyleSheet(
        "::section {"
            "background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #616161, stop: 0.5 #505050, stop: 0.6 #434343, stop:1 #656565);"
            "color: white;"
            "padding-left: 4px;"
            "border: 1px solid #6c6c6c;"
        "}"
    )