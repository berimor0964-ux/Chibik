import QtQuick
import QtQuick.Window
import QtQuick.Controls

Window {
    id: root

    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint
    color: "transparent"
    visible: false

    // Закрываем при потере фокуса
    onActiveChanged: {
        if (!active && visible) {
            hideNotification()
        }
    }

    property string titleText: "Уведомление"
    property string bodyText: ""

    width: 280
    height: 90

    opacity: 0
    Behavior on opacity { NumberAnimation { duration: 300 } }

    Rectangle {
        anchors.fill: parent
        color: "#2b2b2b"
        border.color: "#4a9eff"
        border.width: 2
        radius: 8

        Rectangle {
            id: iconBox
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            width: 40
            height: 40
            color: "#4a9eff"
            radius: 20

            Text {
                anchors.centerIn: parent
                text: "!"
                color: "white"
                font.pixelSize: 20
                font.bold: true
            }
        }

        Column {
            anchors.left: iconBox.right
            anchors.leftMargin: 10
            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            spacing: 4

            Text {
                text: root.titleText
                color: "white"
                font.family: "Minecraft Default"
                font.pixelSize: 16
                font.bold: true
                renderType: Text.NativeRendering
            }

            Text {
                text: root.bodyText
                color: "#bbb"
                font.family: "Minecraft Default"
                font.pixelSize: 14
                renderType: Text.NativeRendering
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

        root.x = Screen.desktopAvailableWidth - root.width - 20
        root.y = Screen.desktopAvailableHeight - root.height - 20

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
        if (opacity === 0) {
            root.visible = false
        }
    }
}