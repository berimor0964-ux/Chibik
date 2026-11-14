import QtQuick
import QtQuick.Window
import "components"

Window {
    id: rootWindow

    width: 128
    height: 128
    visible: true
    title: "Desktop Pet"

    color: "transparent"
    flags: Qt.FramelessWindowHint
         | Qt.WindowStaysOnTopHint
         | Qt.Tool
         | Qt.NoDropShadowWindowHint

    Component.onCompleted: {
        rootWindow.x = Screen.desktopAvailableWidth - rootWindow.width
        rootWindow.y = Screen.desktopAvailableHeight - rootWindow.height

        // Здоровение при запуске (через 1 секунду)
        Qt.callLater(function() {
            var charCenterX = rootWindow.x + (rootWindow.width / 2)
            var charTopY = rootWindow.y
            bubble.showBubble(charCenterX, charTopY, "Привет! Я снова тут.")
        })
    }

    Shortcut {
        sequence: "Escape"
        onActivated: Qt.exit(0)
    }

    Character {
        id: chibik
        anchors.fill: parent
        targetWindow: rootWindow
        characterId: "chibik"
        currentState: "idle"
        direction: "right"

        speechBubble: bubble

        onActionRequested: (action) => {
            console.log("Действие:", action)
            bridge.characterAction("chibik", action)

            var charCenterX = rootWindow.x + (rootWindow.width / 2)
            var charTopY = rootWindow.y

            if (action === "talk") {
                chatWindow.visible = true
                chatWindow.show()
                chatWindow.raise()
                chatWindow.requestActivate()
            }
            else if (action === "feed") {
                if (chibik.currentState === "sleep") chibik.currentState = "idle"
            }
            else if (action === "state" || action === "memory") {
                // Актуальные данные сообщает Python-модель персонажа.
            }
            else if (action === "settings") {
                settingsWindow.visible = true
                settingsWindow.show()
                settingsWindow.raise()
                settingsWindow.requestActivate()
            }
            else if (action === "quit") {
                exitWindow.openAtCenter()
            }
        }
    }

    SpeechBubble {
        id: bubble
    }

    Notification {
        id: notificationWindow
    }

    Chat {
        id: chatWindow
    }

    Settings {
        id: settingsWindow
    }

    ExitConfirm {
        id: exitWindow
    }

    Connections {
        target: bridge
        function onDesktopPositionChanged(x, y) {
            rootWindow.x = x
            rootWindow.y = y
        }
        function onDesktopStateChanged(state, direction) {
            chibik.currentState = state
            chibik.direction = direction
        }
        function onSpeechRequested(text) {
            bubble.showBubble(rootWindow.x + rootWindow.width / 2, rootWindow.y, text)
        }
        function onNeedsUpdated(energy, hunger, fun) {
            // Значения также доступны чату и будущему виджету состояния.
            chibik.energy = energy
            chibik.hunger = hunger
            chibik.fun = fun
        }
    }
}