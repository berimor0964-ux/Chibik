import QtQuick
import QtQuick.Window

Window {
    id: root

    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint
    color: "transparent"
    visible: false

    // Закрываем меню, если оно потеряло фокус (кликнули мимо)
    onActiveChanged: {
        if (!active && visible) {
            close()
        }
    }

    width: 180
    height: column.height + 8

    signal actionSelected(string action)

    Rectangle {
        anchors.fill: parent
        color: "#2b2b2b"
        border.color: "#555"
        border.width: 1
        radius: 8

        Column {
            id: column
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 4
            spacing: 2

            Repeater {
                    model: [
                    { text: "Поговорить",  action: "talk" },
                    { text: "Покормить",   action: "feed" },
                    { separator: true },
                    { text: "Состояние",   action: "state" },
                    { text: "Память",      action: "memory" },
                    { text: "Настройки",   action: "settings" },
                    { separator: true },
                    { text: "Выход",       action: "quit" }
                ]

                delegate: Item {
                    width: column.width
                    height: modelData.separator ? 9 : 36

                    Rectangle {
                        visible: modelData.separator === true
                        anchors.centerIn: parent
                        width: parent.width - 16
                        height: 1
                        color: "#555"
                    }

                    Rectangle {
                        visible: !modelData.separator
                        anchors.fill: parent
                        anchors.margins: 2
                        color: itemMouseArea.containsMouse ? "#4a9eff" : "transparent"
                        radius: 4

                        Text {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            verticalAlignment: Text.AlignVCenter
                            text: modelData.text || ""
                            color: "white"
                            font.family: "Minecraft Default"
                            font.pixelSize: 16
                        }

                        MouseArea {
                            id: itemMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                root.close()
                                root.actionSelected(modelData.action)
                            }
                        }
                    }
                }
            }
        }
    }

    Shortcut {
        sequence: "Escape"
        onActivated: root.close()
    }

    function openAt(globalX, globalY) {
        var menuW = root.width
        var menuH = root.height
        var maxX = Screen.desktopAvailableWidth - menuW
        var maxY = Screen.desktopAvailableHeight - menuH

        root.x = Math.min(Math.max(0, globalX), maxX)
        root.y = Math.min(Math.max(0, globalY), maxY)

        root.visible = true
        root.requestActivate()
    }

    function close() {
        root.visible = false
    }
}