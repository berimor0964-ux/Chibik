import QtQuick

Item {
    id: root

    property string objectId: ""
    property string objectType: ""
    property bool editorMode: false

    width: 64
    height: 64

    Image {
        anchors.fill: parent
        source: bridge.resolveObjectSprite(root.objectType)
        fillMode: Image.PreserveAspectFit
        smooth: true
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        onClicked: {
            if (root.editorMode) {
                bridge.requestRemoveObject(root.objectId)
            }
        }
    }
}