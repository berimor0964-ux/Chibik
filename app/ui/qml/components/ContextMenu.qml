import QtQuick
import QtQuick.Window

Window {
    id: root

    // ===== ФЛАГИ ОКНА =====
    flags: Qt.Window
         | Qt.FramelessWindowHint
         | Qt.WindowStaysOnTopHint
         | Qt.Tool
         | Qt.NoDropShadowWindowHint

    color: "transparent"
    visible: false

    width: 180
    height: column.height + 8

    signal actionSelected(string action)

    // ===== АВТОЗАКРЫТИЕ ПРИ ПОТЕРЕ ФОКУСА =====
    onActiveChanged: {
        if (!active && visible) {
            close()
        }
    }

    // ===== ВНЕШНИЙ ВИД =====
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
                    { text: "Поиграть",    action: "play" },
                    { separator: true },
                    { text: "Состояние",   action: "state" },
                    { text: "Память",      action: "memory" },
                    { separator: true },
                    { text: "Настройки",   action: "settings" },
                    { text: "Выход",       action: "quit" }
                ]

                delegate: Item {
                    width: column.width
                    height: modelData.separator ? 9 : 32

                    // Разделитель
                    Rectangle {
                        visible: modelData.separator === true
                        anchors.centerIn: parent
                        width: parent.width - 16
                        height: 1
                        color: "#555"
                    }

                    // Пункт
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
                            font.pixelSize: 14
                        }

                        MouseArea {
                            id: itemMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                var act = modelData.action
                                root.close()
                                if (act === "quit") {
                                    Qt.quit()
                                } else {
                                    root.actionSelected(act)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // ===== ESC =====
    Shortcut {
        sequence: "Escape"
        onActivated: root.close()
    }

    // ===== ОТКРЫТИЕ =====
    function openAt(globalX, globalY) {
        var menuW = root.width
        var menuH = root.height
        var maxX = Screen.desktopAvailableWidth - menuW
        var maxY = Screen.desktopAvailableHeight - menuH

        root.x = Math.min(Math.max(0, globalX), maxX)
        root.y = Math.min(Math.max(0, globalY), maxY)

        root.visible = true
        root.requestActivate()   // ← фокус для автозакрытия
    }

    function close() {
        root.visible = false
    }
}