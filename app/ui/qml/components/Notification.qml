import QtQuick

Rectangle {
    id: root

    property string title: ""
    property string text: ""

    width: 320
    height: contentColumn.implicitHeight + 24
    color: "#2b2b2b"
    radius: 10
    border.color: "#555"
    border.width: 1

    opacity: 0
    Behavior on opacity { NumberAnimation { duration: 300 } }

    Column {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: 12
        spacing: 4

        Text {
            text: root.title
            color: "white"
            font.bold: true
            font.pixelSize: 14
        }
        Text {
            text: root.text
            color: "#cccccc"
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            width: parent.width
        }
    }

    Timer {
        interval: 5000
        running: true
        onTriggered: root.destroy()
    }

    Component.onCompleted: opacity = 1
}