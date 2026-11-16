import QtQuick
import QtQuick.Window

Window {
    id: root
    flags: Qt.Window | Qt.FramelessWindowHint
         | Qt.WindowStaysOnTopHint | Qt.Tool
         | Qt.WindowTransparentForInput
         | Qt.NoDropShadowWindowHint
    color: "transparent"
    visible: false

    property string fullText: ""
    property int visibleChars: 0
    property int maxWidth: 240
    property int charDelay: 40
    property int hideDelay: 5000
    property real anchorX: 0
    property real anchorY: 0

    readonly property string displayText: fullText.substring(0, visibleChars)

    TextMetrics {
        id: fullMetrics
        font.family: "Minecraft Default"
        font.pixelSize: 16
        text: root.fullText
    }

    width: Math.min(maxWidth, fullMetrics.width + 32)
    height: fullMetrics.height + 32

    Rectangle {
        id: bubble
        anchors.fill: parent
        anchors.bottomMargin: 16
        color: "#f4e4c1"
        border.color: "#2d1b0e"
        border.width: 3

        Text {
            anchors.fill: parent
            anchors.margins: 12
            text: root.displayText
            color: "#2d1b0e"
            font.family: "Minecraft Default"
            font.pixelSize: 16
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        Canvas {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.bottom
            width: 20; height: 16
            y: -3
            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.beginPath()
                ctx.moveTo(0, 0)
                ctx.lineTo(20, 0)
                ctx.lineTo(10, 14)
                ctx.closePath()
                ctx.fillStyle = "#f4e4c1"
                ctx.fill()
                ctx.lineWidth = 3
                ctx.strokeStyle = "#2d1b0e"
                ctx.stroke()
            }
        }
    }

    Timer {
        id: typewriterTimer
        interval: root.charDelay
        repeat: true
        onTriggered: {
            if (root.visibleChars < root.fullText.length)
                root.visibleChars++
            else
                typewriterTimer.stop()
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
        updatePosition()
        root.visible = true
        typewriterTimer.start()
        hideTimer.restart()
    }

    function updateAnchor(globalX, globalY) {
        root.anchorX = globalX
        root.anchorY = globalY
        if (root.visible) updatePosition()
    }

    function updatePosition() {
        var w = root.width, h = root.height
        var targetX = anchorX - (w / 2)
        var targetY = anchorY - h + 16
        root.x = Math.min(Math.max(0, targetX),
                          Screen.desktopAvailableWidth - w)
        root.y = Math.min(Math.max(0, targetY),
                          Screen.desktopAvailableHeight - h)
    }

    function hideBubble() {
        root.visible = false
        typewriterTimer.stop()
        hideTimer.stop()
    }
}