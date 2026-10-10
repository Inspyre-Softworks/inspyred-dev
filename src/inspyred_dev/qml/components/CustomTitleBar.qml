import QtQuick
import QtQuick.Window

Rectangle {
    id: root

    required property Window targetWindow

    readonly property bool maximized: targetWindow.visibility === Window.Maximized

    implicitHeight: 48
    color: Theme.background

    function toggleMaximized() {
        if (maximized)
            targetWindow.showNormal()
        else
            targetWindow.showMaximized()
    }

    MouseArea {
        id: moveArea
        anchors.fill: parent
        anchors.topMargin: 5
        anchors.rightMargin: windowControls.width
        acceptedButtons: Qt.LeftButton

        onPressed: root.targetWindow.startSystemMove()
        onDoubleClicked: root.toggleMaximized()
    }

    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        spacing: 10

        AppIcon {
            width: 28
            height: 28
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: root.targetWindow.title
            color: Theme.textPrimary
            font.pixelSize: 14
            font.weight: Font.DemiBold
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    Row {
        id: windowControls
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.bottom: parent.bottom

        WindowControlButton {
            height: parent.height
            iconName: 'minimize'
            tooltip: 'Minimize'
            onClicked: root.targetWindow.showMinimized()
        }

        WindowControlButton {
            height: parent.height
            iconName: root.maximized ? 'restore' : 'maximize'
            tooltip: root.maximized ? 'Restore' : 'Maximize'
            onClicked: root.toggleMaximized()
        }

        WindowControlButton {
            height: parent.height
            iconName: 'close'
            tooltip: 'Close'
            closeButton: true
            onClicked: root.targetWindow.close()
        }
    }

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 1
        color: Theme.borderStrong
        opacity: 0.75
    }

    MouseArea {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 5
        cursorShape: root.maximized ? Qt.ArrowCursor : Qt.SizeVerCursor
        enabled: !root.maximized
        acceptedButtons: Qt.LeftButton
        onPressed: root.targetWindow.startSystemResize(Qt.TopEdge)
    }

    MouseArea {
        anchors.left: parent.left
        anchors.top: parent.top
        width: 7
        height: 7
        cursorShape: Qt.SizeFDiagCursor
        enabled: !root.maximized
        acceptedButtons: Qt.LeftButton
        onPressed: root.targetWindow.startSystemResize(Qt.TopEdge | Qt.LeftEdge)
    }

    MouseArea {
        anchors.right: parent.right
        anchors.top: parent.top
        width: 7
        height: 7
        cursorShape: Qt.SizeBDiagCursor
        enabled: !root.maximized
        acceptedButtons: Qt.LeftButton
        onPressed: root.targetWindow.startSystemResize(Qt.TopEdge | Qt.RightEdge)
    }
}
