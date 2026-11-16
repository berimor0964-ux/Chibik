import QtQuick
import QtQuick.Window
import QtQuick.Controls

Window {
    id: root
    flags: Qt.Window | Qt.FramelessWindowHint
         | Qt.WindowStaysOnTopHint | Qt.Tool
         | Qt.NoDropShadowWindowHint
    color: "transparent"
    visible: false

    property string titleText: "Уведомление"
    property string bodyText: ""
    width: 320
    height: 100
    opacity: 0

    Behavior on opacity { NumberAnimation { duration: 300 } }

    Rectangle {
        anchors.fill: parent
        color: "#f4e4c1"
        border.color: "#ffb89e"
        border.width: 3

        Rectangle {
            id: iconBox
            anchors.left: parent.left
            anchors.leftMargin: 15
            anchors.verticalCenter: parent.verticalCenter
            width: 45; height: 45
            color: "#ffb89e"
            radius: 22
            Text {
                anchors.centerIn: parent
                text: "💡"
                font.pixelSize: 24
            }
        }

        Column {
            anchors.left: iconBox.right
            anchors.leftMargin: 15
            anchors.right: parent.right
            anchors.rightMargin: 15
            anchors.verticalCenter: parent.verticalCenter
            spacing: 6

            Text {
                text: root.titleText
                color: "#2d1b0e"
                font.family: "Minecraft Default"
                font.pixelSize: 17
                font.bold: true
            }
            Text {
                text: root.bodyText
                color: "#6a5040"
                font.family: "Minecraft Default"
                font.pixelSize: 14
                wrapMode: Text.WordWrap
                width: parent.width
            }
        }
    }

    Timer {
        id: hideTimer
        interval: 4000
        onTriggered: hideNotification()
    }

    function showNotification(title, body) {
        titleText = title
        bodyText = body
        root.x = Screen.desktopAvailableWidth - root.width - 25
        root.y = Screen.desktopAvailableHeight - root.height - 25
        root.visible = true
        root.opacity = 1
        root.requestActivate()
        hideTimer.restart()
    }

    function hideNotification() {
        root.opacity = 0
        hideTimer.stop()
    }

    onOpacityChanged: {
        if (opacity === 0) root.visible = false
    }
}