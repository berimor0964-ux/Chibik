import QtQuick

Rectangle {
    id: root

    property string text: ""
    property int maxWidth: 220

    width: Math.min(maxWidth, bubbleText.implicitWidth + 20)
    height: bubbleText.implicitHeight + 16
    radius: 10
    color: "white"
    border.color: "#888"
    border.width: 1

    visible: false

    Text {
        id: bubbleText
        anchors.centerIn: parent
        width: root.maxWidth - 20
        text: root.text
        wrapMode: Text.WordWrap
        color: "#222"
        font.pixelSize: 13
    }

    Timer {
        id: hideTimer
        interval: 5000
        onTriggered: root.visible = false
    }

    function show(text) {
        root.text = text
        root.visible = true
        hideTimer.restart()
    }
}