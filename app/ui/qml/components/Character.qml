import QtQuick

Item {
    id: root

    width: 128
    height: 128

    // Данные
    property string characterId: ""
    property string currentState: "idle"
    property string direction: "right"
    property var targetWindow: null

    // Ссылки и состояния
    property var speechBubble: null
    property bool wasDragged: false

    property alias contextMenu: contextMenu
    signal actionRequested(string action)

    // Пути
    readonly property string framesPath:
        "file:///" + assetsPath + "/characters/chibik"

    property int frameIndex: 1

    readonly property string currentSpriteName: {
        if (currentState === "walk") {
            return direction === "left" ? "walk_left" : "walk_right"
        }
        return currentState
    }

    readonly property string currentFile: {
        var frame = frameIndex < 10 ? "0" + frameIndex : "" + frameIndex
        return framesPath + "/" + currentSpriteName + "_" + frame + ".png"
    }

    Image {
        anchors.fill: parent
        source: root.currentFile
        smooth: false
        fillMode: Image.Pad
        cache: true
        asynchronous: true
    }

    Timer {
        interval: {
            switch (root.currentState) {
                case "sleep": return 2000
                case "walk":  return 300
                case "stand": return 1200
                default:      return 1200
            }
        }
        running: true
        repeat: true
        onTriggered: root.frameIndex = root.frameIndex === 1 ? 2 : 1
    }

    ContextMenu {
        id: contextMenu
        onActionSelected: (action) => {
            console.log("Действие:", action)
            root.actionRequested(action)
        }
    }

    MouseArea {
        id: dragArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        cursorShape: Qt.OpenHandCursor

        property real startMouseGlobalX: 0
        property real startMouseGlobalY: 0
        property real startWindowX: 0
        property real startWindowY: 0

        onPressed: (mouse) => {
            if (mouse.button === Qt.RightButton) {
                var gp = dragArea.mapToGlobal(mouse.x, mouse.y)
                contextMenu.openAt(gp.x, gp.y)
                return
            }

            if (contextMenu.visible) {
                contextMenu.close()
            }

            if (!root.targetWindow) {
                console.warn("targetWindow не передан из Main.qml!")
                return
            }

            root.wasDragged = false
            cursorShape = Qt.ClosedHandCursor

            startWindowX = root.targetWindow.x
            startWindowY = root.targetWindow.y

            var gp = dragArea.mapToGlobal(mouse.x, mouse.y)
            startMouseGlobalX = gp.x
            startMouseGlobalY = gp.y
        }

        onPositionChanged: (mouse) => {
            if (!pressed) return
            if (mouse.buttons !== Qt.LeftButton) return
            if (!root.targetWindow) return

            var gp = dragArea.mapToGlobal(mouse.x, mouse.y)
            var dx = gp.x - startMouseGlobalX
            var dy = gp.y - startMouseGlobalY

            if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
                root.wasDragged = true

                // ИСПРАВЛЕНО: Скрываем облако при перетаскивании
                if (root.speechBubble) {
                    root.speechBubble.hideBubble()
                }
            }

            root.targetWindow.x = startWindowX + dx
            root.targetWindow.y = startWindowY + dy
        }

        onReleased: (mouse) => {
            if (mouse.button !== Qt.LeftButton) return
            cursorShape = Qt.OpenHandCursor

            if (!root.wasDragged && !contextMenu.visible && root.speechBubble) {
                var gp = dragArea.mapToGlobal(root.width / 2, 0)
                root.speechBubble.showBubble(gp.x, gp.y, "Мяу!")
            }
        }
    }
}