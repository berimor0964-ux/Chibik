import QtQuick
import QtQuick.Window

Window {
    id: root
    flags: Qt.Window | Qt.FramelessWindowHint
         | Qt.WindowStaysOnTopHint
         | Qt.Tool | Qt.NoDropShadowWindowHint
    color: "transparent"
    visible: false

    property string sceneMode: "room"
    width: 180
    height: column.height + 8

    signal actionSelected(string action)

    onActiveChanged: {
        if (!active && visible) close()
    }

    Rectangle {
        anchors.fill: parent
        color: "#3e2723"
        border.color: "#2d1b0e"
        border.width: 3

        Column {
            id: column
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 4
            spacing: 2

            Repeater {
                model: [
                    { text: "Поговорить", action: "talk" },
                    { text: "Покормить",  action: "feed" },
                    { text: "Погулять",   action: "walk" },
                    { text: "Домой",      action: "home", hideInRoom: true },
                    { text: "Поспать",    action: "sleep" },
                    { separator: true },
                    { text: "Состояние",  action: "state" },
                    { text: "Память",     action: "memory" },
                    { text: "Настройки",  action: "settings" },
                    { separator: true },
                    { text: "Выход",      action: "quit" }
                ]

                delegate: Item {
                    width: column.width
                    height: modelData.separator ? 8 : 36
                    visible: !(modelData.hideInRoom
                               && root.sceneMode === "room")

                    Rectangle {
                        visible: modelData.separator === true
                        anchors.centerIn: parent
                        width: parent.width - 16
                        height: 2
                        color: "#2d1b0e"
                    }

                    Rectangle {
                        visible: !modelData.separator
                        anchors.fill: parent
                        anchors.margins: 2
                        color: itemMouseArea.containsMouse
                               ? "#8d6e63" : "transparent"

                        Text {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            verticalAlignment: Text.AlignVCenter
                            text: modelData.text || ""
                            color: "#f4e4c1"
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

    Shortcut { sequence: "Escape"; onActivated: root.close() }

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

    function close() { root.visible = false }
}