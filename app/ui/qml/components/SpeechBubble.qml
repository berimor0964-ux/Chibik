import QtQuick
import QtQuick.Window

Window {
    id: root

    flags: Qt.Window
         | Qt.FramelessWindowHint
         | Qt.WindowStaysOnTopHint
         | Qt.Tool
         | Qt.WindowTransparentForInput
         | Qt.NoDropShadowWindowHint

    color: "transparent"
    visible: false

    property string fullText: ""
    property int visibleChars: 0
    property int maxWidth: 220
    property int charDelay: 50
    property int hideDelay: 5000

    property real anchorX: 0
    property real anchorY: 0

    readonly property string displayText:
        fullText.substring(0, visibleChars)

    // Считаем размеры по ПОЛНОМУ тексту, чтобы окно не меняло размер во время печати
    TextMetrics {
        id: fullMetrics
        font.family: "Minecraft Default"
        font.pixelSize: 16
        text: root.fullText
    }

    width: Math.min(maxWidth, fullMetrics.width + 24)
    height: fullMetrics.height + 20 + 14

    Rectangle {
        id: bubble
        anchors.fill: parent
        anchors.bottomMargin: 14
        color: "#f5f5f5"
        border.color: "#888"
        border.width: 2
        radius: 10
        antialiasing: false

        Text {
            id: bubbleText
            anchors.fill: parent
            anchors.margins: 10
            text: root.displayText
            color: "#222"
            font.family: "Minecraft Default"
            font.pixelSize: 16
            renderType: Text.NativeRendering
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        Canvas {
            id: tailCanvas
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.bottom
            width: 16
            height: 18
            y: -3

            onPaint: {
                var ctx = getContext("2d");
                ctx.reset();

                ctx.beginPath();
                ctx.moveTo(0, 0);
                ctx.lineTo(16, 0);
                ctx.lineTo(8, 14);
                ctx.closePath();
                ctx.fillStyle = "#f5f5f5";
                ctx.fill();

                ctx.beginPath();
                ctx.rect(2, 0, 12, 3);
                ctx.fillStyle = "#f5f5f5";
                ctx.fill();

                ctx.beginPath();
                ctx.moveTo(0, -1);
                ctx.lineTo(8, 14);
                ctx.lineTo(16, -1);
                ctx.lineWidth = 2;
                ctx.strokeStyle = "#888";
                ctx.stroke();
            }
        }
    }

    Timer {
        id: typewriterTimer
        interval: root.charDelay
        repeat: true
        onTriggered: {
            if (root.visibleChars < root.fullText.length) {
                root.visibleChars++
            } else {
                typewriterTimer.stop()
            }
        }
    }

    Timer {
        id: hideTimer
        interval: root.hideDelay
        onTriggered: root.hideBubble()
    }

    function showBubble(globalX, globalY, text) {
        root.anchorX = globalX
        root.anchorY = globalY

        fullText = text
        visibleChars = 0

        // Центрируем сразу по финальному размеру
        updatePosition()

        root.visible = true
        typewriterTimer.start()
        hideTimer.restart()
    }

    function updatePosition() {
        var w = root.width
        var h = root.height

        var targetX = anchorX - (w / 2)
        var targetY = anchorY - h + 14

        var maxX = Screen.desktopAvailableWidth - w
        var maxY = Screen.desktopAvailableHeight - h

        root.x = Math.min(Math.max(0, targetX), maxX)
        root.y = Math.min(Math.max(0, targetY), maxY)
    }

    function hideBubble() {
        root.visible = false
        typewriterTimer.stop()
        hideTimer.stop()
    }
}