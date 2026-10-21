import QtQuick
import QtQuick.Controls

Window {
    id: root
    width: 380
    height: 300
    title: "Настройки"
    flags: Qt.Window | Qt.WindowStaysOnTopHint

    Column {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        Row {
            spacing: 12
            Text { text: "Всегда поверх окон:"; width: 180 }
            Switch {
                checked: true
                onToggled: console.log("always-on-top:", checked)
            }
        }

        Row {
            spacing: 12
            Text { text: "Режим редактора:"; width: 180 }
            Switch {
                onToggled: world.editorMode = checked
            }
        }

        Row {
            spacing: 12
            Text { text: "Звук:"; width: 180 }
            Slider {
                width: 120
                from: 0; to: 1; value: 0.7
                onValueChanged: console.log("volume:", value)
            }
        }
    }
}