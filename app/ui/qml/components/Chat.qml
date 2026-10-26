import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts

Window {
    id: root

    property int baseWidth: 380
    property int baseHeight: 500
    width: baseWidth
    height: baseHeight

    minimumWidth: 300
    minimumHeight: 400

    // Оставляем стандартную рамку, чтобы ресайз работал идеально
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "#1e1e1e" // Строго темный фон
    title: "Чат"

    // Масштаб для шрифтов и элементов
    property real zoom: 1.0
    property int baseFont: 16

    ListModel {
        id: chatModel
    }

    Item {
        id: mainContainer
        width: root.width
        height: root.height

        // Растем вправо и вниз
        transformOrigin: Item.TopLeft

        Rectangle {
            anchors.fill: parent
            color: "#1e1e1e"
            border.color: "#444"
            border.width: 2
            radius: 8

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // ===== ШАПКА =====
                Rectangle {
                    Layout.fillWidth: true
                    height: 45
                    color: "#2b2b2b"
                    radius: 6

                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: 8
                        color: "#2b2b2b"
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
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 6

                        Text {
                            text: "Chibik"
                            color: "white"
                            font.family: "Minecraft Default"
                            font.pixelSize: 18 * root.zoom
                            font.bold: true
                            Layout.fillWidth: true
                        }

                        // Кнопка минус
                        Rectangle {
                            width: 30; height: 30; radius: 15
                            color: "#444"
                            Text { anchors.centerIn: parent; text: "-"; color: "white"; font.pixelSize: 20; font.bold: true; y: -2 }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: { if (root.zoom > 0.8) root.zoom -= 0.1 }
                                hoverEnabled: true
                                onEntered: parent.color = "#4a9eff"
                                onExited: parent.color = "#444"
                            }
                        }

                        // Кнопка плюс
                        Rectangle {
                            width: 30; height: 30; radius: 15
                            color: "#444"
                            Text { anchors.centerIn: parent; text: "+"; color: "white"; font.pixelSize: 20; font.bold: true; y: -2 }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: { if (root.zoom < 1.4) root.zoom += 0.1 }
                                hoverEnabled: true
                                onEntered: parent.color = "#4a9eff"
                                onExited: parent.color = "#444"
                            }
                        }

                        // Кнопка закрыть
                        Rectangle {
                            width: 30; height: 30; radius: 15
                            color: "#553333"
                            Text { anchors.centerIn: parent; text: "✕"; color: "#ff5555"; font.pixelSize: 16; font.bold: true }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: root.hide()
                                hoverEnabled: true
                                onEntered: parent.color = "#ff5555"
                                onExited: parent.color = "#553333"
                            }
                        }
                    }
                }

                // ===== ИСТОРИЯ =====
                ListView {
                    id: chatList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: 10
                    clip: true
                    spacing: 8
                    model: chatModel

                    delegate: Rectangle {
                        width: chatList.width
                        // Высота подстраивается под масштаб и текст
                        height: messageText.implicitHeight + (16 * root.zoom)
                        color: sender === "Вы" ? "#3a5a7a" : "#3a3a3a"
                        border.color: "#555"
                        border.width: 1
                        radius: 8

                        Text {
                            id: messageText
                            anchors.fill: parent
                            anchors.margins: 8 * root.zoom
                            text: sender + ": " + message
                            color: "white"
                            font.family: "Minecraft Default"
                            font.pixelSize: root.baseFont * root.zoom // Шрифт меняется
                            wrapMode: Text.WordWrap
                        }
                    }
                    onCountChanged: {
                        Qt.callLater(function() { chatList.positionViewAtEnd() })
                    }
                }

                // ===== ВВОД =====
                RowLayout {
                    Layout.fillWidth: true
                    Layout.margins: 10
                    spacing: 8

                                        TextField {
                        id: inputField
                        Layout.fillWidth: true
                        height: 36 * root.zoom
                        color: "white"
                        font.family: "Minecraft Default"
                        font.pixelSize: root.baseFont * root.zoom
                        placeholderText: "Сообщение..."

                        background: Rectangle {
                            color: "#2b2b2b"
                            radius: 6
                            border.color: "#4a9eff"
                            border.width: 1
                        }
                        onAccepted: sendButton.clicked()
                    }

                    Button {
                        id: sendButton
                        width: 45 * root.zoom // Кнопка растет
                        height: 36 * root.zoom
                        text: ">"
                        font.pixelSize: root.baseFont * root.zoom
                        background: Rectangle {
                            color: parent.pressed ? "#3a7a4a" : "#4a9eff"
                            radius: 6
                        }
                        onClicked: {
                            if (inputField.text.length === 0) return
                            chatModel.append({ "sender": "Вы", "message": inputField.text })
                            var userText = inputField.text
                            inputField.text = ""
                            chatModel.append({ "sender": "Chibik", "message": "Ты сказал: " + userText })
                        }
                    }
                }
            }
        }
    }

    // Сворачивание при клике мимо
    onActiveChanged: {
        if (!active && visible) {
            root.showMinimized()
        }
    }

    onClosing: function(close) {
        close.accepted = false
        root.hide()
    }
}