import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts

Window {
    id: root
    width: 400
    height: 500
    minimumWidth: 320
    minimumHeight: 400
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"
    title: "Чат с Мирой"

    property real zoom: 1.0
    property int baseFont: 16

    ListModel { id: chatModel }

    Rectangle {
        anchors.fill: parent
        color: "#f4e4c1"
        border.color: "#2d1b0e"
        border.width: 4

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            // Шапка
            Rectangle {
                Layout.fillWidth: true
                height: 48
                color: "#5d4037"

                // Нижняя граница шапки (вместо border.bottomColor)
                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: 4
                    color: "#2d1b0e"
                }

                MouseArea {
                    anchors.fill: parent
                    property point clickPos: "0,0"
                    onPressed: (mouse) => clickPos = Qt.point(mouse.x, mouse.y)
                    onPositionChanged: (mouse) => {
                        if (pressed) {
                            root.x += mouse.x - clickPos.x
                            root.y += mouse.y - clickPos.y
                        }
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 8

                    Text {
                        text: "ЧАТ"
                        color: "#f4e4c1"
                        font.family: "Minecraft Default"
                        font.pixelSize: 18 * root.zoom
                        font.bold: true
                        Layout.fillWidth: true
                    }

                    Rectangle {
                        width: 32; height: 32
                        color: "#8d6e63"
                        border.color: "#2d1b0e"
                        border.width: 2
                        Text {
                            anchors.centerIn: parent
                            text: "✕"
                            color: "#f4e4c1"
                            font.family: "Minecraft Default"
                            font.pixelSize: 18
                            font.bold: true
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: root.hide()
                        }
                    }
                }
            }

            ListView {
                id: chatList
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 12
                clip: true
                spacing: 8
                model: chatModel

                delegate: Rectangle {
                    width: chatList.width
                    height: messageText.implicitHeight + 24
                    color: sender === "Вы" ? "#d4c4a8" : "#ffffff"
                    border.color: "#2d1b0e"
                    border.width: 2

                    Text {
                        id: messageText
                        anchors.fill: parent
                        anchors.margins: 10
                        text: sender + ": " + message
                        color: "#2d1b0e"
                        font.family: "Minecraft Default"
                        font.pixelSize: root.baseFont * root.zoom
                        wrapMode: Text.WordWrap
                    }
                }
                onCountChanged: Qt.callLater(function() {
                    chatList.positionViewAtEnd()
                })
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.margins: 12
                spacing: 8

                TextField {
                    id: inputField
                    Layout.fillWidth: true
                    height: 40 * root.zoom
                    color: "#2d1b0e"
                    font.family: "Minecraft Default"
                    font.pixelSize: root.baseFont * root.zoom
                    placeholderText: "Сообщение..."
                    placeholderTextColor: "#8d6e63"

                    background: Rectangle {
                        color: "#ffffff"
                        border.color: "#2d1b0e"
                        border.width: 2
                    }
                    onAccepted: sendButton.clicked()
                }

                Rectangle {
                    width: 45 * root.zoom
                    height: 40 * root.zoom
                    color: sendButtonMouse.pressed ? "#8d6e63" : "#5d4037"
                    border.color: "#2d1b0e"
                    border.width: 2

                    Text {
                        anchors.centerIn: parent
                        text: "➤"
                        color: "#f4e4c1"
                        font.family: "Minecraft Default"
                        font.pixelSize: root.baseFont * root.zoom
                    }

                    MouseArea {
                        id: sendButtonMouse
                        anchors.fill: parent
                        onClicked: {
                            if (inputField.text.length === 0) return
                            var userText = inputField.text.trim()
                            if (userText.length === 0) return
                            chatModel.append({
                                "sender": "Вы",
                                "message": userText
                            })
                            inputField.text = ""
                            bridge.sendChatMessage(userText)
                        }
                    }
                }
            }
        }
    }

    onClosing: function(close) {
        close.accepted = false
        root.hide()
    }

    Connections {
        target: bridge
        function onChatResponse(text) {
            chatModel.append({ "sender": "Мира", "message": text })
        }
        function onChatFailed(text) {
            chatModel.append({ "sender": "Система", "message": text })
        }
    }
}