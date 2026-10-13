import QtQuick
import QtQuick.Controls

TextField {
    id: root

    property string helpId: ''
    property string helpText: ''
    property string tooltip: ''

    readonly property string resolvedHelp: helpText.length > 0
        ? helpText
        : (helpId.length > 0 ? HelpRegistry.textFor(helpId) : '')
    readonly property string effectiveTooltip: tooltip.length > 0 ? tooltip : resolvedHelp

    color: Theme.textPrimary
    placeholderTextColor: Theme.textSecondary
    selectionColor: Theme.accent
    selectedTextColor: '#FFFFFF'
    font.pixelSize: 14
    font.family: Qt.platform.os === 'windows' ? 'Segoe UI Variable' : 'sans-serif'
    leftPadding: 14
    rightPadding: 14
    implicitHeight: 44
    hoverEnabled: true

    Accessible.name: placeholderText
    Accessible.description: resolvedHelp

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
            color: root.activeFocus ? Theme.surfaceRaised : Theme.surface
            border.width: root.activeFocus ? 2 : 1
            border.color: root.activeFocus ? Theme.cyan : Theme.border

            Behavior on border.color {
                ColorAnimation { duration: 100 }
            }
        }
    }

    ToolTip.visible: effectiveTooltip.length > 0 && (root.hovered || root.activeFocus)
    ToolTip.delay: 650
    ToolTip.timeout: 7000
    ToolTip.text: effectiveTooltip
}
