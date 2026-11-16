import QtQuick

Item {
    id: root

    width: 128
    height: 128

    // Данные
    property string sceneMode: "room"
    property string characterId: ""
    property string currentState: "idle"
    property string direction: "right"
    property real energy: 100
    property real hunger: 50
    property real fun: 50
    property var targetWindow: null

    // Ссылки и состояния
    property var speechBubble: null
    property bool wasDragged: false
    property bool eating: false

    property alias contextMenu: contextMenu
    signal actionRequested(string action)

    // Пути
    readonly property string framesPath:
        assetsUrl + "/characters/chibik"

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

    function say(text) {
        if (!root.speechBubble) return
        var gp = root.mapToGlobal(root.width / 2, 0)
        root.speechBubble.showBubble(gp.x, gp.y, text)
    }

    Behavior on scale {
        NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
    }

    Image {
        id: characterImage
        anchors.fill: parent
        source: root.currentFile
        smooth: false
        fillMode: Image.PreserveAspectFit
        cache: true
        asynchronous: false

        onStatusChanged: {
            if (status === Image.Error) {
                console.error("Не удалось загрузить спрайт Миры:", source)
            } else if (status === Image.Ready) {
                console.log("Спрайт Миры загружен:", source)
            }
        }
    }

    // Файл нужно бросить прямо на спрайт Миры, а не просто на комнату.
    DropArea {
        anchors.fill: parent
        z: 20
        onEntered: root.eating = true
        onExited: root.eating = false
        onDropped: (drop) => {
            root.eating = false
            if (drop.urls && drop.urls.length > 0) {
                drop.acceptProposedAction()
                root.eating = true
                for (var i = 0; i < drop.urls.length; i++) {
                    bridge.eatFile(drop.urls[i].toString())
                }
                eatAnimation.restart()
            }
        }
    }

    SequentialAnimation {
        id: eatAnimation
        NumberAnimation { target: root; property: "scale"; to: 0.72; duration: 160; easing.type: Easing.InQuad }
        NumberAnimation { target: root; property: "scale"; to: 1.12; duration: 200; easing.type: Easing.OutBack }
        NumberAnimation { target: root; property: "scale"; to: 1.0; duration: 180; easing.type: Easing.OutQuad }
        ScriptAction { script: root.eating = false }
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
    sceneMode: root.sceneMode
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
        property real startCharacterX: 0
        property real startCharacterY: 0

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
            bridge.pauseMovement()
            cursorShape = Qt.ClosedHandCursor

            startCharacterX = root.x
            startCharacterY = root.y

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

            root.x = Math.max(8, Math.min(root.targetWindow.width - root.width - 8, startCharacterX + dx))
            root.y = Math.max(150, Math.min(root.targetWindow.height - root.height - 8, startCharacterY + dy))
        }

        onReleased: (mouse) => {
            if (mouse.button !== Qt.LeftButton) return
            cursorShape = Qt.OpenHandCursor
            bridge.moveCharacterToWindowPosition(
                root.targetWindow.x + Math.round(root.x),
                root.targetWindow.y + Math.round(root.y)
            )
            bridge.resumeMovement()

            if (!root.wasDragged && !contextMenu.visible && root.speechBubble) {
                var gp = dragArea.mapToGlobal(root.width / 2, 0)
                root.speechBubble.showBubble(gp.x, gp.y, "Мяу!")
            }
        }
    }
}