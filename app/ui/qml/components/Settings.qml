import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts

Window {
    id: root
    width: 350
    height: 350
    minimumWidth: 300
    minimumHeight: 300
    flags: Qt.Window | Qt.FramelessWindowHint
         | Qt.WindowStaysOnTopHint | Qt.Tool
    color: "transparent"
    title: "Настройки"

    property real zoom: 1.0
    property int baseFont: 14
    property real characterScale: 1.0
    property bool alwaysOnTop: true
    property bool autoRotate: true

    // Сигнал с параметрами
    signal settingsApplied(real scale, bool alwaysOnTop, bool autoRotate)

    Rectangle {
        anchors.fill: parent
        color: "#f4e4c1"
        border.color: "#2d1b0e"
        border.width: 4

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            Rectangle {
                Layout.fillWidth: true
                height: 50
                color: "#5d4037"

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
                    anchors.leftMargin: 15
                    anchors.rightMargin: 15
                    spacing: 8

                    Text {
                        text: "⚙️ Настройки"
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

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 20
                spacing: 20

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "📏 Размер:"
                        color: "#2d1b0e"
                        font.family: "Minecraft Default"
                        font.pixelSize: root.baseFont * root.zoom
                        Layout.preferredWidth: 100
                    }
                    Slider {
                        id: sizeSlider
                        Layout.fillWidth: true
                        from: 0.5; to: 2.0; value: root.characterScale
                        onValueChanged: root.characterScale = value
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "📌 Поверх окон:"
                        color: "#2d1b0e"
                        font.family: "Minecraft Default"
                        font.pixelSize: root.baseFont * root.zoom
                        Layout.fillWidth: true
                    }
                    Switch {
                        checked: root.alwaysOnTop
                        onCheckedChanged: root.alwaysOnTop = checked
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "🔄 Автоповорот:"
                        color: "#2d1b0e"
                        font.family: "Minecraft Default"
                        font.pixelSize: root.baseFont * root.zoom
                        Layout.fillWidth: true
                    }
                    Switch {
                        checked: root.autoRotate
                        onCheckedChanged: root.autoRotate = checked
                    }
                }

                Item { Layout.fillHeight: true }

                Button {
                    text: "✨ Применить"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 45 * root.zoom
                    background: Rectangle {
                        color: parent.pressed ? "#8d6e63" : "#5d4037"
                        radius: 10
                        border.color: "#2d1b0e"
                        border.width: 2
                    }
                    contentItem: Text {
                        text: parent.text
                        color: "#f4e4c1"
                        font.family: "Minecraft Default"
                        font.pixelSize: root.baseFont * root.zoom
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        root.settingsApplied(
                            root.characterScale,
                            root.alwaysOnTop,
                            root.autoRotate
                        )
                        root.hide()
                    }
                }
            }
        }
    }

    onClosing: function(close) {
        close.accepted = false
        root.hide()
    }
}