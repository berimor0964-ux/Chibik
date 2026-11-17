import QtQuick
import QtQuick.Window

Window {
    id: root
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput | Qt.NoDropShadowWindowHint
    color: "transparent"
    visible: false

    property string fullText: ""
    property int visibleChars: 0
    property int maxWidth: 260
    property int charDelay: 40
    property int hideDelay: 5000
    property real anchorX: 0
    property real anchorY: 0

    readonly property string displayText: fullText.substring(0, visibleChars)

    TextMetrics {
        id: fullMetrics
        font.family: "Segoe UI"
        font.pixelSize: 16
        text: root.fullText
    }

    width: Math.min(maxWidth, fullMetrics.width + 44)
    height: fullMetrics.height + 40

    // Мягкая тень
    Rectangle {
        anchors.fill: bubble
        anchors.topMargin: 4
        anchors.leftMargin: 4
        z: -1
        color: "#20d87093"
        radius: bubble.radius
    }

    Rectangle {
        id: bubble
        anchors.fill: parent
        anchors.bottomMargin: 22
        color: "#fff0f5"
        border.color: "#ffb6c1"
        border.width: 3
        radius: 22

        // Блик в углу
        Rectangle {
            x: 8; y: 8; width: 20; height: 8
            color: "#ffffff"
            radius: 4
            opacity: 0.6
        }

        Text {
            anchors.fill: parent
            anchors.margins: 16
            text: root.displayText
            color: "#d87093"
            font.family: "Segoe UI"
            font.pixelSize: 16
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        // Хвостик из двух кружков (облачный)
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.bottom
            anchors.topMargin: -4
            width: 16; height: 16
            color: "#fff0f5"
            radius: 8
            border.color: "#ffb6c1"
            border.width: 3
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.bottom
            anchors.topMargin: 8
            width: 10; height: 10
            color: "#fff0f5"
            radius: 5
            border.color: "#ffb6c1"
            border.width: 3
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
        var targetY = anchorY - h + 22
        root.x = Math.min(Math.max(0, targetX), Screen.desktopAvailableWidth - w)
        root.y = Math.min(Math.max(0, targetY), Screen.desktopAvailableHeight - h)
    }

    function hideBubble() {
        root.visible = false
        typewriterTimer.stop()
        hideTimer.stop()
    }
}