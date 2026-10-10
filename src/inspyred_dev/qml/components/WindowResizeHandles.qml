import QtQuick
import QtQuick.Window

Item {
    id: root

    required property Window targetWindow

    readonly property bool maximized: targetWindow.visibility === Window.Maximized

    MouseArea {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 5
        cursorShape: Qt.SizeHorCursor
        enabled: !root.maximized
        acceptedButtons: Qt.LeftButton
        onPressed: root.targetWindow.startSystemResize(Qt.LeftEdge)
    }

    MouseArea {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 5
        cursorShape: Qt.SizeHorCursor
        enabled: !root.maximized
        acceptedButtons: Qt.LeftButton
        onPressed: root.targetWindow.startSystemResize(Qt.RightEdge)
    }

    MouseArea {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 5
        cursorShape: Qt.SizeVerCursor
        enabled: !root.maximized
        acceptedButtons: Qt.LeftButton
        onPressed: root.targetWindow.startSystemResize(Qt.BottomEdge)
    }

    MouseArea {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        width: 7
        height: 7
        cursorShape: Qt.SizeBDiagCursor
        enabled: !root.maximized
        acceptedButtons: Qt.LeftButton
        onPressed: root.targetWindow.startSystemResize(Qt.BottomEdge | Qt.LeftEdge)
    }

    MouseArea {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: 7
        height: 7
        cursorShape: Qt.SizeFDiagCursor
        enabled: !root.maximized
        acceptedButtons: Qt.LeftButton
        onPressed: root.targetWindow.startSystemResize(Qt.BottomEdge | Qt.RightEdge)
    }
}
