import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Window {
    id: root
    width: 400
    height: 500
    title: "Чат с персонажем"
    flags: Qt.Window | Qt.WindowStaysOnTopHint

    property var messages: []

    function addMessage(sender, text) {
        var arr = root.messages.slice()
        arr.push({ sender: sender, text: text })
        root.messages = arr
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        ListView {
            id: listView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            model: root.messages
            onCountChanged: positionViewAtEnd()

            delegate: Rectangle {
                width: listView.width
                height: label.implicitHeight + 16
                radius: 8
                color: modelData.sender === "user" ? "#dcf8c6" : "#f0f0f0"

                Text {
                    id: label
                    anchors.fill: parent
                    anchors.margins: 8
                    text: modelData.text
                    wrapMode: Text.WordWrap
                    color: "#222"
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            TextField {
                id: input
                Layout.fillWidth: true
                placeholderText: "Написать сообщение..."
                onAccepted: sendButton.clicked()
            }

            Button {
                id: sendButton
                text: "▶"
                enabled: input.text.length > 0
                onClicked: {
                    var text = input.text.trim()
                    if (text.length > 0) {
                        root.addMessage("user", text)
                        bridge.sendChatMessage(text)
                        input.text = ""
                    }
                }
            }
        }
    }
}