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

    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    color: "#1e1e1e"
    title: "Настройки"

    // Масштаб для шрифтов и элементов (как в чате)
    property real zoom: 1.0
    property int baseFont: 14

    // Свойства для сохранения настроек
    property real characterScale: 1.0
    property bool alwaysOnTop: true
    property bool autoRotate: true
    property real volume: 0.7

    signal settingsApplied()

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
                        text: "Настройки"
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

            // ===== КОНТЕНТ =====
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 15 * root.zoom // Отступы тоже растут
                spacing: 15 * root.zoom

                // 1. Размер персонажа
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Размер:";
                        color: "white";
                        font.family: "Minecraft Default";
                        font.pixelSize: root.baseFont * root.zoom
                        Layout.preferredWidth: 90 * root.zoom
                    }
                    Slider {
                        id: sizeSlider
                        Layout.fillWidth: true
                        from: 0.5; to: 2.0; value: root.characterScale
                        onValueChanged: root.characterScale = value
                    }
                }

                // 2. Громкость
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Звук:";
                        color: "white";
                        font.family: "Minecraft Default";
                        font.pixelSize: root.baseFont * root.zoom
                        Layout.preferredWidth: 90 * root.zoom
                    }
                    Slider {
                        id: volumeSlider
                        Layout.fillWidth: true
                        from: 0.0; to: 1.0; value: root.volume
                        onValueChanged: root.volume = value
                    }
                }

                // 3. Всегда поверх окон
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Поверх окон:";
                        color: "white";
                        font.family: "Minecraft Default";
                        font.pixelSize: root.baseFont * root.zoom
                        Layout.fillWidth: true
                    }
                    Switch {
                        checked: root.alwaysOnTop
                        onCheckedChanged: root.alwaysOnTop = checked
                    }
                }

                // 4. Автоповорот персонажа
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Автоповорот:";
                        color: "white";
                        font.family: "Minecraft Default";
                        font.pixelSize: root.baseFont * root.zoom
                        Layout.fillWidth: true
                    }
                    Switch {
                        checked: root.autoRotate
                        onCheckedChanged: root.autoRotate = checked
                    }
                }

                Item { Layout.fillHeight: true } // Отталкивает кнопку вниз

                // Кнопка ПРИМЕНИТЬ
                Button {
                    text: "Применить"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40 * root.zoom

                    background: Rectangle {
                        color: parent.pressed ? "#3a7a4a" : "#4a9eff"
                        radius: 6
                    }

                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        font.family: "Minecraft Default"
                        font.pixelSize: root.baseFont * root.zoom
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    onClicked: {
                        root.settingsApplied()
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