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
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint

    property string sceneMode: "room"
    property real time: 0

    NumberAnimation on time {
        from: 0; to: 1000000
        duration: 1000000
        loops: Animation.Infinite
    }

    // ===== КОМНАТА (приглушённая палитра dusty rose) =====
    Rectangle {
        id: room
        anchors.fill: parent
        visible: rootWindow.sceneMode === "room"

        // Стена — приглушённый пыльно-розовый
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: "#f0e4e8" }
            GradientStop { position: 0.65; color: "#f5e8ec" }
            GradientStop { position: 1.0; color: "#ece0e4" }
        }

        // Нежный узор
        Repeater {
            model: 25
            Rectangle {
                x: 30 + (index * 53) % (parent.width - 60)
                y: 20 + (index * 37) % 180
                width: 5; height: 5
                color: "#d8b8c0"
                radius: 2.5
                opacity: 0.2
            }
        }

        // Пол — приглушённый персиково-бежевый
        Rectangle {
            id: floor
            anchors.bottom: parent.bottom
            width: parent.width
            height: parent.height * 0.36
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0.0; color: "#e8d0c0" }
                GradientStop { position: 1.0; color: "#d8c0b8" }
            }

            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: 3
                color: "#c8a8a0"
                opacity: 0.5
            }

            Repeater {
                model: 5
                Rectangle {
                    x: (index + 1) * (parent.width / 6)
                    y: 8
                    width: 1
                    height: parent.height - 16
                    color: "#c0a8a0"
                    opacity: 0.35
                }
            }
        }

        // Ковёр — приглушённый
        Rectangle {
            x: 180; y: floor.y + 18
            width: 140; height: 50
            color: "#e0c0c8"
            radius: 25
            opacity: 0.85

            Rectangle {
                anchors.centerIn: parent
                width: parent.width - 30; height: parent.height - 16
                color: "#d8b0b8"
                radius: 18
                opacity: 0.6
            }
        }

        // Дверь — приглушённая
        Rectangle {
            x: 18
            y: floor.y - 120
            width: 60
            height: 120
            color: "#d8b0b8"
            radius: 28

            Rectangle {
                x: 6; y: 6
                width: parent.width - 12
                height: parent.height - 6
                color: "#e0c0c8"
                radius: 22

                Rectangle {
                    x: 8; y: 12
                    width: parent.width - 16
                    height: 40
                    color: "#e8ccd4"
                    radius: 12
                }
                Rectangle {
                    x: 8; y: 60
                    width: parent.width - 16
                    height: 40
                    color: "#e8ccd4"
                    radius: 12
                }
                Rectangle {
                    x: parent.width - 18
                    y: parent.height / 2 - 6
                    width: 12; height: 12
                    color: "#d4b870"
                    radius: 6
                    opacity: 0.85
                }
            }
        }

        // Кровать — приглушённая
        Rectangle {
            x: 96
            y: floor.y - 60
            width: 130
            height: 60
            color: "#d8b8c0"
            radius: 16

            Rectangle {
                x: -4; y: -8
                width: 14
                height: parent.height + 8
                color: "#c8a0a8"
                radius: 7
            }

            Rectangle {
                x: 12; y: 6
                width: parent.width - 20
                height: parent.height - 12
                color: "#f0e4e8"
                radius: 10

                Rectangle {
                    x: 8; y: 8
                    width: 36; height: 20
                    color: "#ffffff"
                    radius: 10
                    opacity: 0.85
                }
                Rectangle {
                    x: 48; y: 8
                    width: parent.width - 58
                    height: parent.height - 16
                    color: "#d8b8c0"
                    radius: 8
                    opacity: 0.75
                }
            }
        }

        // Окно — приглушённое
        Rectangle {
            x: parent.width - 140
            y: 25
            width: 110
            height: 90
            color: "#b8d8e0"
            radius: 42

            Rectangle {
                x: 16; y: 16
                width: 26; height: 26
                color: "#f0d870"
                radius: 13
                opacity: 0.85
            }
            Rectangle {
                x: 55; y: 45
                width: 28; height: 10
                color: "#ffffff"
                radius: 5
                opacity: 0.8
            }
            Rectangle { x: 50; y: 0; width: 2; height: parent.height; color: "#d8b8c0"; opacity: 0.5 }
            Rectangle { x: 0; y: 42; width: parent.width; height: 2; color: "#d8b8c0"; opacity: 0.5 }

            Rectangle {
                anchors.top: parent.bottom
                anchors.topMargin: -2
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width + 10
                height: 5
                color: "#d8b8c0"
                radius: 2
                opacity: 0.7
            }
        }

        // Картина
        Rectangle {
            x: 200; y: 55
            width: 55; height: 45
            color: "#ffffff"
            radius: 5
            opacity: 0.9

            Rectangle {
                x: 5; y: 5
                width: parent.width - 10
                height: parent.height - 10
                color: "#b8d8e0"
                radius: 2
            }
            Rectangle {
                x: 10; y: 10
                width: 12; height: 12
                color: "#f0d870"
                radius: 6
            }
            Rectangle {
                x: 5; y: parent.height - 16
                width: parent.width - 10
                height: 11
                color: "#a8d0a8"
                radius: 5
            }
        }

        // Часы
        Rectangle {
            x: 290; y: 50
            width: 40; height: 40
            color: "#ffffff"
            radius: 20
            opacity: 0.9

            Rectangle {
                x: parent.width / 2 - 1; y: 8
                width: 2; height: 12
                color: "#b89098"
                rotation: 30
            }
            Rectangle {
                x: parent.width / 2 - 1; y: 12
                width: 2; height: 8
                color: "#b89098"
                rotation: 90
            }
            Rectangle {
                anchors.centerIn: parent
                width: 4; height: 4
                color: "#b89098"
                radius: 2
            }
        }

        // Столик с растением
        Rectangle {
            x: parent.width - 100
            y: floor.y - 45
            width: 75; height: 6
            color: "#b89098"
            radius: 3
            opacity: 0.85
        }
        Rectangle {
            x: parent.width - 90
            y: floor.y - 38
            width: 4; height: 38
            color: "#a88088"
            opacity: 0.8
        }
        Rectangle {
            x: parent.width - 35
            y: floor.y - 38
            width: 4; height: 38
            color: "#a88088"
            opacity: 0.8
        }
        Rectangle {
            x: parent.width - 75
            y: floor.y - 70
            width: 26; height: 25
            color: "#d8a0a8"
            radius: 5
        }
        Rectangle {
            x: parent.width - 70
            y: floor.y - 95
            width: 10; height: 20
            color: "#98c898"
            radius: 5
            rotation: -20
        }
        Rectangle {
            x: parent.width - 58
            y: floor.y - 95
            width: 10; height: 20
            color: "#a8d0a8"
            radius: 5
            rotation: 20
        }
        Rectangle {
            x: parent.width - 64
            y: floor.y - 105
            width: 8; height: 22
            color: "#88b888"
            radius: 4
        }

        // Плавающие сердечки — приглушённые
        Repeater {
            model: 5
            Rectangle {
                width: 10; height: 10
                color: "#d890a0"
                radius: 5
                opacity: 0.4
                x: 40 + index * 90
                y: 30 + Math.sin((rootWindow.time + index * 200) / 100) * 15
            }
        }
    }

    // ===== ДВОР (приглушённая палитра) =====
    Item {
        id: outsideScene
        anchors.fill: parent
        visible: rootWindow.sceneMode === "outside"

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0.0; color: "#b8d8e8" }
                GradientStop { position: 0.65; color: "#d8e8f0" }
                GradientStop { position: 1.0; color: "#f0e4e8" }
            }
        }

        // Солнце — приглушённое
        Rectangle {
            x: parent.width - 120
            y: 20
            width: 75; height: 75
            color: "#f0d870"
            radius: 37

            Rectangle {
                anchors.centerIn: parent
                width: parent.width + 20
                height: parent.height + 20
                color: "#f0d870"
                radius: 47
                opacity: 0.2
            }
            Rectangle {
                anchors.centerIn: parent
                width: parent.width + 40
                height: parent.height + 40
                color: "#f0d870"
                radius: 57
                opacity: 0.1
            }
        }

        // Облака
        Repeater {
            model: 3
            Rectangle {
                x: 45 + index * 120 + Math.sin((rootWindow.time + index * 300) / 200) * 12
                y: 35 + (index % 2) * 20 + Math.cos((rootWindow.time + index * 200) / 250) * 6
                width: 85 - index * 8
                height: 30
                color: "#ffffff"
                radius: 15
                opacity: 0.75
            }
        }

        // Трава — приглушённая
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 140
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0.0; color: "#98c898" }
                GradientStop { position: 1.0; color: "#88b888" }
            }
            radius: 10
        }

        // Забор — приглушённый
        Repeater {
            model: 5
            Rectangle {
                x: 200 + index * 50
                y: parent.height - 180
                width: 6; height: 40
                color: "#d8b8c0"
                radius: 3
                opacity: 0.8
            }
        }
        Rectangle {
            x: 200
            y: parent.height - 165
            width: 206
            height: 3
            color: "#d8b8c0"
            radius: 1
            opacity: 0.65
        }

        // Дом — приглушённый
        Rectangle {
            x: 25
            y: parent.height - 250
            width: 165
            height: 140
            color: "#f5e8ec"
            radius: 22

            Rectangle {
                x: -10; y: -28
                width: parent.width + 20
                height: 38
                color: "#d890a0"
                radius: 18
                opacity: 0.85
            }

            Rectangle {
                x: parent.width - 45
                y: -50
                width: 20; height: 28
                color: "#c88090"
                radius: 3
                opacity: 0.85
            }

            Rectangle {
                x: parent.width - 42
                y: -65 + Math.sin(rootWindow.time / 150) * 5
                width: 12; height: 12
                color: "#ffffff"
                radius: 6
                opacity: 0.55
            }

            Rectangle {
                x: 25; y: 30
                width: 45; height: 45
                color: "#b8d8e0"
                radius: 22

                Rectangle { x: 20; y: 0; width: 2; height: parent.height; color: "#d8b8c0"; opacity: 0.5 }
                Rectangle { x: 0; y: 20; width: parent.width; height: 2; color: "#d8b8c0"; opacity: 0.5 }
            }

            Rectangle {
                x: 100; y: 70
                width: 45; height: 70
                color: "#e0c0c8"
                radius: 22

                Rectangle {
                    x: parent.width - 12
                    y: parent.height / 2
                    width: 7; height: 7
                    color: "#d4b870"
                    radius: 3
                    opacity: 0.85
                }
            }
        }

        // Дерево — приглушённое
        Rectangle {
            x: parent.width - 130
            y: parent.height - 210
            width: 14; height: 80
            color: "#907050"
            radius: 5
            opacity: 0.85
        }
        Rectangle {
            x: parent.width - 170
            y: parent.height - 280
            width: 90; height: 90
            color: "#88c088"
            radius: 45
            opacity: 0.85
        }
        Rectangle {
            x: parent.width - 150
            y: parent.height - 300
            width: 50; height: 50
            color: "#98c898"
            radius: 25
            opacity: 0.8
        }

        Repeater {
            model: 4
            Rectangle {
                x: parent.width - 165 + index * 20
                y: parent.height - 275 + (index % 2) * 18
                width: 7; height: 7
                color: "#d890a0"
                radius: 3
                opacity: 0.8
            }
        }

        // Бабочка — приглушённая
        Rectangle {
            width: 16; height: 10
            x: 240 + Math.sin(rootWindow.time / 80) * 35
            y: 110 + Math.cos(rootWindow.time / 60) * 20
            color: "transparent"

            Rectangle {
                anchors.left: parent.left
                width: 7; height: 9
                color: "#d890a0"
                radius: 3
                rotation: Math.sin(rootWindow.time / 20) * 25
            }
            Rectangle {
                anchors.right: parent.right
                width: 7; height: 9
                color: "#d8b8c0"
                radius: 3
                rotation: -Math.sin(rootWindow.time / 20) * 25
            }
        }

        // Цветы — приглушённые
        Repeater {
            model: 5
            Rectangle {
                x: 35 + index * 75
                y: parent.height - 90 + (index % 3) * 18
                width: 9; height: 9
                color: index % 2 === 0 ? "#d890a0" : "#f0d870"
                radius: 4
                opacity: 0.8
            }
        }

        // Дорожка
        Rectangle {
            x: 120
            y: parent.height - 150
            width: parent.width - 170
            height: 8
            color: "#e8d8c0"
            radius: 4
            opacity: 0.55
        }
    }

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
            chibik.energy = energy; chibik.hunger = hunger; chibik.fun = fun
        }
    }

    Connections {
        target: settingsWindow
        function onSettingsApplied(scale, alwaysOnTop, autoRotate) {
            chibik.scale = scale
            bridge.setAutoRotate(autoRotate)
            var baseFlags = Qt.FramelessWindowHint | Qt.Tool | Qt.NoDropShadowWindowHint
            rootWindow.flags = alwaysOnTop ? (baseFlags | Qt.WindowStaysOnTopHint) : baseFlags
        }
    }

    Shortcut { sequence: "Escape"; onActivated: Qt.exit(0) }
}