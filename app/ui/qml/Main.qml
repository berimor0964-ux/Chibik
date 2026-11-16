import QtQuick
import QtQuick.Window
import "components"

Window {
    id: rootWindow
    width: houseWidth
    height: houseHeight
    x: houseX
    y: houseY
    visible: true
    title: "Chibik — домик Миры"
    color: "transparent"
    flags: Qt.FramelessWindowHint
         | Qt.WindowStaysOnTopHint
         | Qt.Tool
         | Qt.NoDropShadowWindowHint

    property string sceneMode: "room"

    // ===== КОМНАТА =====
    Rectangle {
        id: room
        anchors.fill: parent
        visible: rootWindow.sceneMode === "room"
        color: "#e6d5b8"
        border.color: "#2d1b0e"
        border.width: 4

        // Обои
        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: floor.top
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0.0; color: "#f4e4c1" }
                GradientStop { position: 1.0; color: "#e6d5b8" }
            }
        }

        // Пол
        Rectangle {
            id: floor
            anchors.bottom: parent.bottom
            width: parent.width
            height: parent.height * 0.38
            color: "#8b5a2b"

            // Верхняя граница пола (вместо border.topColor)
            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: 4
                color: "#6d4521"
            }

            Repeater {
                model: Math.floor(parent.width / 48)
                Rectangle {
                    x: index * 48
                    y: 0
                    width: 2
                    height: parent.height
                    color: "#6d4521"
                }
            }
            Repeater {
                model: 6
                Rectangle {
                    x: 0
                    y: index * (parent.height / 6)
                    width: parent.width
                    height: 2
                    color: "#5a3a1a"
                }
            }
        }

        // Окно
        Rectangle {
            x: parent.width - 150; y: 30; width: 120; height: 100
            color: "#87ceeb"
            border.color: "#5d4037"
            border.width: 6

            Rectangle { x: 53; y: 0; width: 6; height: parent.height; color: "#5d4037" }
            Rectangle { x: 0; y: 45; width: parent.width; height: 6; color: "#5d4037" }

            Rectangle { x: 15; y: 15; width: 24; height: 24; color: "#ffd966" }
            Rectangle { x: 15; y: 9; width: 24; height: 6; color: "#ffd966" }
            Rectangle { x: 15; y: 39; width: 24; height: 6; color: "#ffd966" }
            Rectangle { x: 9; y: 15; width: 6; height: 24; color: "#ffd966" }
            Rectangle { x: 39; y: 15; width: 6; height: 24; color: "#ffd966" }
        }

        // ДВЕРЬ СЛЕВА
        Rectangle {
            x: 16; y: floor.y - 140; width: 64; height: 140
            color: "#3e2723"

            Rectangle {
                x: 6; y: 6; width: parent.width - 12; height: parent.height - 6
                color: "#8d6e63"
                border.color: "#2d1b0e"
                border.width: 3

                Rectangle {
                    x: parent.width - 18; y: parent.height / 2 - 4
                    width: 8; height: 8; color: "#ffd966"
                }
            }
            Rectangle {
                anchors.bottom: parent.bottom
                x: -4; width: parent.width + 8; height: 6; color: "#2d1b0e"
            }
        }

        // КРОВАТЬ
        Rectangle {
            x: 96; y: floor.y - 70; width: 130; height: 70
            color: "#5d4037"

            Rectangle {
                x: 6; y: 6; width: parent.width - 12; height: parent.height - 12
                color: "#f4e4c1"
                border.color: "#2d1b0e"
                border.width: 2

                Rectangle {
                    x: 10; y: 10; width: 36; height: 24
                    color: "#ffffff"
                    border.color: "#2d1b0e"
                    border.width: 2
                }
                Rectangle {
                    x: 50; y: 10; width: parent.width - 62; height: parent.height - 16
                    color: "#ffb89e"
                    border.color: "#2d1b0e"
                    border.width: 2
                }
            }
        }

        // Стол и растение
        Rectangle {
            x: parent.width - 140; y: floor.y - 60
            width: 100; height: 8; color: "#5d4037"
        }
        Rectangle {
            x: parent.width - 130; y: floor.y - 52
            width: 8; height: 52; color: "#3e2723"
        }
        Rectangle {
            x: parent.width - 50; y: floor.y - 52
            width: 8; height: 52; color: "#3e2723"
        }
        Rectangle {
            x: parent.width - 125; y: floor.y - 85
            width: 24; height: 25; color: "#d4764e"
            border.color: "#2d1b0e"
            border.width: 2
        }
        Rectangle {
            x: parent.width - 121; y: floor.y - 110
            width: 16; height: 25; color: "#7ec87e"
        }
    }

    // ===== ДВОР =====
    Item {
        id: outsideScene
        anchors.fill: parent
        visible: rootWindow.sceneMode === "outside"

        Rectangle { anchors.fill: parent; color: "#87ceeb" }

        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 160
            color: "#7cb342"

            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: 4
                color: "#9ccc65"
            }
        }

        Rectangle {
            x: parent.width - 110; y: 30; width: 60; height: 60
            color: "#ffd966"
        }
        Rectangle {
            x: parent.width - 110; y: 20; width: 60; height: 10
            color: "#ffd966"
        }
        Rectangle {
            x: parent.width - 110; y: 90; width: 60; height: 10
            color: "#ffd966"
        }
        Rectangle {
            x: parent.width - 120; y: 30; width: 10; height: 60
            color: "#ffd966"
        }
        Rectangle {
            x: parent.width - 50; y: 30; width: 10; height: 60
            color: "#ffd966"
        }

        Rectangle {
            x: 30; y: parent.height - 260; width: 180; height: 160
            color: "#f5deb3"
            border.color: "#2d1b0e"
            border.width: 4

            Rectangle {
                x: -10; y: -24; width: parent.width + 20; height: 28
                color: "#d4764e"
                border.color: "#2d1b0e"
                border.width: 3
            }

            Rectangle {
                x: 50; y: 30; width: 50; height: 50
                color: "#87ceeb"
                border.color: "#2d1b0e"
                border.width: 4
                Rectangle { x: 22; y: 0; width: 4; height: parent.height; color: "#2d1b0e" }
                Rectangle { x: 0; y: 22; width: parent.width; height: 4; color: "#2d1b0e" }
            }

            Rectangle {
                x: 110; y: 80; width: 50; height: 80
                color: "#8d6e63"
                border.color: "#2d1b0e"
                border.width: 3
                Rectangle {
                    x: parent.width - 14; y: parent.height / 2 - 4
                    width: 8; height: 8; color: "#ffd966"
                }
            }
        }

        Text {
            x: parent.width / 2 - 80; y: 30
            text: "МИРА НА ПРОГУЛКЕ"
            color: "#2d1b0e"
            font.family: "Minecraft Default"
            font.pixelSize: 20
            font.bold: true
        }
    }

    // ===== ПЕРСОНАЖ =====
    Character {
        id: chibik
        x: Math.max(8, rootWindow.width / 2 - 64)
        y: rootWindow.height - 150
        width: 128
        height: 128
        targetWindow: rootWindow
        characterId: "chibik"
        currentState: "idle"
        direction: "right"
        speechBubble: bubble
        sceneMode: rootWindow.sceneMode

        onActionRequested: (action) => {
            bridge.characterAction("chibik", action)
            if (action === "talk") { chatWindow.visible = true; chatWindow.raise(); }
            else if (action === "settings") { settingsWindow.visible = true; settingsWindow.raise(); }
            else if (action === "quit") { exitWindow.openAtCenter(); }
        }
    }

    SpeechBubble { id: bubble }
    Chat { id: chatWindow }
    Settings { id: settingsWindow }
    ExitConfirm { id: exitWindow }

    Connections {
        target: bridge
        function onDesktopPositionChanged(x, y) {
            chibik.x = x - rootWindow.x
            chibik.y = y - rootWindow.y
            bubble.updateAnchor(x + chibik.width / 2, y + 6)
        }
        function onDesktopSceneChanged(mode) { rootWindow.sceneMode = mode }
        function onDesktopStateChanged(state, direction) {
            chibik.currentState = state
            chibik.direction = direction
        }
        function onSpeechRequested(text) {
            bubble.showBubble(rootWindow.x + chibik.x + chibik.width / 2,
                              rootWindow.y + chibik.y + 6, text)
        }
        function onNeedsUpdated(energy, hunger, fun) {
            chibik.energy = energy
            chibik.hunger = hunger
            chibik.fun = fun
        }
    }

    // Обработка настроек
    Connections {
        target: settingsWindow
        function onSettingsApplied(scale, alwaysOnTop, autoRotate) {
            chibik.scale = scale
            bridge.setAutoRotate(autoRotate)
            var baseFlags = Qt.FramelessWindowHint | Qt.Tool | Qt.NoDropShadowWindowHint
            rootWindow.flags = alwaysOnTop
                ? (baseFlags | Qt.WindowStaysOnTopHint)
                : baseFlags
        }
    }

    Shortcut { sequence: "Escape"; onActivated: Qt.exit(0) }
}