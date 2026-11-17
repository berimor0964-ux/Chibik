import QtQuick
import QtQuick.Window

Window {
    id: root
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint
    color: "transparent"
    visible: false

    property string sceneMode: "room"
    width: 210
    height: column.height + 16

    signal actionSelected(string action)

    onActiveChanged: { if (!active && visible) close() }

    // Тень
    Rectangle {
        anchors.fill: parent
        anchors.topMargin: 4
        anchors.leftMargin: 4
        z: -1
        color: "#20d87093"
        radius: 16
    }

    Rectangle {
        anchors.fill: parent
        color: "#fff0f5"
        border.color: "#ffb6c1"
        border.width: 3
        radius: 16

        Column {
            id: column
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 8
            spacing: 4

            Repeater {
                model: [
                    { text: "💬  Поговорить", action: "talk" },
                    { text: "🍕  Покормить", action: "feed" },
                    { text: "🚶  Погулять", action: "walk" },
                    { text: "🏠  Домой", action: "home", hideInRoom: true },
                    { text: "😴  Поспать", action: "sleep" },
                    { separator: true },
                    { text: "📊  Состояние", action: "state" },
                    { text: "💭  Память", action: "memory" },
                    { text: "⚙️  Настройки", action: "settings" },
                    { separator: true },
                    { text: "👋  Выход", action: "quit" }
                ]

                delegate: Item {
                    width: column.width
                    height: modelData.separator ? 12 : 40
                    visible: !(modelData.hideInRoom && root.sceneMode === "room")

                    Rectangle {
                        visible: modelData.separator === true
                        anchors.centerIn: parent
                        width: parent.width - 20
                        height: 2
                        color: "#ffb6c1"
                        radius: 1
                    }

                    Rectangle {
                        visible: !modelData.separator
                        anchors.fill: parent
                        anchors.margins: 2
                        color: itemMouseArea.containsMouse ? "#ffe4e1" : "#ffffff"
                        radius: 10
                        border.color: itemMouseArea.containsMouse ? "#ff69b4" : "#ffc0cb"
                        border.width: itemMouseArea.containsMouse ? 2 : 1
                        scale: itemMouseArea.containsMouse ? 1.02 : 1.0

                        Behavior on color { ColorAnimation { duration: 150 } }
                        Behavior on scale { NumberAnimation { duration: 150 } }
                        Behavior on border.color { ColorAnimation { duration: 150 } }

                        Text {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            verticalAlignment: Text.AlignVCenter
                            text: modelData.text || ""
                            color: "#d87093"
                            font.family: "Segoe UI"
                            font.pixelSize: 15
                            font.bold: itemMouseArea.containsMouse
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
        var menuW = root.width, menuH = root.height
        var maxX = Screen.desktopAvailableWidth - menuW
        var maxY = Screen.desktopAvailableHeight - menuH
        root.x = Math.min(Math.max(0, globalX), maxX)
        root.y = Math.min(Math.max(0, globalY), maxY)
        root.visible = true
        root.requestActivate()
    }

    function close() { root.visible = false }
}