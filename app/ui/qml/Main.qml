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
    }

    Shortcut {
        sequence: "Escape"
        onActivated: Qt.quit()
    }

    Character {
        id: chibik
        anchors.fill: parent
        targetWindow: rootWindow
        characterId: "chibik"
        currentState: "idle"
        direction: "right"

        onActionRequested: (action) => {
            console.log("Персонаж:", characterId, "— действие:", action)
        }
    }
}