import QtQuick

Item {
    id: root

    property bool vertical: false
    property color lineColor: Theme.borderStrong
    property real strength: 1.0

    implicitWidth: vertical ? 1 : 48
    implicitHeight: vertical ? 48 : 1

    Rectangle {
        anchors.centerIn: parent
        width: root.vertical ? 5 : parent.width
        height: root.vertical ? parent.height : 5
        color: root.lineColor
        opacity: 0.20 * root.strength
    }

    Rectangle {
        anchors.centerIn: parent
        width: root.vertical ? 3 : parent.width
        height: root.vertical ? parent.height : 3
        color: root.lineColor
        opacity: 0.36 * root.strength
    }

    Rectangle {
        anchors.centerIn: parent
        width: root.vertical ? 1 : parent.width
        height: root.vertical ? parent.height : 1
        color: root.lineColor
        opacity: 0.96 * root.strength
    }
}
