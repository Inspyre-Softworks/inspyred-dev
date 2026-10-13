import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: root

    property string iconName: ''
    property string helpId: ''
    property string helpText: ''
    property string tooltip: ''
    property string shortcutSequence: ''
    property bool forceLabel: false
    property bool accent: false
    property bool destructive: false
    property bool compact: false
    property bool selected: false
    property bool iconOnly: false
    property bool suppressLabel: false
    property bool bounceOnHover: false
    property color hoverGlowColor: Theme.borderStrong

    // The global display preference wins over a button's compact/icon-only hint.
    // suppressLabel is reserved for layouts that physically cannot fit a label.
    readonly property bool showLabel: !suppressLabel
        && text.length > 0
        && (forceLabel || AppSettings.labelsEnabled)
    readonly property string resolvedHelp: helpText.length > 0
        ? helpText
        : (helpId.length > 0 ? HelpRegistry.textFor(helpId) : '')
    readonly property string effectiveTooltip: {
        let base = tooltip.length > 0 ? tooltip : resolvedHelp
        if (shortcutSequence.length > 0)
            return base.length > 0 ? base + '  ·  ' + shortcutSequence : shortcutSequence
        return base
    }

    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    opacity: root.enabled ? 1.0 : 0.65
    scale: root.bounceOnHover && root.hovered ? 1.035 : 1.0
    z: root.bounceOnHover && root.hovered ? 2 : 0
    transformOrigin: Item.Center
    implicitHeight: compact ? 36 : 44
    implicitWidth: contentItem.implicitWidth + (compact ? 22 : 28)
    leftPadding: compact ? 11 : 14
    rightPadding: compact ? 11 : 14

    Accessible.name: text
    Accessible.description: resolvedHelp

    contentItem: RowLayout {
        spacing: 8

        InspyredIcon {
            visible: root.iconName.length > 0
            name: root.iconName
            color: root.enabled
                ? (root.accent ? '#FFFFFF' : Theme.textPrimary)
                : Theme.textSecondary
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
            Layout.alignment: Qt.AlignVCenter
        }

        Text {
            visible: root.showLabel && root.text.length > 0
            text: root.text
            color: root.enabled
                ? (root.accent ? '#FFFFFF' : Theme.textPrimary)
                : Theme.textSecondary
            font.pixelSize: 14
            font.weight: Font.DemiBold
            font.family: Qt.platform.os === 'windows' ? 'Segoe UI Variable' : 'sans-serif'
            elide: Text.ElideRight
            Layout.alignment: Qt.AlignVCenter
        }
    }

    background: Item {
        GlowFrame {
            anchors.fill: parent
            radius: 11
            glowColor: root.activeFocus
                ? Theme.cyan
                : (root.hovered
                    ? root.hoverGlowColor
                    : (root.accent || root.selected ? Theme.borderStrong : Theme.glow))
            strength: root.activeFocus || root.hovered || root.accent || root.selected ? 1.0 : 0.72
        }

        Rectangle {
            anchors.fill: parent
            radius: 11
            border.width: root.activeFocus ? 2 : 1
            border.color: root.activeFocus
                ? Theme.cyan
                : (root.hovered
                    ? root.hoverGlowColor
                    : (root.accent || root.selected ? Theme.borderStrong : Theme.border))

            property color fillColor: root.destructive
                ? Theme.danger
                : (root.accent
                    ? (root.hovered ? Theme.accentHover : Theme.accent)
                    : (root.selected
                        ? (root.hovered ? Theme.accentHover : Theme.surfaceAlt)
                        : (root.hovered ? Theme.surfaceAlt : 'transparent')))

            color: root.down
                ? Qt.darker(fillColor, 1.08)
                : fillColor

            Behavior on color {
                ColorAnimation { duration: 100 }
            }

        }
    }

    Behavior on opacity {
        NumberAnimation { duration: 100 }
    }

    Behavior on scale {
        NumberAnimation {
            duration: root.hovered ? 240 : 120
            easing.type: root.hovered ? Easing.OutBack : Easing.OutCubic
            easing.overshoot: 1.8
        }
    }

    ToolTip.visible: effectiveTooltip.length > 0 && (root.hovered || root.activeFocus)
    ToolTip.delay: 500
    ToolTip.timeout: 7000
    ToolTip.text: effectiveTooltip

    Shortcut {
        enabled: root.enabled && root.shortcutSequence.length > 0
        sequence: root.shortcutSequence
        onActivated: root.clicked()
    }
}
