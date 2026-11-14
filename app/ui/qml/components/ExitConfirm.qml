import QtQuick
import QtQuick.Window
import QtQuick.Controls

Window {
    id: root

    width: 280
    height: 140
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    color: "transparent"
    visible: false

    Rectangle {
        anchors.fill: parent
        color: "#2b2b2b"
        border.color: "#ff5555"
        border.width: 2
        radius: 8

        Column {
            anchors.centerIn: parent
            spacing: 20

            Text {
                text: "Точно хочешь уйти?"
                color: "white"
                font.family: "Minecraft Default"
                font.pixelSize: 16
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Row {
                spacing: 20
                anchors.horizontalCenter: parent.horizontalCenter

                // Кнопка Да
                Rectangle {
                    width: 80; height: 30; radius: 6
                    color: "#ff5555"
                    Text { anchors.centerIn: parent; text: "Да"; color: "white"; font.family: "Minecraft Default"; font.pixelSize: 14 }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: Qt.exit(0)
                    }
                }

                // Кнопка Нет
                Rectangle {
                    width: 80; height: 30; radius: 6
                    color: "#444"
                    Text { anchors.centerIn: parent; text: "Нет"; color: "white"; font.family: "Minecraft Default"; font.pixelSize: 14 }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.visible = false
                    }
                }
            }
        }
    }

    function openAtCenter() {
        root.x = (Screen.desktopAvailableWidth - root.width) / 2
        root.y = (Screen.desktopAvailableHeight - root.height) / 2
        root.visible = true
        root.requestActivate()
    }
}