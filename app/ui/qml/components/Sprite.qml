import QtQuick

Item {
    id: root

    property string sheet: ""
    property int frameCount: 1
    property int frameWidth: 64
    property int frameHeight: 64
    property int frameDuration: 200
    property bool running: true
    property bool mirror: false

    width: frameWidth
    height: frameHeight
    clip: true

    property int currentFrame: 0

    Image {
        id: sheetImage
        source: root.sheet
        x: -root.currentFrame * root.frameWidth
        y: 0
        width: root.frameWidth * root.frameCount
        height: root.frameHeight
        smooth: true
    }

    transform: Scale {
        origin.x: root.width / 2
        xScale: root.mirror ? -1 : 1
    }

    Timer {
        interval: root.frameDuration
        running: root.running && root.frameCount > 1
        repeat: true
        onTriggered: {
            root.currentFrame = (root.currentFrame + 1) % root.frameCount
        }
    }
}