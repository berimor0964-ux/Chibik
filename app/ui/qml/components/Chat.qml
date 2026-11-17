import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts

Window {
    id: root
    width: 420
    height: 520
    minimumWidth: 340
    minimumHeight: 420
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"
    title: "Чат с Мирой"

    property real zoom: 1.0
    property int baseFont: 16

    ListModel { id: chatModel }

    // Мягкая тень
    Rectangle {
        anchors.fill: parent
        anchors.topMargin: 6
        anchors.leftMargin: 6
        z: -1
        color: "#20d87093"
        radius: 24
    }

    Rectangle {
        anchors.fill: parent
        color: "#fff0f5"
        border.color: "#ffb6c1"
        border.width: 4
        radius: 24

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 0

            // Шапка с градиентом
            Rectangle {
                Layout.fillWidth: true
                height: 56
                radius: 18
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "#ffb6c1" }
                    GradientStop { position: 1.0; color: "#ff69b4" }
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
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    spacing: 10

                    Text {
                        text: "💬  Чат с Мирой"
                        color: "#ffffff"
                        font.family: "Segoe UI"
                        font.pixelSize: 18 * root.zoom
                        font.bold: true
                        Layout.fillWidth: true
                    }

                    Rectangle {
                        width: 36; height: 36
                        color: closeArea.containsMouse ? "#ffffff" : "#ffe4e1"
                        radius: 18
                        border.color: "#ffffff"
                        border.width: 2

                        Behavior on color { ColorAnimation { duration: 150 } }

                        Text {
                            anchors.centerIn: parent
                            text: "✕"
                            color: closeArea.containsMouse ? "#ff69b4" : "#d87093"
                            font.family: "Segoe UI"
                            font.pixelSize: 20
                            font.bold: true
                        }
                        MouseArea {
                            id: closeArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: root.hide()
                        }
                    }
                }
            }

            // История
            ListView {
                id: chatList
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 12
                clip: true
                spacing: 10
                model: chatModel

                delegate: Rectangle {
                    width: chatList.width
                    height: messageText.implicitHeight + 28
                    color: sender === "Вы" ? "#ffe4e1" : "#ffffff"
                    radius: 14
                    border.color: "#ffb6c1"
                    border.width: 2
                    opacity: 0
                    scale: 0.9

                    // Анимация появления
                    Behavior on opacity { NumberAnimation { duration: 250 } }
                    Behavior on scale { NumberAnimation { duration: 250; easing.type: Easing.OutBack } }

                    Component.onCompleted: { opacity = 1; scale = 1.0 }

                    Text {
                        id: messageText
                        anchors.fill: parent
                        anchors.margins: 12
                        text: sender + ": " + message
                        color: "#d87093"
                        font.family: "Segoe UI"
                        font.pixelSize: root.baseFont * root.zoom
                        wrapMode: Text.WordWrap
                    }
                }
                onCountChanged: Qt.callLater(function() { chatList.positionViewAtEnd() })
            }

            // Поле ввода
            RowLayout {
                Layout.fillWidth: true
                Layout.margins: 12
                spacing: 10

                TextField {
                    id: inputField
                    Layout.fillWidth: true
                    height: 44 * root.zoom
                    color: "#d87093"
                    font.family: "Segoe UI"
                    font.pixelSize: root.baseFont * root.zoom
                    placeholderText: "Напишите Мире..."
                    placeholderTextColor: "#ffb6c1"

                    background: Rectangle {
                        color: "#ffffff"
                        radius: 14
                        border.color: inputField.activeFocus ? "#ff69b4" : "#ffb6c1"
                        border.width: inputField.activeFocus ? 3 : 2

                        Behavior on border.color { ColorAnimation { duration: 200 } }
                        Behavior on border.width { NumberAnimation { duration: 200 } }
                    }
                    onAccepted: sendButton.clicked()
                }

                Rectangle {
                    id: sendButton
                    width: 48 * root.zoom
                    height: 44 * root.zoom
                    color: sendMouse.pressed ? "#ff69b4" : "#ffb6c1"
                    radius: 14

                    Behavior on color { ColorAnimation { duration: 150 } }

                    Text {
                        anchors.centerIn: parent
                        text: "➤"
                        color: "#ffffff"
                        font.family: "Segoe UI"
                        font.pixelSize: root.baseFont * root.zoom
                    }

                    MouseArea {
                        id: sendMouse
                        anchors.fill: parent
                        onClicked: {
                            if (inputField.text.length === 0) return
                            var userText = inputField.text.trim()
                            if (userText.length === 0) return
                            chatModel.append({ "sender": "Вы", "message": userText })
                            inputField.text = ""
                            bridge.sendChatMessage(userText)
                        }
                    }
                }
            }
        }
    }

    onClosing: function(close) { close.accepted = false; root.hide() }

    Connections {
        target: bridge
        function onChatResponse(text) { chatModel.append({ "sender": "Мира", "message": text }) }
        function onChatFailed(text) { chatModel.append({ "sender": "Система", "message": text }) }
    }
}