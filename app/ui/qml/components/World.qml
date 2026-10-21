import QtQuick

Item {
    id: root
    anchors.fill: parent

    property var characters: ({})
    property var objects: ({})
    property bool editorMode: false

    // ---- Персонажи ----
    function addCharacter(id, x, y) {
        if (characters[id]) return
        var comp = Qt.createComponent("character.qml")
        if (comp.status !== Component.Ready) {
            console.error("character.qml error:", comp.errorString())
            return
        }
        var obj = comp.createObject(root, {
            characterId: id,
            x: x - 32,
            y: y - 64
        })
        characters[id] = obj
    }

    function updateCharacterPosition(id, x, y) {
        if (characters[id]) {
            characters[id].x = x - 32
            characters[id].y = y - 64
        }
    }

    function setCharacterState(id, state) {
        if (characters[id]) {
            characters[id].currentState = state
        }
    }

    function characterSay(id, text) {
        if (characters[id]) {
            characters[id].say(text)
        }
    }

    // ---- Объекты ----
    function addObject(id, type, x, y) {
        if (objects[id]) return
        var comp = Qt.createComponent("object.qml")
        if (comp.status !== Component.Ready) {
            console.error("object.qml error:", comp.errorString())
            return
        }
        var obj = comp.createObject(root, {
            objectId: id,
            objectType: type,
            editorMode: root.editorMode,
            x: x - 32,
            y: y - 64
        })
        objects[id] = obj
    }

    function removeObject(id) {
        if (objects[id]) {
            objects[id].destroy()
            delete objects[id]
        }
    }

    onEditorModeChanged: {
        for (var k in objects) {
            objects[k].editorMode = editorMode
        }
    }
}