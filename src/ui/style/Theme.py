def apply_stylesheet(app):
    import os
    from data.Globals import Globals
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import QFile, QIODevice, QTextStream


    # Load the stylesheet
    stylesheet = QFile(os.path.join(Globals.RESOURCE_DIR,"ui", "style", "stylesheet.qss"))
    print 
    stylesheet.open(QIODevice.ReadOnly | QFile.Text)
    stream = QTextStream(stylesheet)
    app.setStyleSheet(stream.readAll())
