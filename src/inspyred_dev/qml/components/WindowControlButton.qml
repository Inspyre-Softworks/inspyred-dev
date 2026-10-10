import QtQuick
import QtQuick.Controls

Button {
    id: root

    property string iconName: ''
    property string tooltip: ''
    property bool closeButton: false

    implicitWidth: 46
    implicitHeight: 40
    padding: 0
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus

    Accessible.name: tooltip

    contentItem: Item {
        InspyredIcon {
            anchors.centerIn: parent
            width: 16
            height: 16
            name: root.iconName
            color: root.closeButton && (root.hovered || root.down)
                ? '#FFFFFF'
                : Theme.textPrimary
            strokeWidth: 1.65
        }
    }

    background: Rectangle {
        color: {
            if (root.closeButton && (root.hovered || root.down))
                return Theme.danger
            if (root.down)
                return Qt.darker(Theme.surfaceAlt, 1.08)
            return root.hovered || root.activeFocus ? Theme.surfaceAlt : 'transparent'
        }

        Behavior on color {
            ColorAnimation { duration: 80 }
        }
    }

    ToolTip.visible: tooltip.length > 0 && (hovered || activeFocus)
    ToolTip.delay: hovered ? 500 : 0
    ToolTip.text: tooltip
}
