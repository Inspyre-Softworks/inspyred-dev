import QtQuick

Item {
    id: root

    property real radius: 0
    property color glowColor: Theme.glow
    property real strength: 1.0
    readonly property color renderedGlowColor: Qt.rgba(
        glowColor.r,
        glowColor.g,
        glowColor.b,
        1.0
    )

    // Layered translucent outlines keep this lightweight while giving borders
    // a soft neon falloff on platforms where shader effects are unavailable.
    Rectangle {
        anchors.fill: parent
        anchors.margins: -3
        radius: root.radius + 3
        color: 'transparent'
        border.width: 2
        border.color: root.renderedGlowColor
        opacity: 0.24 * root.strength
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: -1
        radius: root.radius + 1
        color: 'transparent'
        border.width: 2
        border.color: root.renderedGlowColor
        opacity: 0.46 * root.strength
    }
}
