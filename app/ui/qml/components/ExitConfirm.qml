import QtQuick
import QtQuick.Window
import QtQuick.Controls

Window {
    id: root
    width: 320
    height: 160
    flags: Qt.Window | Qt.FramelessWindowHint
         | Qt.WindowStaysOnTopHint | Qt.Tool
    color: "transparent"
    visible: false

    Rectangle {
        anchors.fill: parent
        color: "#f4e4c1"
        border.color: "#ffb89e"
        border.width: 3

        Column {
            anchors.centerIn: parent
            spacing: 25

            Text {
                text: "👋 Точно хочешь уйти?"
                color: "#2d1b0e"
                font.family: "Minecraft Default"
                font.pixelSize: 18
                font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Row {
                spacing: 20
                anchors.horizontalCenter: parent.horizontalCenter

                Rectangle {
                    width: 90; height: 36
                    color: "#ffb89e"
                    border.color: "#2d1b0e"
                    border.width: 2
                    Text {
                        anchors.centerIn: parent
                        text: "Да"
                        color: "#2d1b0e"
                        font.family: "Minecraft Default"
                        font.pixelSize: 15
                        font.bold: true
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: Qt.exit(0)
                    }
                }

                Rectangle {
                    width: 90; height: 36
                    color: "#e6d5b8"
                    border.color: "#2d1b0e"
                    border.width: 2
                    Text {
                        anchors.centerIn: parent
                        text: "Нет"
                        color: "#2d1b0e"
                        font.family: "Minecraft Default"
                        font.pixelSize: 15
                        font.bold: true
                    }
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