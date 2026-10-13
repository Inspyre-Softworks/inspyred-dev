import QtQuick
import QtQuick.Controls

ComboBox {
    id: root

    property string helpId: ''
    property string helpText: ''
    property string tooltip: ''
    property real popupMaximumHeight: 280

    readonly property string resolvedHelp: helpText.length > 0
        ? helpText
        : (helpId.length > 0 ? HelpRegistry.textFor(helpId) : '')
    readonly property string effectiveTooltip: tooltip.length > 0 ? tooltip : resolvedHelp

    hoverEnabled: true
    implicitHeight: 44
    leftPadding: 14
    rightPadding: 34
    font.pixelSize: 14
    font.family: Qt.platform.os === 'windows' ? 'Segoe UI Variable' : 'sans-serif'

    Accessible.name: currentText
    Accessible.description: resolvedHelp

    contentItem: Text {
        leftPadding: 0
        rightPadding: 0
        text: root.displayText
        font: root.font
        color: Theme.textPrimary
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    indicator: Text {
        x: root.width - width - 12
        anchors.verticalCenter: parent.verticalCenter
        text: '⌄'
        color: Theme.textSecondary
        font.pixelSize: 18
    }

    background: Item {
        GlowFrame {
            anchors.fill: parent
            radius: 11
            glowColor: root.activeFocus ? Theme.cyan : Theme.glow
            strength: root.activeFocus || root.hovered ? 1.0 : 0.72
        }

        Rectangle {
            anchors.fill: parent
            radius: 11
            color: root.hovered ? Theme.surfaceAlt : Theme.surface
            border.width: root.activeFocus ? 2 : 1
            border.color: root.activeFocus ? Theme.cyan : Theme.border
        }
    }

    delegate: ItemDelegate {
        width: root.width
        text: modelData
        font: root.font
        highlighted: root.highlightedIndex === index

        contentItem: Text {
            text: parent.text
            color: Theme.textPrimary
            font: parent.font
            verticalAlignment: Text.AlignVCenter
            leftPadding: 8
        }

        background: Rectangle {
            color: parent.highlighted ? Theme.surfaceAlt : Theme.surface
            radius: 6
        }
    }

    popup: Popup {
        y: root.height + 6
        width: root.width
        implicitHeight: contentItem.implicitHeight + 12
        padding: 6
        onOpened: {
            if (root.currentIndex >= 0)
                contentItem.positionViewAtIndex(root.currentIndex, ListView.Contain)
        }

        contentItem: ListView {
            clip: true
            implicitHeight: Math.min(contentHeight, root.popupMaximumHeight)
            model: root.popup.visible ? root.delegateModel : null
            currentIndex: root.highlightedIndex

            ScrollBar.vertical: ScrollBar {
                policy: parent.contentHeight > parent.height
                    ? ScrollBar.AlwaysOn
                    : ScrollBar.AsNeeded
            }
        }

        background: Rectangle {
            color: Theme.surface
            border.color: Theme.border
            border.width: 1
            radius: 10
        }
    }

    ToolTip.visible: effectiveTooltip.length > 0 && (root.hovered || root.activeFocus)
    ToolTip.delay: 650
    ToolTip.timeout: 7000
    ToolTip.text: effectiveTooltip
}
