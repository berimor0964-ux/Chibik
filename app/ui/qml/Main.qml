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

            var charCenterX = rootWindow.x + (rootWindow.width / 2)
            var charTopY = rootWindow.y

            if (action === "talk") {
                chatWindow.visible = true
                chatWindow.show()
                chatWindow.raise()
                chatWindow.requestActivate()
            }
            else if (action === "feed") {
                // Если персонаж спал - будим
                if (chibik.currentState === "sleep") {
                    chibik.currentState = "idle"
                }
                bubble.showBubble(charCenterX, charTopY, "Спасибо! ♥")
            }
            else if (action === "state") {
                notificationWindow.showNotification("Состояние", "Энергия: 80%, Голод: 20%")
            }
            else if (action === "memory") {
                notificationWindow.showNotification("Память", "Я помню, как мы пили кофе.")
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
}